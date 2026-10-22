import json
import os
from pathlib import Path
import subprocess
import sys
import time
import wave

import pytest

from openclaw_stt.core import Config, STTError, parse_result, transcribe
from openclaw_stt.evaluation import add_note, benchmark, normalize, score, write_private_json


@pytest.fixture
def audio(tmp_path):
    path = tmp_path / "voice with spaces; $(touch SHOULD_NOT_EXIST).wav"
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(48000)
        output.writeframes(bytes(48000 * 2 * 2))
    return path


@pytest.fixture
def config(tmp_path):
    worker = tmp_path / "engine.py"
    worker.write_text('''
import json, os, pathlib, sys, time, wave
mode, audio, language, keywords = sys.argv[1:]
if mode == "timeout":
    time.sleep(10)
if mode == "bad":
    print("Downloading model... not JSON")
    sys.exit(0)
if mode == "error":
    print("model unavailable", file=sys.stderr)
    sys.exit(7)
with wave.open(audio) as wav:
    assert (wav.getnchannels(), wav.getframerate(), wav.getsampwidth()) == (1, 16000, 2)
assert os.environ["NEEDLE_TELEMETRY"] == "0"
assert os.environ["DO_NOT_TRACK"] == "1"
assert os.environ["HF_HUB_OFFLINE"] == "1"
text = "" if mode == "silence" else "Hola Giân"
print(json.dumps({"text": text, "language": language or "es", "words": []}))
pathlib.Path(__file__).with_suffix(".observed").write_text(json.dumps({"audio":audio,"keywords":pathlib.Path(keywords).read_text()}))
''')
    path = tmp_path / "config.toml"
    lines = ['default_backend = "good"', 'max_duration_seconds = 5']
    for name in ("good", "silence", "bad", "error", "timeout"):
        lines.extend([f"[backends.{name}]", 'type = "command"',
                      "argv = " + json.dumps([sys.executable, str(worker), name, "{audio}", "{language}", "{keywords_file}"])])
    path.write_text("\n".join(lines))
    return Config(path)


def test_ogg_opus_hints_cleanup_and_safe_argv(audio, config, tmp_path):
    ogg = tmp_path / "telegram voice.ogg"
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-c:a", "libopus", str(ogg)], check=True)
    result = transcribe(ogg, config, language="es", keywords=["Giân", "OpenClaw", "Giân"])
    assert result["text"] == "Hola Giân"
    assert result["language_hint"] == "es"
    assert result["audio_duration_seconds"] == pytest.approx(1, abs=.01)
    assert len(result["normalized_audio_sha256"]) == 64
    observed = json.loads((tmp_path / "engine.observed").read_text())
    assert observed["keywords"] == "Giân\nOpenClaw"
    assert not Path(observed["audio"]).exists()
    assert not Path("SHOULD_NOT_EXIST").exists()


def test_silence_is_success_not_error(audio, config):
    assert transcribe(audio, config, backend="silence")["text"] == ""


@pytest.mark.parametrize("backend,message", [("bad", "JSON"), ("error", "model unavailable"), ("missing", "Unknown backend")])
def test_backend_failures_are_explicit(audio, config, backend, message):
    with pytest.raises(STTError, match=message):
        transcribe(audio, config, backend=backend)


def test_timeout_terminates_process(audio, config):
    start = time.monotonic()
    with pytest.raises(STTError, match="deadline"):
        transcribe(audio, config, backend="timeout", timeout=.5)
    assert time.monotonic() - start < 3


def test_duration_limit_never_silently_truncates(audio, config):
    config.data["max_duration_seconds"] = .1
    with pytest.raises(STTError, match="truncated"):
        transcribe(audio, config)


def test_corrupt_audio(config, tmp_path):
    source = tmp_path / "broken.ogg"
    source.write_bytes(b"not an audio file")
    with pytest.raises(STTError, match="ffmpeg exited"):
        transcribe(source, config)


@pytest.mark.parametrize("payload", ["[]", '{}', '{"text":null}', '{"text":"ok","words":[{"word":"x","probability":2}]}', '{"text":"ok","words":[{"word":"x","start":2,"end":1}]}'])
def test_invalid_engine_output_rejected(payload):
    with pytest.raises(STTError):
        parse_result(payload)


def test_cli_stdout_is_transcript_only_and_empty_hint_autodetects(audio, config):
    command = [sys.executable, "-m", "openclaw_stt.cli", "--config", str(config.path),
               "transcribe", str(audio), "--language", ""]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout == "Hola Giân\n"
    assert result.stderr == ""
    silence = subprocess.run(command + ["--backend", "silence"], capture_output=True, text=True)
    assert silence.returncode == 0 and silence.stdout == ""
    error = subprocess.run(command + ["--backend", "bad"], capture_output=True, text=True)
    assert error.returncode == 1 and error.stdout == "" and "JSON" in error.stderr


def test_unicode_and_keyword_scoring():
    assert normalize("¡NIÑO, café! Giân") == "niño café giân"
    result = score("¡Hola, Giân!", "Hola Gian", ["Giân", "Hola", "not in reference"])
    assert result["word_errors"] == 1 and result["reference_words"] == 2
    assert result["character_errors"] == 1
    assert result["keyword_hits"] == 1 and result["keyword_total"] == 2
    assert score("", "hallucination")["silence_false_positive"]
    assert not score("", "")["silence_false_positive"]
    assert score("one two", "one three two")["word_errors"] == 1
    assert score("one two", "one")["word_errors"] == 1


def test_benchmark_switches_backends_keeps_errors_and_checks_hashes(audio, config, tmp_path):
    manifest = tmp_path / "corpus/manifest.jsonl"
    add_note(manifest, audio, "spanish", "Hola Giân", "es", ["Giân"], ["outdoor", "es"])
    report = benchmark(manifest, config, ["good", "error"], repeat=2)
    assert report["summary"]["good"]["wer"] == 0
    assert report["summary"]["good"]["keyword_recall"] == 1
    assert report["summary"]["error"]["failed"] == 2
    assert report["summary"]["error"]["wer"] is None
    assert report["by_tag"]["good"]["outdoor"]["succeeded"] == 2
    hashes = {row["result"]["normalized_audio_sha256"] for row in report["records"] if row["status"] == "ok"}
    assert len(hashes) == 1
    stored = tmp_path / "report.json"
    write_private_json(stored, report)
    assert stored.stat().st_mode & 0o777 == 0o600
    retained = manifest.parent / json.loads(manifest.read_text())["audio"]
    retained.write_bytes(b"changed")
    failed = benchmark(manifest, config, ["good"])
    assert "checksum mismatch" in failed["records"][0]["error"]


def test_import_never_overwrites_or_accepts_path_traversal(audio, tmp_path):
    manifest = tmp_path / "corpus/manifest.jsonl"
    with pytest.raises(STTError, match="id must"):
        add_note(manifest, audio, "../escape", "")
    row = add_note(manifest, audio, "one", "")
    assert (manifest.parent / row["audio"]).stat().st_mode & 0o777 == 0o600
    with pytest.raises(STTError, match="Duplicate"):
        add_note(manifest, audio, "one", "")


def test_conversion_failure_is_counted_for_every_backend(config, tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({"id": "missing", "audio": "missing.wav", "reference": "hola"}) + "\n")
    report = benchmark(manifest, config, ["good", "silence"], repeat=2)
    assert all(s["failed"] == 2 for s in report["summary"].values())
    assert len(report["records"]) == 4

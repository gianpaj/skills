from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
import wave
from contextlib import contextmanager
from dataclasses import dataclass


class STTError(Exception):
    """An actionable conversion, configuration, or inference failure."""


def runtime_env():
    return {
        **os.environ,
        "NEEDLE_TELEMETRY": "0",
        "DO_NOT_TRACK": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "HF_HUB_OFFLINE": "1",
        "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
    }


def run(argv, deadline, *, env=None):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise STTError("Transcription deadline exceeded")
    try:
        with subprocess.Popen(
            [str(arg) for arg in argv], stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
            env=env or runtime_env(), start_new_session=True,
        ) as process:
            try:
                stdout, stderr = process.communicate(timeout=remaining)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.communicate()
                raise STTError("Transcription deadline exceeded or interrupted") from None
            if process.returncode:
                # stderr may include input paths; callers must keep benchmark reports private.
                raise STTError(f"{Path(str(argv[0])).name} exited {process.returncode}: {stderr.strip()[-1600:]}")
            return stdout
    except OSError as exc:
        raise STTError(f"Cannot run {argv[0]}: {exc}") from exc


def file_sha256(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


class Config:
    def __init__(self, path):
        self.path = Path(path).expanduser().resolve()
        try:
            self.data = tomllib.loads(self.path.read_text())
        except (OSError, ValueError) as exc:
            raise STTError(f"Cannot read config {self.path}: {exc}") from exc
        self.backends = self.data.get("backends", {})
        self.default = self.data.get("default_backend", "whistle")
        if not self.backends or self.default not in self.backends:
            raise STTError("Config requires backends and a valid default_backend")

    def path_value(self, value):
        path = Path(value).expanduser()
        return str(path if path.is_absolute() else self.path.parent / path)

    def executable(self, value):
        return self.path_value(value) if "/" in value else value

    def backend(self, name):
        try:
            return self.backends[name]
        except KeyError:
            raise STTError(f"Unknown backend {name!r}; choose from {', '.join(self.backends)}") from None


@dataclass
class PreparedAudio:
    path: Path
    source_sha256: str
    pcm_sha256: str
    duration_seconds: float
    conversion_ms: float


@contextmanager
def prepare_audio(path, config, deadline):
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise STTError(f"Audio file not found: {source}")
    started = time.monotonic()
    limit = float(config.data.get("max_duration_seconds", 600))
    if not math.isfinite(limit) or limit <= 0:
        raise STTError("max_duration_seconds must be positive and finite")
    with tempfile.TemporaryDirectory(prefix="openclaw-stt-") as directory:
        target = Path(directory) / "audio.wav"
        run([
            config.executable(config.data.get("ffmpeg", "ffmpeg")),
            "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-protocol_whitelist", "file,pipe", "-i", source,
            "-t", str(limit + 0.01), "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", target,
        ], deadline)
        try:
            with wave.open(str(target), "rb") as audio:
                duration = audio.getnframes() / audio.getframerate()
                if duration <= 0 or duration > limit:
                    raise STTError(f"Audio must contain >0 and <= {limit:g} seconds; not transcribing truncated input")
        except (wave.Error, OSError) as exc:
            raise STTError(f"Cannot decode normalized audio: {exc}") from exc
        yield PreparedAudio(target, file_sha256(source), file_sha256(target), duration,
                            (time.monotonic() - started) * 1000)


def parse_result(stdout):
    try:
        payload = json.loads(stdout)
    except ValueError as exc:
        raise STTError("Backend stdout is not a single JSON object") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
        raise STTError("Backend JSON must contain a string 'text' (empty string is valid silence)")
    words = payload.get("words") or []
    if not isinstance(words, list):
        raise STTError("Backend 'words' must be a list")
    normalized = []
    for word in words:
        if not isinstance(word, dict) or not isinstance(word.get("word"), str):
            raise STTError("Each backend word must contain string 'word'")
        item = {"word": word["word"]}
        for key in ("start", "end", "probability"):
            value = word.get(key)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
                raise STTError(f"Invalid word {key}")
            item[key] = value
        if item["probability"] is not None and not 0 <= item["probability"] <= 1:
            raise STTError("Word probability is outside [0, 1]")
        if item["start"] is not None and item["end"] is not None and not 0 <= item["start"] <= item["end"]:
            raise STTError("Invalid word timestamp range")
        normalized.append(item)
    language = payload.get("language") or None
    if language is not None and not isinstance(language, str):
        raise STTError("Backend language must be a string or null")
    return payload, normalized, language


def infer(audio, config, backend, language, keywords, deadline):
    cfg = config.backend(backend)
    kind = cfg.get("type")
    started = time.monotonic()
    keywords = list(dict.fromkeys(k.strip() for k in keywords if k.strip()))
    with tempfile.TemporaryDirectory(prefix="openclaw-stt-hints-") as directory:
        keyword_file = Path(directory) / "keywords.txt"
        keyword_file.write_text("\n".join(keywords), encoding="utf-8")
        if kind == "needle":
            if language and language not in {"en", "de", "fr", "es", "it", "nl", "pl"}:
                raise STTError(f"Whistle does not support language {language!r}")
            model = config.path_value(cfg["model"])
            argv = [config.executable(cfg["executable"]), "--model", model,
                    "--audio", audio.path, "--audio-word-timestamps"]
            if language:
                argv.extend(["--audio-language", language])
            if keywords:
                argv.extend(["--audio-keywords", keyword_file])
            if cfg.get("threads"):
                argv.extend(["--threads", str(cfg["threads"])])
            if cfg.get("depth"):
                argv.extend(["--audio-depth", str(cfg["depth"])])
        elif kind == "faster-whisper":
            model = config.path_value(cfg["model"])
            argv = [config.executable(cfg.get("python", sys.executable)),
                    "-m", "openclaw_stt.faster_whisper_worker", "--audio", audio.path,
                    "--model", model, "--device", cfg.get("device", "cpu"),
                    "--compute-type", cfg.get("compute_type", "int8"),
                    "--beam-size", str(cfg.get("beam_size", 5)),
                    "--keywords-file", keyword_file]
            if language:
                argv.extend(["--language", language])
        elif kind == "command":
            model = cfg.get("model", backend)
            replacements = {
                "{audio}": str(audio.path), "{language}": language or "",
                "{keywords_file}": str(keyword_file), "{model}": model,
            }
            argv = list(cfg["argv"])
            if not argv:
                raise STTError("Command backend needs nonempty argv")
            argv[0] = config.executable(argv[0])
            for index, arg in enumerate(argv):
                for placeholder, value in replacements.items():
                    arg = arg.replace(placeholder, value)
                argv[index] = arg
        else:
            raise STTError(f"Unknown backend type: {kind!r}")
        stdout = run(argv, deadline)
    payload, words, detected = parse_result(stdout)
    model_hash = file_sha256(model) if kind == "needle" else cfg.get("model_sha256")
    executable_hash = file_sha256(argv[0]) if kind == "needle" else None
    backend_ms = (time.monotonic() - started) * 1000
    total_ms = audio.conversion_ms + backend_ms
    return {
        "schema_version": 1, "text": payload["text"].strip(),
        "language": detected, "language_hint": language or None, "keywords": keywords,
        "backend": backend, "engine": kind, "model": model,
        "engine_version": cfg.get("engine_version"),
        "model_sha256": model_hash, "executable_sha256": executable_hash,
        "confidence": None, "words": words,
        "audio_sha256": audio.source_sha256, "normalized_audio_sha256": audio.pcm_sha256,
        "audio_duration_seconds": audio.duration_seconds,
        "timings": {
            "conversion_ms": audio.conversion_ms, "backend_process_ms": backend_ms,
            "total_ms": total_ms, "real_time_factor": total_ms / 1000 / audio.duration_seconds,
            "ttft_ms": payload.get("ttft_ms"), "decode_tps": payload.get("decode_tps"),
            "mode": "cold-process",
        },
    }


def transcribe(path, config, backend=None, language=None, keywords=(), timeout=90):
    if not math.isfinite(timeout) or timeout <= 0:
        raise STTError("timeout must be positive and finite")
    backend = backend or config.default
    config.backend(backend)
    deadline = time.monotonic() + timeout
    with prepare_audio(path, config, deadline) as audio:
        return infer(audio, config, backend, language or None, keywords, deadline)

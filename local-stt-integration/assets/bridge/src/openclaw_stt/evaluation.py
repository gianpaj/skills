from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import time
import unicodedata

from .core import STTError, file_sha256, infer, prepare_audio


NORMALIZER = "unicode-nfkc-casefold-punctuation-space-v1"


def normalize(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    return " ".join("".join(c if c.isalnum() or c.isspace() else " " for c in text).split())


def distance(reference, hypothesis):
    row = list(range(len(hypothesis) + 1))
    for i, expected in enumerate(reference, 1):
        next_row = [i]
        for j, actual in enumerate(hypothesis, 1):
            next_row.append(min(next_row[-1] + 1, row[j] + 1, row[j - 1] + (expected != actual)))
        row = next_row
    return row[-1]


def score(reference, hypothesis, keywords=()):
    expected, actual = normalize(reference), normalize(hypothesis)
    ref_words, hyp_words = expected.split(), actual.split()
    ref_chars, hyp_chars = expected.replace(" ", ""), actual.replace(" ", "")
    eligible = {normalize(k) for k in keywords if normalize(k) and f" {normalize(k)} " in f" {expected} "}
    return {
        "word_errors": distance(ref_words, hyp_words), "reference_words": len(ref_words),
        "character_errors": distance(ref_chars, hyp_chars), "reference_characters": len(ref_chars),
        "keyword_hits": sum(f" {k} " in f" {actual} " for k in eligible),
        "keyword_total": len(eligible), "empty_reference": not expected,
        "silence_false_positive": not expected and bool(actual),
    }


def summarize(records):
    successful = [r for r in records if r["status"] == "ok"]
    totals = {key: sum(r["scores"][key] for r in successful) for key in (
        "word_errors", "reference_words", "character_errors", "reference_characters",
        "keyword_hits", "keyword_total", "empty_reference", "silence_false_positive",
    )}
    latencies = sorted(r["result"]["timings"]["total_ms"] for r in successful)
    duration = sum(r["result"]["audio_duration_seconds"] for r in successful)
    return {
        "attempted": len(records), "succeeded": len(successful), "failed": len(records) - len(successful),
        **totals,
        "wer": totals["word_errors"] / totals["reference_words"] if totals["reference_words"] else None,
        "cer": totals["character_errors"] / totals["reference_characters"] if totals["reference_characters"] else None,
        "keyword_recall": totals["keyword_hits"] / totals["keyword_total"] if totals["keyword_total"] else None,
        "latency_median_ms": statistics.median(latencies) if latencies else None,
        "latency_p95_ms": latencies[max(0, math.ceil(len(latencies) * 0.95) - 1)] if latencies else None,
        "real_time_factor": sum(latencies) / 1000 / duration if duration else None,
    }


def read_manifest(path):
    path = Path(path).resolve()
    rows, ids = [], set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise STTError(f"Cannot read manifest: {exc}") from exc
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("entry must be an object")
            for key in ("id", "audio", "reference"):
                if not isinstance(row.get(key), str):
                    raise ValueError(f"{key} must be a string")
            if not row["id"] or row["id"] in ids:
                raise ValueError("id must be nonempty and unique")
            for key in ("tags", "keywords"):
                if not isinstance(row.get(key, []), list) or any(not isinstance(x, str) for x in row.get(key, [])):
                    raise ValueError(f"{key} must be a list of strings")
            if row.get("language") is not None and not isinstance(row["language"], str):
                raise ValueError("language must be a string or null")
            ids.add(row["id"])
            rows.append(row)
        except (ValueError, TypeError) as exc:
            raise STTError(f"Invalid manifest line {number}: {exc}") from exc
    if not rows:
        raise STTError("Manifest is empty")
    return path, rows


def benchmark(manifest, config, backends, timeout=90, repeat=1):
    if repeat < 1 or not math.isfinite(timeout) or timeout <= 0:
        raise STTError("repeat and timeout must be positive")
    manifest, samples = read_manifest(manifest)
    backends = list(dict.fromkeys(backends or [config.default]))
    for name in backends:
        config.backend(name)
    records = []
    for sample in samples:
        # Convert once; all engines and repetitions receive the same bytes.
        source = manifest.parent / sample["audio"]
        try:
            if source.is_file() and sample.get("sha256") and sample["sha256"] != file_sha256(source):
                raise STTError(f"Audio checksum mismatch for {sample['id']}")
            with prepare_audio(source, config, time.monotonic() + timeout) as audio:
                if sample.get("sha256") and sample["sha256"] != audio.source_sha256:
                    raise STTError(f"Audio checksum mismatch for {sample['id']}")
                for iteration in range(repeat):
                    for name in backends:
                        base = {"id": sample["id"], "backend": name, "iteration": iteration,
                                "tags": sample.get("tags", []), "reference": sample["reference"]}
                        try:
                            result = infer(audio, config, name, sample.get("language"), sample.get("keywords", []),
                                           time.monotonic() + max(0, timeout - audio.conversion_ms / 1000))
                            records.append({**base, "status": "ok", "result": result,
                                            "scores": score(sample["reference"], result["text"], sample.get("keywords", []))})
                        except (STTError, KeyError, ValueError) as exc:
                            records.append({**base, "status": "error", "error": str(exc)})
        except STTError as exc:
            for iteration in range(repeat):
                for name in backends:
                    records.append({"id": sample["id"], "backend": name, "iteration": iteration,
                                    "tags": sample.get("tags", []), "reference": sample["reference"],
                                    "status": "error", "error": str(exc)})
    groups = defaultdict(list)
    for record in records:
        for tag in set(record["tags"]):
            groups[(record["backend"], tag)].append(record)
    return {
        "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "normalizer": NORMALIZER, "latency_mode": "cold-process; shared conversion included per attempt",
        "manifest_sha256": file_sha256(manifest), "config_sha256": file_sha256(config.path),
        "repeat": repeat, "notes": "WER/CER use successful attempts only; always inspect failure counts. Word probabilities are not comparable across engines.",
        "summary": {name: summarize([r for r in records if r["backend"] == name]) for name in backends},
        "by_tag": {name: {tag: summarize(group) for (engine, tag), group in groups.items() if engine == name} for name in backends},
        "records": records,
    }


def write_private_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        os.fchmod(output.fileno(), 0o600)
        json.dump(value, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write("\n")


def add_note(manifest, audio, identifier, reference, language=None, keywords=(), tags=()):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", identifier):
        raise STTError("id must use 1–100 letters, digits, underscores, dots or hyphens")
    manifest, source = Path(manifest).resolve(), Path(audio).resolve()
    if not source.is_file():
        raise STTError(f"Audio file not found: {source}")
    if manifest.exists():
        _, existing = read_manifest(manifest)
        if any(row["id"] == identifier for row in existing):
            raise STTError(f"Duplicate corpus id: {identifier}")
    target = manifest.parent / "audio" / f"{identifier}{source.suffix.lower()}"
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Exclusive create: never overwrite an existing recording.
    with source.open("rb") as incoming, target.open("xb") as outgoing:
        os.fchmod(outgoing.fileno(), 0o600)
        shutil.copyfileobj(incoming, outgoing)
    row = {"id": identifier, "audio": str(target.relative_to(manifest.parent)),
           "reference": reference, "language": language or None,
           "keywords": list(keywords), "tags": list(tags), "sha256": file_sha256(target)}
    fd = os.open(manifest, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as output:
        os.fchmod(output.fileno(), 0o600)
        output.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row

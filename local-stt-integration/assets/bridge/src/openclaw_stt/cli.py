from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from .core import Config, STTError, transcribe
from .evaluation import add_note, benchmark, write_private_json


def main():
    parser = argparse.ArgumentParser(description="Thin local STT adapter and evaluation harness")
    parser.add_argument("--config", default=os.environ.get("OPENCLAW_STT_CONFIG", "config.local.toml"))
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("transcribe", help="Transcribe a local file; text stdout is safe for OpenClaw")
    p.add_argument("audio")
    p.add_argument("--backend")
    p.add_argument("--language", default=None, help="Empty means autodetect; supports OpenClaw's empty placeholder")
    p.add_argument("--keyword", action="append", default=[])
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--timeout", type=float, default=90)
    p = sub.add_parser("benchmark", help="Score human-labeled JSONL audio on selected engines")
    p.add_argument("manifest")
    p.add_argument("--backend", action="append", default=[])
    p.add_argument("--repeat", type=int, default=1)
    p.add_argument("--timeout", type=float, default=90)
    p.add_argument("--output", required=True)
    p = sub.add_parser("add-note", help="Explicitly retain a labeled local recording in a corpus")
    p.add_argument("audio")
    p.add_argument("--manifest", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--reference", required=True, help="Human transcript; empty string labels silence")
    p.add_argument("--language")
    p.add_argument("--keyword", action="append", default=[])
    p.add_argument("--tag", action="append", default=[])
    p = sub.add_parser("openclaw-config", help="Print media config fragment (does not modify OpenClaw)")
    p.add_argument("--backend")
    args = parser.parse_args()
    try:
        if args.command == "add-note":
            row = add_note(args.manifest, args.audio, args.id, args.reference, args.language, args.keyword, args.tag)
            print(json.dumps(row, ensure_ascii=False))
            return 0
        config = Config(args.config)
        if args.command == "transcribe":
            result = transcribe(args.audio, config, args.backend, args.language, args.keyword, args.timeout)
            if args.format == "json":
                print(json.dumps(result, ensure_ascii=False, allow_nan=False))
            elif result["text"]:
                print(result["text"])
        elif args.command == "benchmark":
            report = benchmark(args.manifest, config, args.backend, args.timeout, args.repeat)
            write_private_json(args.output, report)
            print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
            return int(any(row["failed"] for row in report["summary"].values()))
        elif args.command == "openclaw-config":
            backend = args.backend or config.default
            config.backend(backend)
            print(json.dumps({"tools": {"media": {
                "models": [{"type": "cli", "command": str(Path(sys.executable).parent / "stt-bridge"),
                            "args": ["--config", str(config.path), "transcribe", "{{AttachmentPath}}",
                                     "--backend", backend, "--format", "text", "--language", "{{Language}}",
                                     "--timeout", "90"],
                            "capabilities": ["audio"], "timeoutSeconds": 95}],
                "audio": {"enabled": True},
            }}}, indent=2))
        return 0
    except (STTError, OSError, KeyError, ValueError, TypeError) as exc:
        print(f"stt-bridge: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

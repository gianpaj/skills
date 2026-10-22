#!/usr/bin/env python3
"""Copy the bundled bridge into a new project; optionally fetch local runtimes."""
import argparse
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--setup", action="store_true", help="Download dependencies/models and run bridge tests")
    parser.add_argument("--whisper", action="store_true", help="Include faster-whisper dependencies during setup (not its weights)")
    args = parser.parse_args()
    if args.whisper and not args.setup:
        parser.error("--whisper requires --setup")
    source = Path(__file__).resolve().parents[1] / "assets/bridge"
    destination = args.destination.expanduser().resolve()
    # Do not install inside the source, or overwrite user files at any destination.
    if destination.is_relative_to(source):
        parser.error("choose a destination outside the bundled bridge")
    if destination.exists():
        parser.error(f"destination already exists: {destination}")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(
        "__pycache__", ".pytest_cache", ".venv", ".runtime", "*.egg-info",
        "config.local.toml", "reports", "corpus",
    ))
    print(f"Bridge copied to {destination}", flush=True)
    if args.setup:
        command = ["bash", str(destination / "scripts/setup-needle.sh")]
        if args.whisper:
            command += ["--extra", "whisper"]
        subprocess.run(command, cwd=destination, check=True)
    print("Agent configuration is unchanged. Use stt-bridge openclaw-config to generate a fragment.")


if __name__ == "__main__":
    main()

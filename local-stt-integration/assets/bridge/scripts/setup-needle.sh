#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v ffmpeg >/dev/null || { echo 'Install ffmpeg first.' >&2; exit 1; }
command -v uv >/dev/null || { echo 'Install uv first: https://docs.astral.sh/uv/' >&2; exit 1; }
export NEEDLE_TELEMETRY=0 DO_NOT_TRACK=1 HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HUB_OFFLINE=0
uv sync --frozen --python 3.12 --extra whistle --extra test "$@"
case "$(uname -s)-$(uname -m)" in
  Linux-x86_64) platform=linux-x86_64 ;;
  Linux-aarch64|Linux-arm64) platform=linux-arm64 ;;
  Darwin-arm64) platform=macos-arm64 ;;
  *) echo 'Unsupported setup platform; fetch a native Needle build manually.' >&2; exit 1 ;;
esac
.venv/bin/needle download "$platform" --out .runtime
.venv/bin/needle download whistle --out .runtime
.venv/bin/python - "$platform" <<'PY'
import hashlib, importlib.metadata, json, pathlib, sys
from needle.agent import fetch
root = pathlib.Path.cwd()
platform = sys.argv[1]
artifacts = [root / '.runtime' / platform / 'needle', root / '.runtime/whistle.cact']
provenance = {'cactus_needle': importlib.metadata.version('cactus-needle'),
              'engine_version': fetch.engine_version(3),
              'sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts}}
(root / '.runtime/provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
config = root / 'config.local.toml'
if not config.exists():
    template = (root / 'examples/config.toml').read_text()
    config.write_text(template.replace('linux-x86_64', platform))
print('Runtime ready. Existing config.local.toml is preserved.')
PY
.venv/bin/pytest -q

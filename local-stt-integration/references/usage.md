# Bridge commands and engine configuration

Run commands below from the copied bridge project. Use absolute paths when
calling from another directory. Config paths resolve relative to the config file.

## Transcribe

```sh
.venv/bin/stt-bridge --config config.local.toml transcribe /path/to/note.ogg
.venv/bin/stt-bridge --config config.local.toml transcribe /path/to/note.ogg \
  --language es --keyword OpenClaw --keyword Giân --format json
```

Text mode emits only the transcript. JSON mode includes text, detected language,
words/timestamps/probabilities where available, audio hashes, engine metadata,
conversion time, backend-process time, total time, and real-time factor. Aggregate
confidence is null. The default deadline is 90 seconds; audio over 10 minutes is
rejected rather than silently truncated. Adjust `max_duration_seconds` in config
and both agent/wrapper timeouts deliberately for longer notes.

## Smoke test

```sh
.venv/bin/python scripts/make-smoke-corpus.py
.venv/bin/stt-bridge --config config.local.toml benchmark corpus/smoke/manifest.jsonl \
  --backend whistle --repeat 2 --output reports/smoke.json
```

The public JFK sample is downloaded from whisper.cpp and checked against a pinned
SHA-256. Opus and deterministic artificial-noise variants are derived from it;
silence is generated. These are not independent quality samples.

## Import real labeled notes

```sh
.venv/bin/stt-bridge add-note /path/to/note.ogg \
  --manifest corpus/real/manifest.jsonl --id walk-es-001 \
  --reference 'El texto exacto que dije' --language es \
  --tag outdoor --tag es --keyword OpenClaw
.venv/bin/stt-bridge --config config.local.toml benchmark corpus/real/manifest.jsonl \
  --backend whistle --output reports/real.json
```

`add-note` copies audio with private permissions and records its hash. IDs must
be unique. An empty reference labels silence. Omit `--language` for autodetection,
including code-switched clips. Use clean/noisy, EN/ES/mixed, mumbled, jargon and
non-speech tags to find weaknesses. Keep held-out clips while tuning keywords.

JSONL manifest entries require string `id`, relative `audio`, and human
`reference`. Optional fields: `language`, `keywords`, `tags`, and `sha256`.
Changed recordings fail hash checks. Benchmark failures are retained in reports
and cause a nonzero exit; a report is still written.

## Add faster-whisper large-v3-turbo

```sh
uv sync --frozen --extra whistle --extra whisper --extra test
HF_HUB_DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 .venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download('mobiuslabsgmbh/faster-whisper-large-v3-turbo',
    local_dir='.runtime/faster-whisper-large-v3-turbo',
    allow_patterns=['*.json', '*.bin', 'vocabulary.*', 'tokenizer.*'])
PY
```

Enable the commented `whisper-turbo` section in `config.local.toml`. CUDA uses
`device="cuda"`, `compute_type="float16"` and needs CUDA 12/cuDNN 9 libraries.
CPU can use `device="cpu"`, `compute_type="int8"`. The worker requires local
weights and does not download them during inference. PyAV <19 is pinned for
faster-whisper 1.2.1 compatibility with the `metadata_errors` argument. Its default
VAD-disabled decoding can hallucinate on silence; measure non-speech explicitly.

```sh
.venv/bin/stt-bridge --config config.local.toml benchmark corpus/real/manifest.jsonl \
  --backend whistle --backend whisper-turbo --output reports/comparison.json
```

Each sample is converted once and shared across backends/repetitions. WER/CER are
corpus-micro over successful attempts; inspect failure counts before comparing
accuracy. All-failed engines have null scores. The custom Unicode normalizer
preserves accents and numbers, casefolds, and replaces punctuation with spaces;
CER excludes spaces. It is not Whisper's published normalizer. Timing includes a
fresh process/model load plus the shared conversion; caches can still warm.

## Other local engines

Add a `type="command"` backend:

```toml
[backends.other]
type = "command"
argv = ["/absolute/path/to/engine", "--audio", "{audio}"]
```

Supported placeholders: `{audio}`, `{language}`, `{keywords_file}`, `{model}`.
Arguments remain separate, without a shell. An unset language stays an empty
argument; omit language flags if the engine rejects it. Backend stdout must be a
single JSON object with required string `text`, optional string/null `language`,
and optional `words` list of `{word,start,end,probability}`. Use `--backend other`
to test it without changing the default.

## OpenClaw activation and rollback

The generated fragment pins a backend using `--backend`. Changing
`default_backend` alone does not switch an existing OpenClaw entry: change that
argument or regenerate the fragment. Preserve non-audio models and ensure no
audio-capable cloud entry remains when local-only operation is required.

Save the prior media value privately. Restore it with the supported OpenClaw config
setter; if `tools.media` was absent, `openclaw config unset tools.media` removes
the new subtree. Do not store a full config backup with credentials in this skill.

For development: `uv sync --frozen --extra test`, then `.venv/bin/pytest -q`.
Include `--extra whistle`/`--extra whisper` when keeping those runtimes installed;
`uv sync` removes unselected optional dependencies.

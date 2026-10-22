---
name: local-stt-integration
description: Set up local voice-note transcription with Needle/Whistle or other local ASR engines, connect it to OpenClaw or a similar agent, and compare recognition quality using labeled audio.
---

# Local speech-to-text integration

Reuse upstream inference runtimes. This skill includes a working adapter,
optional faster-whisper backend, corpus importer, and benchmark runner in
[assets/bridge](assets/bridge). It does not require an OpenClaw core patch.

## Install the bundled bridge

Resolve paths against this skill directory, not the caller's working directory.
Choose a separate writable project directory; do not install into the skill tree.
Python 3.12, `uv`, and FFmpeg are required by the setup script. Setup supports
Linux x86-64/ARM64 and macOS ARM64; runtime checks were performed on Linux x86-64.

```sh
python3 /absolute/path/to/this-skill/scripts/install.py /path/to/local-stt --setup
```

The installer refuses an existing destination. Setup downloads pinned Python
dependencies, the native Needle engine, and Whistle weights; it runs the bundled
tests and creates `config.local.toml`. It does not modify the agent configuration.
Use `--whisper` to install the optional faster-whisper dependencies as well; its
model download remains explicit. See [references/usage.md](references/usage.md)
for model downloads, corpus commands, JSON contracts, and engine switching.

## Connect the agent

1. Read the installed agent's incoming-audio documentation and inspect its current
   transcription configuration. For OpenClaw read `docs/nodes/audio.md` and
   `docs/nodes/media-understanding.md`; CLI templates and provider selection vary
   by version. Inspect only the relevant config subtree, not credentials.
2. Run the upstream native binary's `--help` and an actual audio transcription.
   `needle` from pip is a management CLI; the downloaded native `needle` binary is
   the inference CLI. The bundled adapter calls the latter.
3. From the installed bridge directory, transcribe a known local file and print
   the OpenClaw config fragment:

   ```sh
   .venv/bin/stt-bridge --config config.local.toml transcribe /path/to/voice.ogg
   .venv/bin/stt-bridge --config config.local.toml openclaw-config
   ```

4. Merge that fragment into `tools.media`, preserving image/video entries and
   other unrelated settings. Save the previous media subtree privately for
   rollback. Configure only local audio entries if the user wants local-only
   transcription. Do not silently retain a cloud audio fallback. For other agents,
   connect their audio hook to the same transcript-only command.
5. Validate OpenClaw with `openclaw config validate --json`, then run
   `openclaw infer audio transcribe --file /path/to/voice.ogg --json`. Require the
   expected transcript, `transport: local`, and the intended adapter. Check that
   the gateway accepted the configuration; request a fresh channel voice note to
   verify Telegram/other delivery separately.

The generated entry uses absolute command/config paths, a nonempty argv list,
`{{AttachmentPath}}`, and text stdout. The wrapper accepts an empty `{{Language}}`
as autodetection. JSON output is for benchmarks, never agent transcript input.

## Privacy and inference boundaries

- Downloads are explicit setup actions. Inference uses local paths; built-in
  backends disable Needle and Hugging Face telemetry and request offline mode.
  `NEEDLE_TELEMETRY=0`, `DO_NOT_TRACK=1`, and
  `HF_HUB_DISABLE_TELEMETRY=1` are set before upstream invocation.
- The wrapper uses argv arrays, not shell interpolation, and converts to a private
  temporary 16 kHz mono PCM WAV. It cleans temporary files and kills subprocess
  groups on deadline. Errors exit nonzero with empty stdout; silence succeeds
  with empty stdout. No automatic copy of incoming notes is retained.
- Keep recordings, reference transcripts, models, local configs, and reports out
  of git. Retention through `add-note` is explicit. Avoid uploading real audio to
  test the setup. Arbitrary command backends retain their own network behavior.
- If available, trace a representative inference with
  `strace -f -qq -e trace=network -o TRACE EXECUTABLE ...`. Describe zero observed
  calls as evidence for that run, not a universal guarantee.
- Explicit language and keyword hints are supported. Chat-thread reasoning after
  transcription does not mean the recognizer consumes conversation context.

## Verify quality separately

Run both a repeatable smoke corpus and human-labeled real voice notes. Compare
engines on the same normalized audio and hints. Record WER/CER, keyword recall,
silence false positives, failures, and latency; always show failure counts beside
accuracy. Missing confidence stays null; word probabilities are not calibrated
across engines. Fresh-process/model-load latency is not warm service throughput.

The bundled smoke generator uses one checksum-verified public English recording,
Opus/noise variants, and silence. It verifies plumbing, not outdoor, mumbled,
Spanish, or code-switched accuracy. Do not auto-label a benchmark with the engine
under evaluation. Evaluate vocabulary hints separately from unhinted recognition.

References: [OpenClaw audio](https://docs.openclaw.ai/nodes/audio),
[Needle runtime](https://github.com/cactus-compute/needle),
[Whistle model](https://cactuscompute.com/blog/whistle).

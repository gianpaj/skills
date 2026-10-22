# Portable local STT skill

The `local-stt-integration` skill ships a self-contained bridge in `assets/bridge`
and a non-overwriting installer. The bridge reuses the native Needle CLI and
offers optional faster-whisper and JSON-command backends. Agent configuration
changes remain separate from dependency/model installation.

Bundling the working source gives another agent a reproducible implementation.
A link to the machine-local project would not be usable by other people. Model
weights, recordings, transcripts, local config, reports and virtual environments
are excluded; setup fetches pinned dependencies and upstream model artifacts.

The canonical workflow is `SKILL.md`; command details live in
`references/usage.md`. This repository copy is user-owned and edited as ordinary
files, independently of any OpenClaw-managed learned skill with the same name.

Verification: skill validator passed; a clean install into a path containing
spaces passed all 18 bundled tests and real native Whistle Opus transcription.
The installer rejected an existing destination. The live agent configuration
was not changed by this packaging task. Linux x86-64 was exercised; other listed
setup platforms require their own runtime checks.

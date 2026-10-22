"""Public English speech + codec/noise/silence checks. Not an accuracy benchmark."""
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.request import urlopen
import wave

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus/smoke"
URL = "https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/samples/jfk.wav"
SHA256 = "59dfb9a4acb36fe2a2affc14bacbee2920ff435cb13cc314a08c13f66ba7860e"
REFERENCE = "And so my fellow Americans ask not what your country can do for you ask what you can do for your country"


def main():
    CORPUS.mkdir(parents=True, exist_ok=True)
    clean = CORPUS / "jfk.wav"
    if not clean.exists():
        with urlopen(URL, timeout=30) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != SHA256:
            raise SystemExit("Public sample changed; verify its source before updating the checksum")
        clean.write_bytes(data)
    if hashlib.sha256(clean.read_bytes()).hexdigest() != SHA256:
        raise SystemExit("Existing sample checksum mismatch")
    def ffmpeg(*args):
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *map(str, args)], check=True)
    ffmpeg("-i", clean, "-c:a", "libopus", "-b:a", "32k", CORPUS / "jfk.ogg")
    ffmpeg("-i", clean, "-f", "lavfi", "-i", "anoisesrc=color=white:amplitude=0.025:seed=42:r=16000",
           "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:normalize=0",
           "-c:a", "libopus", "-b:a", "32k", CORPUS / "jfk-noisy.ogg")
    with wave.open(str(CORPUS / "silence.wav"), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(bytes(16000 * 2 * 2))
    rows = []
    for identifier, filename, tags in [
        ("jfk-clean", "jfk.wav", ["en", "clean"]),
        ("jfk-opus", "jfk.ogg", ["en", "opus"]),
        ("jfk-noisy", "jfk-noisy.ogg", ["en", "synthetic-noise", "opus"]),
        ("silence", "silence.wav", ["silence"]),
    ]:
        rows.append({"id": identifier, "audio": filename,
                     "reference": "" if identifier == "silence" else REFERENCE,
                     "language": "en", "tags": ["smoke", *tags], "keywords": [],
                     "sha256": hashlib.sha256((CORPUS / filename).read_bytes()).hexdigest(),
                     "source": URL if identifier != "silence" else "generated digital silence"})
    (CORPUS / "manifest.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    print(CORPUS / "manifest.jsonl")


if __name__ == "__main__":
    main()

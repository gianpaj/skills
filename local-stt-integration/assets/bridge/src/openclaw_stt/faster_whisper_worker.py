"""Optional process-isolated backend; models must already exist on disk."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--language")
    parser.add_argument("--keywords-file", required=True)
    args = parser.parse_args()
    from faster_whisper import WhisperModel

    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type,
                         local_files_only=True)
    keywords = Path(args.keywords_file).read_text().splitlines()
    segments, info = model.transcribe(
        args.audio, language=args.language, beam_size=args.beam_size,
        word_timestamps=True, initial_prompt=", ".join(keywords) or None,
    )
    segments = list(segments)  # Decoding is lazy: consume it before producing output.
    print(json.dumps({
        "text": "".join(segment.text for segment in segments).strip(),
        "language": info.language,
        "words": [{"word": word.word.strip(), "start": word.start, "end": word.end,
                   "probability": word.probability}
                  for segment in segments for word in (segment.words or [])],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Standalone XTTS v2 voice-clone synthesizer.

Runs in the isolated ``.venv-xtts`` environment (heavy torch/coqui stack), so the
main Mourice env stays clean. Mourice calls this as a subprocess.

Usage:
    python scripts/xtts_speak.py --text "..." --speaker ref.wav --out out.wav \
        [--language ru] [--device cpu]
"""

from __future__ import annotations

import argparse
import os

# Accept the Coqui model license non-interactively (personal/local use).
os.environ.setdefault("COQUI_TOS_AGREED", "1")

_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


def main() -> None:
    parser = argparse.ArgumentParser(description="XTTS voice-clone synthesis")
    parser.add_argument("--text", required=True)
    parser.add_argument("--speaker", required=True, help="reference voice .wav")
    parser.add_argument("--out", required=True, help="output .wav path")
    parser.add_argument("--language", default="ru")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--temperature", type=float, default=0.75)
    parser.add_argument("--speed", type=float, default=0.9)
    parser.add_argument("--repetition-penalty", type=float, default=5.0)
    parser.add_argument("--top-k", type=int, default=25)
    parser.add_argument("--top-p", type=float, default=0.78)
    parser.add_argument("--pitch", type=float, default=1.0)
    args = parser.parse_args()

    import subprocess
    import tempfile
    from pathlib import Path

    from TTS.api import TTS

    tts = TTS(_MODEL)
    tts.to(args.device)

    if args.pitch != 1.0:
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.wav"
            tts.tts_to_file(
                text=args.text,
                speaker_wav=args.speaker,
                language=args.language,
                file_path=str(raw),
                temperature=args.temperature,
                speed=args.speed,
                repetition_penalty=args.repetition_penalty,
                top_k=args.top_k,
                top_p=args.top_p,
            )
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(raw),
                    "-af", f"asetrate=22050*{args.pitch},atempo=1/{args.pitch}",
                    args.out,
                ],
                check=True, capture_output=True,
            )
    else:
        tts.tts_to_file(
            text=args.text,
            speaker_wav=args.speaker,
            language=args.language,
            file_path=args.out,
            temperature=args.temperature,
            speed=args.speed,
            repetition_penalty=args.repetition_penalty,
            top_k=args.top_k,
            top_p=args.top_p,
        )


if __name__ == "__main__":
    main()

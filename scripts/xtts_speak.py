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
    args = parser.parse_args()

    from TTS.api import TTS

    tts = TTS(_MODEL)
    tts.to(args.device)
    tts.tts_to_file(
        text=args.text,
        speaker_wav=args.speaker,
        language=args.language,
        file_path=args.out,
    )


if __name__ == "__main__":
    main()

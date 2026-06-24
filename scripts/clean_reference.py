"""One-shot script: denoise + normalize a reference WAV for XTTS.

Usage:
    python scripts/clean_reference.py "Пиздатый голос.wav" "Пиздатый голос.wav"
    (source and dest can be the same — overwrites in place)
"""

import sys
from pathlib import Path

import noisereduce as nr
import numpy as np
import soundfile as sf


def clean(src: Path, dst: Path) -> None:
    audio, sr = sf.read(src, always_2d=False)
    audio = audio.astype(np.float32)

    # Estimate noise from first 0.5s (usually silence/room tone)
    noise_sample = audio[: int(sr * 0.5)]
    cleaned = nr.reduce_noise(y=audio, sr=sr, y_noise=noise_sample, prop_decrease=0.8)

    # Peak normalize to -1 dBFS
    peak = np.max(np.abs(cleaned))
    if peak > 0:
        cleaned = cleaned / peak * 0.891  # 10^(-1/20)

    sf.write(dst, cleaned, sr, subtype="PCM_16")
    dur = len(cleaned) / sr
    print(f"Done: {dst} ({dur:.1f}s, {sr} Hz)")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Пиздатый голос.wav")
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src
    clean(src, dst)

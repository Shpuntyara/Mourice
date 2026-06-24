"""XTTS v2 persistent daemon — loads model once, serves synthesis over TCP.

Start once; stays alive. Each request is a JSON line:
    {"text": "...", "out": "/abs/path/to/out.wav"}
Response is a JSON line:
    {"ok": true}  or  {"ok": false, "error": "..."}

Mourice connects via XttsDaemonSpeaker instead of spawning a new subprocess per
utterance, eliminating the ~25 s model-load overhead on every reply.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import noisereduce as nr
import soundfile as sf
from scipy.signal import butter, sosfilt

os.environ.setdefault("COQUI_TOS_AGREED", "1")

_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
_DEFAULT_PORT = 5199


def _postprocess(raw: Path, out: str, pitch: float) -> None:
    """Denoise + normalize synthesized audio in Python (scipy + noisereduce)."""
    audio, sr = sf.read(str(raw), always_2d=False)
    audio = audio.astype(np.float32)

    # Highpass at 80 Hz — remove low-frequency rumble
    sos = butter(4, 80, btype="highpass", fs=sr, output="sos")
    audio = sosfilt(sos, audio).astype(np.float32)

    # Spectral noise reduction — use tail silence as noise profile
    noise_sample = audio[-int(sr * 0.3):] if len(audio) > sr * 0.3 else audio[:int(sr * 0.2)]
    audio = nr.reduce_noise(y=audio, sr=sr, y_noise=noise_sample, prop_decrease=0.75).astype(np.float32)

    # Peak normalize to -1 dBFS
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.891

    if pitch != 1.0:
        # Pitch shift via ffmpeg (rate trick) — only when actually needed
        sf.write(out + ".tmp.wav", audio, sr, subtype="PCM_16")
        subprocess.run(
            ["ffmpeg", "-y", "-i", out + ".tmp.wav",
             "-af", f"asetrate={sr}*{pitch},atempo=1/{pitch}", out],
            check=True, capture_output=True,
        )
        Path(out + ".tmp.wav").unlink(missing_ok=True)
    else:
        sf.write(out, audio, sr, subtype="PCM_16")


def _handle(conn: socket.socket, tts: object, args: argparse.Namespace) -> None:
    data = b""
    while not data.endswith(b"\n"):
        chunk = conn.recv(4096)
        if not chunk:
            return
        data += chunk

    req = json.loads(data.decode())
    text: str = req["text"]
    out_path: str = req["out"]

    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.wav"
        tts.tts_to_file(  # type: ignore[attr-defined]
            text=text,
            speaker_wav=args.speaker,
            language=args.language,
            file_path=str(raw),
            temperature=args.temperature,
            speed=args.speed,
            repetition_penalty=args.repetition_penalty,
            top_k=args.top_k,
            top_p=args.top_p,
        )
        _postprocess(raw, out_path, args.pitch)

    conn.send((json.dumps({"ok": True}) + "\n").encode())


def main() -> None:
    parser = argparse.ArgumentParser(description="XTTS v2 synthesis daemon")
    parser.add_argument("--speaker", required=True)
    parser.add_argument("--language", default="ru")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--temperature", type=float, default=0.55)
    parser.add_argument("--speed", type=float, default=0.88)
    parser.add_argument("--repetition-penalty", type=float, default=5.0)
    parser.add_argument("--top-k", type=int, default=25)
    parser.add_argument("--top-p", type=float, default=0.78)
    parser.add_argument("--pitch", type=float, default=1.0)
    parser.add_argument("--port", type=int, default=_DEFAULT_PORT)
    args = parser.parse_args()

    from TTS.api import TTS

    print(f"[xtts_daemon] Loading model on {args.device}...", flush=True)
    tts = TTS(_MODEL)
    tts.to(args.device)
    print(f"[xtts_daemon] Ready on port {args.port}", flush=True)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", args.port))
    server.listen(4)

    while True:
        conn, _ = server.accept()
        try:
            _handle(conn, tts, args)
        except Exception as exc:
            try:
                conn.send((json.dumps({"ok": False, "error": str(exc)}) + "\n").encode())
            except Exception:
                pass
        finally:
            conn.close()


if __name__ == "__main__":
    main()

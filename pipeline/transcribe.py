#!/usr/bin/env python3
"""Transcribe work/<slug>/src.wav con Parakeet TDT 0.6B v3 (local, gratis) y guarda palabras con tiempos.

Uso: python pipeline/transcribe.py <slug>
Crea work/<slug>/words.json = [{"t": segundos_en_src, "w": "palabra"}] y imprime el texto con tiempos.
"""
import glob
import json
import os
import sys

import numpy as np
import sherpa_onnx
import soundfile as sf

from common import workdir


def model_dir():
    for p in (os.environ.get("ASR_DIR"),
              *glob.glob(os.path.expanduser("~/asr/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"))):
        if p and os.path.isdir(p):
            return p + "/"
    sys.exit("modelo ASR no encontrado: corre `bash setup.sh`")


def main():
    slug = sys.argv[1]
    d = workdir(slug)
    m = model_dir()
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=m + "encoder.int8.onnx", decoder=m + "decoder.int8.onnx", joiner=m + "joiner.int8.onnx",
        tokens=m + "tokens.txt", num_threads=2, model_type="nemo_transducer", decoding_method="greedy_search")
    x, sr = sf.read(os.path.join(d, "src.wav"), dtype="float32")
    assert sr == 16000
    C = 30 * sr
    words = []
    for i in range(0, len(x), C):
        if len(x) - i < sr:  # resto < 1 s: el modelo falla con trozos diminutos
            break
        s = rec.create_stream()
        s.accept_waveform(sr, x[i:i + C])
        rec.decode_stream(s)
        cur, t0 = "", None
        for t, k in zip(list(s.result.timestamps), list(s.result.tokens)):
            if k.startswith("▁") or k.startswith(" "):
                if cur:
                    words.append({"t": round(t0 + i / sr, 2), "w": cur})
                cur, t0 = k.lstrip("▁ "), t
            else:
                t0 = t if t0 is None else t0
                cur += k
        if cur:
            words.append({"t": round(t0 + i / sr, 2), "w": cur})
    with open(os.path.join(d, "words.json"), "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False)
    print(" ".join(f"[{w['t']:.1f}]{w['w']}" for w in words))


if __name__ == "__main__":
    main()

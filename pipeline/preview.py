#!/usr/bin/env python3
"""Evalúa qué tan "gracioso/viral" es cada candidato ANTES de elegir (baja solo el clip de Twitch, en 360p).

Uso: python pipeline/preview.py [--top 10] [--slugs a,b,c]
Toma los candidatos de discover.py, baja cada clip, mide el audio (picos de reacción, gritos, risas) y lo transcribe.
Imprime una ficha por clip y un ranking por `chispa` (0-100). La decisión final la toma quien corre el pipeline,
leyendo la transcripción: ¿hay un remate, una reacción fuerte, un fail, una sorpresa, algo que haga reír?
"""
import argparse
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

from common import find_tdl, workdir
from discover import discover

LAUGH = re.compile(r"\b(j+a+j+[ja]*|j+e+j+[je]*|ha(ha)+h?|he(he)+|jaja\w*|jeje\w*|lol|lmao|xd+|risa\w*|me muero|"
                   r"me meo|llor\w+|muerto|dead)\b", re.I)
REACT = re.compile(r"\b(no puede ser|no me lo creo|qu[eé] (co[ñn]o|mierda|locura|hostia|fuerte)|wtf|omg|oh my god|"
                   r"holy|no way|what the|bro+|loco|puta|co[ñn]o|joder|hostia|dios m[ií]o|socorro|ayuda|"
                   r"mira|miren|espera|esper[aá]|no no no|para para)\b", re.I)
# Groserías: indicador (no condición) de humor, sobre todo dichas por un streamer en plena reacción.
PROF = re.compile(r"\b(mierda\w*|joder\w*|co[ñn]o|puta\w*|put[oa]s?|hostia\w*|cabr[oó]n\w*|carajo|chingad\w*|"
                  r"verga|culiao\w*|conchetumare|weon\w*|wn|mam[oó]n\w*|gilipollas|choto|pedo|co[jg]er|pendejo\w*|"
                  r"shit\w*|fuck\w*|damn|ass|asshole|bitch\w*|dick|bastard|hell)\b", re.I)
TITLE_FUN = re.compile(r"(lmao|lol|jaja|jeje|xd|😂|💀|🤣|omg|wtf|no way|crazy|insane|loco|locura|se cae|fail|"
                       r"muri|muero|borra|hueles|why|cuando|pillaron|pillado|rage|scream|grit)", re.I)


def model():
    import glob
    import sherpa_onnx
    m = next(iter(glob.glob(os.path.expanduser("~/asr/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"))), None)
    if not m:
        sys.exit("modelo ASR no encontrado: corre `bash setup.sh`")
    m += "/"
    return sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=m + "encoder.int8.onnx", decoder=m + "decoder.int8.onnx", joiner=m + "joiner.int8.onnx",
        tokens=m + "tokens.txt", num_threads=2, model_type="nemo_transducer", decoding_method="greedy_search")


def audio_metrics(wav):
    x, sr = sf.read(wav, dtype="float32")
    n = int(sr * 0.1)
    frames = x[: len(x) // n * n].reshape(-1, n)
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-6)
    med, p98 = float(np.median(db)), float(np.percentile(db, 98))
    thr = med + 9
    bursts, last = 0, -99
    for i, v in enumerate(db):
        if v > thr and i - last > 8:  # picos de reacción separados por >0.8 s
            bursts += 1
        if v > thr:
            last = i
    return {"spike_db": round(p98 - med, 1), "bursts": bursts, "loud_pct": round(float((db > thr).mean() * 100), 1),
            "p98_db": round(p98, 1)}


def transcribe(rec, wav):
    x, sr = sf.read(wav, dtype="float32")
    s = rec.create_stream()
    s.accept_waveform(sr, x)
    rec.decode_stream(s)
    return s.result.text.strip()


def chispa(n, m, text):
    """Heurística 0-100: reacciones fuertes en el audio + risas + exclamaciones + título con gancho."""
    sc = min(m["spike_db"], 24) / 24 * 30          # qué tan fuerte es el pico frente a lo normal
    sc += min(m["bursts"], 5) / 5 * 10             # varios picos = risas / gritos repetidos
    sc += min(len(LAUGH.findall(text)), 4) / 4 * 25
    sc += min(len(REACT.findall(text)), 4) / 4 * 15
    sc += min(len(PROF.findall(text)), 3) / 3 * 15  # groserías: indicador de reacción cómica (no lo decide todo)
    sc += 5 if TITLE_FUN.search(n.get("title") or "") else 0
    if len(text.split()) < 6:                      # casi sin habla: depende de la imagen, no se puede juzgar aquí
        sc = min(sc, 55)
    return round(sc)


BONUS = {"MUST": 15, "PRIO": 10, "": 0}


def final_score(n):
    """chispa + bonus por creador obligatorio/prioritario (+5 si habla español). Con chispa < 30 no hay bonus que valga."""
    bonus = BONUS.get(n.get("tier") or "", 0) + (5 if n.get("language") == "ES" else 0)
    return n["chispa"] + (bonus if n["chispa"] >= 30 else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=14)
    ap.add_argument("--slugs", default="")
    a = ap.parse_args()
    cands = discover(top=40)
    if a.slugs:
        want = a.slugs.split(",")
        cands = [c for c in cands if c["slug"] in want]
    else:
        cands = cands[: a.top]
    if not cands:
        sys.exit("sin candidatos")
    tdl, rec, res = find_tdl(), model(), []
    for n in cands:
        d = workdir("_prev")
        mp4, wav = os.path.join(d, n["slug"] + ".mp4"), os.path.join(d, n["slug"] + ".wav")
        try:
            subprocess.run([tdl, "clipdownload", "--id", n["slug"], "-q", "360", "-o", mp4, "--collision", "Overwrite",
                            "--banner", "false"], capture_output=True, timeout=180, check=True)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-ac", "1", "-ar", "16000", wav],
                           check=True)
            m = audio_metrics(wav)
            text = transcribe(rec, wav)
        except Exception as e:  # noqa: BLE001 - un clip que falla no debe frenar a los demás
            print(f"[{n['slug']}] no se pudo evaluar: {e}", file=sys.stderr)
            continue
        n["chispa"], n["audio"], n["texto"] = chispa(n, m, text), m, text
        res.append(n)
        print(f"\n[{n['chispa']:3}] {(n['broadcaster'] or {}).get('login', ''):14} {n['tier'] or '-':4} "
              f"{n['viewCount']}v {n['durationSeconds']}s {n['language']}  {n['title']!r}\n"
              f"      slug={n['slug']}  audio={m}\n      texto: {text[:420]}")
    for r in res:
        r["final"] = final_score(r)
    res.sort(key=lambda r: r["final"], reverse=True)
    print("\n=== RANKING FINAL (chispa + bonus ES/PRIO/MUST; elegir de arriba hacia abajo, mínimo chispa 40) ===")
    for r in res:
        print(f"{r['final']:3} (chispa {r['chispa']:3}) {r['tier'] or '-':4} {(r['broadcaster'] or {}).get('login', ''):14} "
              f"{r['viewCount']:>7}v  {r['title'][:50]!r} slug={r['slug']}")
    json.dump(res, open(os.path.join(workdir("_prev"), "ranking.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

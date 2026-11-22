#!/usr/bin/env python3
"""Registro de clips ya publicados (state/published.json) para no repetir.

Uso:
  python pipeline/state.py list
  python pipeline/state.py add --slug S [--vod V --offset O --title T --yt ID --ig ID --streamer X]
  python pipeline/state.py merge-yt        # agrega al registro lo que YouTube ya tiene ([src:slug] en descripción)
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
import os

from common import ROOT, load_state, save_state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "add", "merge-yt"])
    ap.add_argument("--slug")
    ap.add_argument("--vod")
    ap.add_argument("--offset", type=float)
    ap.add_argument("--title")
    ap.add_argument("--yt")
    ap.add_argument("--ig")
    ap.add_argument("--streamer")
    a = ap.parse_args()
    s = load_state()
    if a.cmd == "list":
        print(json.dumps(s, ensure_ascii=False, indent=1))
    elif a.cmd == "add":
        if not a.slug:
            sys.exit("--slug requerido")
        s.append({k: v for k, v in dict(slug=a.slug, vod=a.vod, offset=a.offset, title=a.title, yt=a.yt,
                                        ig=a.ig, streamer=a.streamer,
                                        ts=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")).items()
                  if v is not None})
        save_state(s)
        print(f"registrado {a.slug} ({len(s)} en total)")
    else:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "pipeline", "publish_youtube.py"), "recent"],
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit(r.stderr[-500:])
        have = {x["slug"] for x in s}
        new = [x for x in json.loads(r.stdout) if x["slug"] not in have]
        s += new
        save_state(s)
        print(f"{len(new)} agregados desde YouTube")


if __name__ == "__main__":
    main()

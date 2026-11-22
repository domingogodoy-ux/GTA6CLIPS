#!/usr/bin/env python3
"""Descarga el momento de un clip desde el VOD en calidad Source (con margen) y extrae el audio.

Uso: python pipeline/fetch.py <slug>
Crea work/<slug>/{src.mp4, src.wav, meta.json}. En meta.json, `clip_start` es el segundo de
src.mp4 donde empieza el clip original de Twitch y `clip_end` donde termina.
"""
import json
import os
import shutil
import sys

from common import cfg, find_tdl, gql, run, workdir


def clip_info(slug):
    q = ('{clip(slug:"%s"){title slug viewCount durationSeconds createdAt language '
         'broadcaster{login displayName} video{id} videoOffsetSeconds}}') % slug
    return (gql(q).get("data") or {}).get("clip")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    slug = sys.argv[1]
    c = cfg()
    info = clip_info(slug)
    if not info:
        sys.exit("clip no encontrado")
    d = workdir(slug)
    src = os.path.join(d, "src.mp4")
    tdl = find_tdl()
    ffmpeg = shutil.which("ffmpeg")
    vod = (info.get("video") or {}).get("id")
    off = info.get("videoOffsetSeconds")
    dur = info["durationSeconds"]
    meta = {"slug": slug, "info": info, "mode": None}
    ok = False
    if vod and off is not None:
        start = max(0, int(off) - c["pad_before"])
        end = int(off + dur) + c["pad_after"]
        r = None
        for _ in range(2):  # TwitchDownloader aborta a veces; reintento una vez
            try:
                run([tdl, "videodownload", "--id", str(vod), "-q", "Source", "-b", str(start), "-e", str(end),
                     "--ffmpeg-path", ffmpeg, "-o", src])
                ok = os.path.exists(src) and os.path.getsize(src) > 100000
            except SystemExit:
                ok = False
            if ok:
                break
        if ok:
            meta.update(mode="vod", vod=vod, offset=off, vod_start=start, vod_end=end,
                        clip_start=off - start, clip_end=off - start + dur)
    if not ok:  # VOD borrado o fallo: bajo solo el clip (puede ser de menor calidad)
        run([tdl, "clipdownload", "--id", slug, "-o", src, "--ffmpeg-path", ffmpeg])
        meta.update(mode="clip", vod=vod, offset=off, clip_start=0, clip_end=dur)
    wav = os.path.join(d, "src.wav")
    run([ffmpeg, "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav])
    pr = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
              "stream=width,height,r_frame_rate:format=duration", "-of", "json", src])
    p = json.loads(pr.stdout)
    meta["width"], meta["height"] = p["streams"][0]["width"], p["streams"][0]["height"]
    meta["fps"] = p["streams"][0]["r_frame_rate"]
    meta["duration"] = float(p["format"]["duration"])
    with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: meta[k] for k in ("mode", "width", "height", "duration", "clip_start", "clip_end")}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Arma el video vertical 1080x1920 a 60 fps (fondo desenfocado + juego + cámara + subtítulos + blur).

Subcomandos:
  frame  <video> <segundos> <salida.png>        extrae un fotograma (para elegir recortes / portada)
  sheet  <video> <salida.jpg> [cada_N_segundos]  hoja de contactos para revisar contenido sensible
  render <spec.json>                             genera el video

spec.json:
{
  "slug": "...",
  "segments": [[ini, fin], ...],            # segundos en src.mp4; varios = se concatenan
  "game_crop": [x, y, w, h] | null,         # recorte del juego (si null: centro automático)
  "cam_crop":  [x, y, w, h] | null,         # recorte de la cámara del streamer (si null: sin cámara)
  "subs": [{"a": 4.3, "b": 6.9, "text": "¡TEXTO!", "hl": false}],  # tiempos relativos al clip final
  "blur": [{"a": 3.0, "b": 5.5, "box": [x, y, w, h]}],             # zonas a difuminar; tiempos del clip final,
                                                                   # box en coordenadas de src.mp4
  "out": "clip.mp4"
}
"""
import json
import os
import shutil
import sys
import textwrap

from common import FONT, run, workdir

W, H, FPS = 1080, 1920, 60
GAME_H = 1166          # alto del recuadro del juego (1080x1166)
CAM_W = 770
YELLOW = "0xFFE600"


def cmd_frame(video, t, out):
    run([shutil.which("ffmpeg"), "-y", "-ss", str(t), "-i", video, "-frames:v", "1", out])


def cmd_sheet(video, out, step=2):
    step = float(step)
    run([shutil.which("ffmpeg"), "-y", "-i", video, "-vf",
         f"fps=1/{step},scale=480:-1,tile=4x6", "-frames:v", "1", out])


def _blur_chain(blur, src_label, n):
    """Cadena de filtros que difumina cajas en ventanas de tiempo. Devuelve (filtros, etiqueta_final)."""
    parts, cur = [], src_label
    for i, b in enumerate(blur or []):
        x, y, w, h = [int(v) for v in b["box"]]
        nxt = f"vb{i}"
        parts.append(f"[{cur}]split=2[base{i}][t{i}];"
                     f"[t{i}]crop={w}:{h}:{x}:{y},boxblur=40:8[bl{i}];"
                     f"[base{i}][bl{i}]overlay={x}:{y}:enable='between(t,{b['a']},{b['b']})'[{nxt}]")
        cur = nxt
    return parts, cur


def _warn_big_blur(spec):
    """Avisa si una caja de blur es grande: el blur debe ser pequeño y ceñido a lo sensible."""
    gc = spec.get("game_crop") or [0, 0, 1920, 1080]
    area = gc[2] * gc[3]
    for b in spec.get("blur") or []:
        bw, bh = b["box"][2], b["box"][3]
        if bw * bh > 0.10 * area:
            print(f"AVISO: blur {bw}x{bh} cubre {bw*bh/area:.0%} del juego (max. recomendado 10%). Achicar la caja.")


def cmd_render(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    _warn_big_blur(spec)
    slug = spec["slug"]
    d = workdir(slug)
    meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
    src = os.path.join(d, "src.mp4")
    sw, sh = meta["width"], meta["height"]
    segs = spec["segments"]
    ff = shutil.which("ffmpeg")

    cam = spec.get("cam_crop")
    gc = spec.get("game_crop")
    if not gc:  # recorte central con la proporción del recuadro del juego
        gh = sh
        gw = int(round(gh * W / GAME_H))
        gc = [(sw - gw) // 2, 0, gw, gh]
    gc = [int(round(v)) for v in gc]
    exp_h = round(gc[2] * GAME_H / W)
    if abs(exp_h - gc[3]) > 0.03 * exp_h:  # corrijo la proporción para no deformar
        gc[3] = min(exp_h, sh - gc[1])
    game_y = 120 if cam else (H - GAME_H) // 2
    sub_y = 1050 if cam else 1450
    cam_y = int(spec.get("cam_y", 1340))

    inputs = []
    for a, b in segs:
        inputs += ["-ss", f"{a}", "-t", f"{b - a}", "-i", src]
    n = len(segs)
    parts = []
    for i in range(n):
        parts.append(f"[{i}:v]setpts=PTS-STARTPTS,fps={FPS}[v{i}]")
        parts.append(f"[{i}:a]asetpts=PTS-STARTPTS[a{i}]")
    if n == 1:
        parts.append("[v0]null[vc]")
        parts.append("[a0]anull[aout]")
    else:
        parts.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vc]")
        parts.append("".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[aout]")
    bparts, cur = _blur_chain(spec.get("blur"), "vc", n)
    parts += bparts
    outs = ["bgsrc", "gsrc"] + (["csrc"] if cam else [])
    parts.append(f"[{cur}]split={len(outs)}" + "".join(f"[{o}]" for o in outs))
    parts.append(f"[bgsrc]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                 f"boxblur=30:5,eq=brightness=-0.12[bg]")
    parts.append(f"[gsrc]crop={gc[2]}:{gc[3]}:{gc[0]}:{gc[1]},scale={W}:{GAME_H}[g]")
    parts.append(f"[bg][g]overlay=0:{game_y}[o1]")
    last = "o1"
    if cam:
        cx, cy, cw, ch = [int(v) for v in cam]
        parts.append(f"[csrc]crop={cw}:{ch}:{cx}:{cy},scale={CAM_W}:-2[cam]")
        parts.append(f"[o1][cam]overlay=(W-w)/2:{cam_y}[o2]")
        last = "o2"
    # subtítulos
    dts = []
    for i, s in enumerate(spec.get("subs", [])):
        tf = os.path.join(d, f"sub{i}.txt")
        with open(tf, "w", encoding="utf-8") as f:
            f.write("\n".join(textwrap.wrap(s["text"], 20)))
        color = YELLOW if s.get("hl") else "white"
        dts.append(f"drawtext=fontfile={FONT}:textfile={tf}:fontsize=84:fontcolor={color}:borderw=7:"
                   f"bordercolor=black:line_spacing=6:x=(w-text_w)/2:y={sub_y}-text_h/2:"
                   f"enable='between(t,{s['a']},{s['b']})'")
    if dts:
        parts.append(f"[{last}]" + ",".join(dts) + "[v]")
    else:
        parts.append(f"[{last}]null[v]")
    fs = os.path.join(d, "filter.txt")
    with open(fs, "w", encoding="utf-8") as f:
        f.write(";\n".join(parts))
    out = spec.get("out", os.path.join(d, "clip.mp4"))
    if not os.path.isabs(out):
        out = os.path.join(d, out)
    run([ff, "-y", *inputs, "-filter_complex_script", fs, "-map", "[v]", "-map", "[aout]",
         "-c:v", "libx264", "-crf", "17", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-dn", "-map_metadata", "-1",
         "-map_chapters", "-1", out])
    pr = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
              "-of", "json", out])
    print(out, pr.stdout.replace("\n", " "))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("frame", "sheet", "render"):
        sys.exit(__doc__)
    {"frame": cmd_frame, "sheet": cmd_sheet, "render": cmd_render}[sys.argv[1]](*sys.argv[2:])

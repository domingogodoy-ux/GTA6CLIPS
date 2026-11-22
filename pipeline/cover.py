#!/usr/bin/env python3
"""Crea la portada de YouTube (1280x720) y la de Reels (1080x1920, texto dentro de la zona segura).

Uso: python pipeline/cover.py <cover.json>

cover.json:
{
  "bg": "ruta/fotograma.png",                  # fotograma de buena resolución (edit.py frame)
  "face": "ruta/cara.png",                     # cara (idealmente mejorada con IA); "face_box": [x0,y0,x1,y1] opcional
  "yt_crop": [x0,y0,x1,y1], "rl_crop": [x0,y0,x1,y1],   # recortes del fotograma (16:9 y 9:16)
  "bar": "NOMBRE JUEGA GTA VI",                # barra blanca superior
  "yt_lines": [["TEXTO","white"],["¡GIGANTE!","yellow"]], "rl_lines": [...],
  "yt_circle": [cx,cy,rx,ry], "rl_circle": [cx,cy,rx,ry],   # círculo rojo (opcional)
  "yt_arrow": [[x0,y0],[x1,y1]],               # flecha roja (opcional)
  "yt_face_xy": "bl" | [x,y], "rl_face_xy": [x,y],
  "sharp": false, "out": "ruta/base"           # genera base_YT_1280x720.jpg y base_REELS_1080x1920.jpg
}
Zona segura Reels: texto y cara entre y=240 y y=1680 (la cuadrícula del perfil recorta los bordes).
"""
import json
import math
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import FONT  # noqa: E402

COL = {"white": "white", "yellow": (255, 230, 0), "red": (255, 30, 30)}


def F(s):
    return ImageFont.truetype(FONT, s)


def grade(im):
    return ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.4)).enhance(1.12)


def stroke(d, xy, t, font, fill, sw=10):
    d.text(xy, t, font=font, fill=fill, stroke_width=sw, stroke_fill="black")


def face_card(path, size, angle=-6, border=12, box=None, sharp=False):
    im = Image.open(path).convert("RGB")
    if box:
        im = im.crop(tuple(box))
    f = im.resize((size, size), Image.LANCZOS)
    if sharp:
        f = f.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=2))
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 7, fill=255)
    card = Image.new("RGBA", (size + 2 * border, size + 2 * border), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, card.size[0] - 1, card.size[1] - 1),
                                           radius=size // 7 + border, fill=(255, 255, 255, 255))
    card.paste(f, (border, border), m)
    return card.rotate(angle, expand=True, resample=Image.BICUBIC)


def arrow(d, p0, p1, col=(255, 30, 30), w=14):
    d.line([tuple(p0), tuple(p1)], fill="black", width=w + 8)
    d.line([tuple(p0), tuple(p1)], fill=col, width=w)
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    L = 46
    d.polygon([tuple(p1), (p1[0] - L * math.cos(a - 0.45), p1[1] - L * math.sin(a - 0.45)),
               (p1[0] - L * math.cos(a + 0.45), p1[1] - L * math.sin(a + 0.45))], fill=col)


def ellipse(d, c, rx, ry, w=10):
    d.ellipse((c[0] - rx - 3, c[1] - ry - 3, c[0] + rx + 3, c[1] + ry + 3), outline="black", width=w + 6)
    d.ellipse((c[0] - rx, c[1] - ry, c[0] + rx, c[1] + ry), outline=(255, 30, 30), width=w)


def bar(d, Wd, y, h, t, fs):
    d.rectangle((0, y, Wd, y + h), fill="white")
    f = F(fs)
    w = d.textlength(t, font=f)
    d.text(((Wd - w) / 2, y + (h - fs) // 2 - 4), t, font=f, fill="black")


def fit_font(d, text, size, max_w):
    while size > 40 and d.textlength(text, font=F(size)) > max_w:
        size -= 4
    return F(size)


def make(c):
    bg = Image.open(c["bg"]).convert("RGB")
    # --- YouTube 1280x720
    im = grade(bg.crop(tuple(c["yt_crop"])).resize((1280, 720), Image.LANCZOS))
    d = ImageDraw.Draw(im)
    bar(d, 1280, 0, 66, c["bar"], 44)
    for i, (t, col) in enumerate(c["yt_lines"]):
        f = fit_font(d, t, 110, 1224)
        w = d.textlength(t, font=f)
        stroke(d, (1262 - w if c.get("yt_right", True) else 28, 76 + i * 118), t, f, COL.get(col, col), 10)
    if c.get("yt_circle"):
        cx, cy, rx, ry = c["yt_circle"]
        ellipse(d, (cx, cy), rx, ry)
    if c.get("yt_arrow"):
        arrow(d, *c["yt_arrow"])
    card = face_card(c["face"], 330, box=c.get("face_box"), sharp=c.get("sharp", False))
    xy = c.get("yt_face_xy", "bl")
    xy = (10, 720 - card.size[1] + 10) if xy == "bl" else tuple(xy)
    im = im.convert("RGBA")
    im.alpha_composite(card, xy)
    im.convert("RGB").save(c["out"] + "_YT_1280x720.jpg", quality=95)
    # --- Reels 1080x1920 (zona segura y 240..1680)
    im = grade(bg.crop(tuple(c["rl_crop"])).resize((1080, 1920), Image.LANCZOS))
    d = ImageDraw.Draw(im)
    bar(d, 1080, 250, 80, c["bar"], 52)
    y0 = c.get("rl_text_y", 1130)
    for i, (t, col) in enumerate(c["rl_lines"]):
        f = fit_font(d, t, c.get("rl_fs", 130), 1030)
        w = d.textlength(t, font=f)
        stroke(d, ((1080 - w) / 2, y0 + i * 140), t, f, COL.get(col, col), 12)
    if c.get("rl_circle"):
        cx, cy, rx, ry = c["rl_circle"]
        ellipse(d, (cx, cy), rx, ry)
    card = face_card(c["face"], 380, box=c.get("face_box"), sharp=c.get("sharp", False))
    im = im.convert("RGBA")
    im.alpha_composite(card, tuple(c.get("rl_face_xy", [14, 350])))
    im.convert("RGB").save(c["out"] + "_REELS_1080x1920.jpg", quality=95)
    print(c["out"] + "_YT_1280x720.jpg", c["out"] + "_REELS_1080x1920.jpg")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    make(json.load(open(sys.argv[1], encoding="utf-8")))

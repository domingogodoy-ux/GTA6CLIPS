#!/usr/bin/env python3
"""Publica un Reel en Instagram con la API oficial (Instagram API with Unified Login, graph.facebook.com), subida resumable.

Variables de entorno: IG_USER_ID, IG_ACCESS_TOKEN  (token de usuario del sistema; no caduca)
Uso:
  python pipeline/publish_instagram.py publish <video.mp4> <caption.json> [cover_url]
  python pipeline/publish_instagram.py check       # verifica que el token y la cuenta funcionan (no publica)

caption.json: {"ig_caption": "..."}
Portada: usar antes `ig_cover_frame.py` (pone la portada como primer fotograma y se publica con thumb_offset=0).
cover_url (opcional, alternativa): URL pública de la portada del Reel (la API no acepta archivo local para la portada).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com/v25.0"


def _req(url, data=None, headers=None, method=None):
    r = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(r, timeout=600) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} en {url[:90]}: {e.read()[:700].decode('utf-8', 'replace')}")


def publish(video, caption, cover_url=None):
    uid, tok = os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"]
    form = {"media_type": "REELS", "upload_type": "resumable", "caption": caption[:2200],
            "share_to_feed": "true", "access_token": tok}
    if cover_url:
        form["cover_url"] = cover_url
    else:
        # La portada va como primer fotograma del video (ver ig_cover_frame.py): miniatura = fotograma 0.
        form["thumb_offset"] = "0"
    c = _req(f"{GRAPH}/{uid}/media", urllib.parse.urlencode(form).encode(),
             {"Content-Type": "application/x-www-form-urlencoded"}, "POST")
    cid = c["id"]
    up = c.get("uri") or f"https://rupload.facebook.com/ig-api-upload/v25.0/{cid}"
    size = os.path.getsize(video)
    with open(video, "rb") as f:
        data = f.read()
    _req(up, data, {"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(size)}, "POST")
    status = None
    for _ in range(60):  # hasta ~5 min procesando
        s = _req(f"{GRAPH}/{cid}?fields=status_code,status&access_token={tok}")
        status = s.get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram rechazó el video: {s}")
        time.sleep(5)
    else:
        sys.exit(f"Instagram no terminó de procesar (último estado: {status})")
    p = _req(f"{GRAPH}/{uid}/media_publish",
             urllib.parse.urlencode({"creation_id": cid, "access_token": tok}).encode(),
             {"Content-Type": "application/x-www-form-urlencoded"}, "POST")
    mid = p["id"]
    info = _req(f"{GRAPH}/{mid}?fields=permalink&access_token={tok}")
    return {"id": mid, "url": info.get("permalink")}


def check():
    tok, uid = os.environ["IG_ACCESS_TOKEN"], os.environ["IG_USER_ID"]
    r = _req(f"{GRAPH}/{uid}?fields=username&access_token={tok}")
    return {"ok": True, "username": r.get("username")}


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "publish":
        cap = json.load(open(sys.argv[3], encoding="utf-8"))
        print(json.dumps(publish(sys.argv[2], cap["ig_caption"], sys.argv[4] if len(sys.argv) > 4 else None)))
    elif len(sys.argv) == 2 and sys.argv[1] == "check":
        print(json.dumps(check()))
    else:
        sys.exit(__doc__)

#!/usr/bin/env python3
"""Sube un video a YouTube (Shorts) con la API oficial, solo con la librería estándar.

Variables de entorno: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
Uso:
  python pipeline/publish_youtube.py upload <video.mp4> <caption.json> [portada.jpg]
  python pipeline/publish_youtube.py recent          # lista los slugs de las últimas subidas (marcador [src:slug])

caption.json: {"yt_title": "...", "yt_description": "...", "tags": ["..."], "slug": "..."}
Se agrega el marcador `[src:<slug>]` al final de la descripción para poder evitar duplicados.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

# oauth2.googleapis.com puede estar bloqueado en el entorno; este endpoint equivalente de Google suele estar permitido.
TOKEN_URL = os.environ.get("YT_TOKEN_URL", "https://www.googleapis.com/oauth2/v4/token")
API = "https://www.googleapis.com"


def _req(url, data=None, headers=None, method=None):
    r = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(r, timeout=600) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} en {url[:80]}: {e.read()[:600].decode('utf-8', 'replace')}")


def access_token():
    body = urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    _, _, b = _req(TOKEN_URL, body, {"Content-Type": "application/x-www-form-urlencoded"})
    return json.loads(b)["access_token"]


def upload(video, cap, thumb=None):
    tok = access_token()
    desc = cap["yt_description"].rstrip()
    if cap.get("slug"):
        desc += f"\n\n[src:{cap['slug']}]"
    meta = {"snippet": {"title": cap["yt_title"][:100], "description": desc[:5000],
                        "tags": cap.get("tags", [])[:15], "categoryId": "20"},
            "status": {"privacyStatus": cap.get("privacy", "public"), "selfDeclaredMadeForKids": False}}
    size = os.path.getsize(video)
    _, h, _ = _req(f"{API}/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                   json.dumps(meta).encode(),
                   {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                    "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)}, "POST")
    loc = h.get("Location") or h.get("location")
    with open(video, "rb") as f:
        data = f.read()
    _, _, b = _req(loc, data, {"Content-Type": "video/mp4", "Content-Length": str(size)}, "PUT")
    vid = json.loads(b)
    res = {"id": vid["id"], "url": f"https://youtube.com/shorts/{vid['id']}",
           "privacy": vid.get("status", {}).get("privacyStatus")}
    if thumb:  # miniatura personalizada: puede exigir canal verificado; si falla, se sigue igual
        try:
            with open(thumb, "rb") as f:
                _req(f"{API}/upload/youtube/v3/thumbnails/set?videoId={vid['id']}&uploadType=media",
                     f.read(), {"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"}, "POST")
            res["thumbnail"] = True
        except SystemExit as e:
            res["thumbnail"] = f"falló: {e}"
    return res


def recent():
    tok = access_token()
    h = {"Authorization": f"Bearer {tok}"}
    _, _, b = _req(f"{API}/youtube/v3/channels?part=contentDetails&mine=true", headers=h)
    up = json.loads(b)["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    _, _, b = _req(f"{API}/youtube/v3/playlistItems?part=snippet&maxResults=50&playlistId={up}", headers=h)
    out = []
    for it in json.loads(b).get("items", []):
        m = re.search(r"\[src:([^\]]+)\]", it["snippet"].get("description", ""))
        if m:
            out.append({"slug": m.group(1), "yt": it["snippet"]["resourceId"]["videoId"]})
    return out


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "upload":
        cap = json.load(open(sys.argv[3], encoding="utf-8"))
        print(json.dumps(upload(sys.argv[2], cap, sys.argv[4] if len(sys.argv) > 4 else None)))
    elif len(sys.argv) == 2 and sys.argv[1] == "recent":
        print(json.dumps(recent()))
    else:
        sys.exit(__doc__)

"""Utilidades compartidas del pipeline gta6clips."""
import json
import os
import shutil
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
STATE_FILE = os.path.join(ROOT, "state", "published.json")
FONT = os.path.join(ROOT, "assets", "Anton.ttf")

GQL_URL = "https://gql.twitch.tv/gql"
GQL_CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"


def cfg():
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def gql(query):
    req = urllib.request.Request(
        GQL_URL,
        data=json.dumps({"query": query}).encode(),
        headers={"Client-ID": GQL_CLIENT_ID, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_state(items):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)


def find_tdl():
    for p in (os.environ.get("TDL"), os.path.expanduser("~/tdl/TwitchDownloaderCLI"),
              shutil.which("TwitchDownloaderCLI")):
        if p and os.path.exists(p):
            return p
    sys.exit("TwitchDownloaderCLI no encontrado: corre `bash setup.sh`")


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.stderr.write((r.stdout or "")[-1500:] + (r.stderr or "")[-1500:])
        sys.exit(f"falló: {' '.join(map(str, cmd))[:200]}")
    return r


def workdir(slug):
    d = os.path.join(WORK, slug)
    os.makedirs(d, exist_ok=True)
    return d

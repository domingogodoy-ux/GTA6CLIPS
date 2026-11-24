#!/usr/bin/env python3
"""Lista los clips más virales de GTA VI en Twitch que aún no se han publicado.

Uso: python pipeline/discover.py [--top 15] [--json]
"""
import argparse
import datetime as dt
import json
import re
import sys

from common import cfg, gql, load_state


def fetch(game, period, langs, n=100):
    q = ('{game(name:"%s"){clips(first:%d,criteria:{period:%s,sort:VIEWS_DESC,languages:[%s]})'
         '{edges{node{title slug viewCount durationSeconds createdAt language '
         'broadcaster{login displayName} video{id} videoOffsetSeconds}}}}}') % (game, n, period, ",".join(langs))
    d = gql(q)
    g = (d.get("data") or {}).get("game")
    return [e["node"] for e in (g["clips"]["edges"] if g else [])]


def already(node, state, window):
    vod = (node.get("video") or {}).get("id")
    off = node.get("videoOffsetSeconds")
    for s in state:
        if s.get("slug") == node["slug"]:
            return True
        if vod and s.get("vod") == vod and off is not None and s.get("offset") is not None \
                and abs(s["offset"] - off) <= window:
            return True
    return False


def discover(top=15):
    """Devuelve los candidatos nuevos ordenados por puntaje (lista de nodos de clip)."""
    c = cfg()
    state = load_state()
    skip = re.compile(c["skip_title_regex"], re.I)
    now = dt.datetime.now(dt.timezone.utc)
    seen, out = set(), []
    for period in c["periods"]:
        for node in fetch(c["game"], period, c["languages"]):
            if node["slug"] in seen:
                continue
            seen.add(node["slug"])
            b = (node.get("broadcaster") or {}).get("login", "")
            pref = node.get("language") == c.get("preferred_language")
            must = b.lower() in [x.lower() for x in c.get("must_broadcasters", [])]
            prio = b.lower() in [x.lower() for x in c.get("priority_broadcasters", [])]
            minv = c["min_views"]
            if pref:
                minv = c.get("preferred_language_min_views", minv)
            if prio:
                minv = min(minv, c.get("priority_min_views", minv))
            if must:
                minv = min(minv, c.get("must_min_views", minv))
            if node["viewCount"] < minv:
                continue
            node["tier"] = "MUST" if must else ("PRIO" if prio else "")
            if not (c["min_clip_seconds"] <= node["durationSeconds"] <= c["max_clip_seconds"]):
                continue
            if skip.search(node["title"] or "") or b in c["blocked_broadcasters"]:
                continue
            if not node.get("video") or node.get("videoOffsetSeconds") is None:
                node["_no_vod"] = True  # se podrá bajar solo el clip (calidad menor)
            if already(node, state, c["dedupe_vod_window_seconds"]):
                continue
            age_h = max(1.0, (now - dt.datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))).total_seconds() / 3600)
            boost = c.get("preferred_language_boost", 1.0) if pref else 1.0
            if prio:
                boost = max(boost, c.get("priority_boost", 1.0))
            if must:
                boost = max(boost, c.get("must_boost", 1.0))
            node["score"] = round(node["viewCount"] / (age_h + 6) ** 0.5 * boost, 1)
            out.append(node)
    out.sort(key=lambda n: n["score"], reverse=True)
    return out[:top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--json", action="store_true", help="imprime solo JSON")
    a = ap.parse_args()
    out = discover(a.top)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    for n in out:
        v = n.get("video") or {}
        print(f'{n["score"]:8} {n["viewCount"]:6}v {n["durationSeconds"]:>3}s {n["language"]} {n.get("tier",""):4} '
              f'{(n["broadcaster"] or {}).get("login",""):16} {n["title"][:55]!r} '
              f'slug={n["slug"]} vod={v.get("id")} off={n.get("videoOffsetSeconds")}'
              f'{" [SIN VOD]" if n.get("_no_vod") else ""}')
    if not out:
        sys.exit("sin candidatos nuevos")


if __name__ == "__main__":
    main()

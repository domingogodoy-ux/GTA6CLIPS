# GTA6CLIPS

Sistema para encontrar los momentos más virales de streamers jugando GTA VI en Twitch, convertirlos en clips
verticales (YouTube Shorts / Instagram Reels) con subtítulos y portadas, y publicarlos.

El criterio (qué clip elegir, dónde cortar, subtítulos, portada, caption) lo pone Claude siguiendo
[`RUNBOOK.md`](RUNBOOK.md); los scripts de `pipeline/` hacen el trabajo mecánico.

| Script | Qué hace |
|---|---|
| `pipeline/discover.py` | Clips más vistos de GTA VI (24 h y 7 días, ES/EN), filtrados y sin repetir |
| `pipeline/fetch.py` | Baja el momento del VOD en calidad Source y extrae el audio |
| `pipeline/transcribe.py` | Transcripción local con tiempos por palabra (gratis) |
| `pipeline/edit.py` | Vertical 1080x1920@60: fondo desenfocado, juego, cámara, subtítulos, blur de zonas sensibles |
| `pipeline/cover.py` | Portadas YouTube 1280x720 y Reels 1080x1920 |
| `pipeline/publish_youtube.py` | Sube a YouTube con la API oficial |
| `pipeline/publish_instagram.py` | Publica Reels con la API oficial de Instagram |
| `pipeline/state.py` | Registro de lo ya publicado (`state/published.json`) |
| `pipeline/yt_auth.py` | Se corre **una vez en tu PC** para obtener el token de YouTube |

## Secretos (variables de entorno, nunca en el repo)
`YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`, `IG_USER_ID`, `IG_ACCESS_TOKEN`.
El token de Instagram caduca a los 60 días: renovarlo antes con `python3 pipeline/publish_instagram.py refresh`
y reemplazar el secreto.

## Uso manual
```
bash setup.sh
python3 pipeline/discover.py
python3 pipeline/fetch.py <slug> && python3 pipeline/transcribe.py <slug>
# escribir work/<slug>/spec.json y renderizar:
python3 pipeline/edit.py render work/<slug>/spec.json
```

## Aviso
Resubir clips de streamers puede generar reclamos de derechos de autor o strikes. Se da crédito en cada
publicación, pero eso no es un permiso. `config.json` tiene `blocked_broadcasters` para excluir streamers.

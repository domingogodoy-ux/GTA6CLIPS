#!/usr/bin/env python3
"""EJECUTAR UNA VEZ EN TU PC: autoriza tu canal de YouTube y muestra el token de actualización.

Requisitos: Python 3 con `pip install google-auth-oauthlib`.
Uso:  python yt_auth.py ruta/al/client_secret.json

Se abre el navegador, eliges la cuenta/canal y aceptas. En la terminal verás:
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
Guárdalos como variables de entorno/secretos. No los pegues en el chat ni en el repositorio.
"""
import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]

if len(sys.argv) != 2:
    sys.exit(__doc__)
flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
print("\n--- Copia estos tres valores como secretos ---")
print("YT_CLIENT_ID=" + creds.client_id)
print("YT_CLIENT_SECRET=" + creds.client_secret)
print("YT_REFRESH_TOKEN=" + creds.refresh_token)

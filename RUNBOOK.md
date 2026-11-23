# RUNBOOK — una corrida de clipping GTA VI (1 clip publicado por corrida)

Este documento lo sigue Claude en cada tarea programada (8:00, 16:00 y 20:00, hora de Chile).
Nadie supervisa la corrida: Claude decide con criterio, no hace preguntas y deja un resumen al final.
Todo se ejecuta desde la raíz del repositorio. Los pasos 1–3 son mecánicos; el criterio está en los pasos 4–8.

## Reglas permanentes del dueño (Domingo)
- Idioma de textos: español de Chile, tono casual. Nunca bajar la resolución del original (el render usa
  fuente 1080p/1440p y salida 1080x1920@60 con CRF 17). No abusar de zooms.
- **Prioridad a creadores en español**: la mayoría de los clips del día (al menos 2 de cada 3) deben ser de
  streamers que hablan español. `discover.py` ya les da más puntaje (x2.5) y acepta menos vistas (150); aun así,
  antes de elegir mira `state/published.json`: si en las últimas 24 h hubo menos de 2 clips en español por
  cada 3 publicados, elige un candidato `ES` aunque sea algo menos viral. Solo se publica uno en inglés si es
  claramente mucho mejor o si no hay ningún candidato en español de calidad aceptable (dilo en el resumen).
- **Creadores obligatorios (si o si): Rubius, Ibai y Auronplay.** Si `discover.py` muestra un candidato con
  marca `MUST` (viene de `must_broadcasters` en `config.json`) que cumpla los criterios del paso 1, **se elige ese**
  antes que cualquier otro, aunque tenga pocas vistas, salvo que ya se haya publicado un clip del mismo streamer
  en las últimas 8 h. Si no hay ninguno, se sigue con los `PRIO` (creadores en español destacados: TheGrefg,
  elxokas, Knekro, IlloJuan, DjMaRiiO, ElSpreen, Coscu, Spursito, Mixwell, Vegetta777, etc.) y luego el resto.
  Para agregar más creadores basta editar `priority_broadcasters` o `must_broadcasters` en `config.json`.
- Publicar **público e inmediato**, sin revisión. 3 clips al día.
- Contenido sensible (desnudez, sexo, drogas, violencia gráfica): **no se descarta, se difumina** solo la zona
  problemática (`blur` en el spec) y se publica igual. Excepción: si la escena es explícita de principio a fin y
  el blur taparía casi todo el encuadre, se salta ese candidato y se toma el siguiente.
- Las portadas con cara usan Seedream 5.5 (Higgsfield) para mejorar la cara **sin pedir confirmación de costo**
  (excepción acordada solo para portadas). Cualquier otra generación con costo: no hacerla.
  Si Higgsfield rechaza la cara (`ip_detected`), usar la cara sin mejorar; nunca intentar saltarse el rechazo.
- No ingresar ni mostrar contraseñas/tokens. Los secretos son variables de entorno; nunca imprimirlos.
- Siempre dar crédito al streamer en el caption ("Clip de @streamer en Twitch").

## 0. Preparación (siempre)
```
bash setup.sh                 # ffmpeg, librerías, TwitchDownloaderCLI, modelo de transcripción (~3-6 min la 1ª vez)
python3 pipeline/state.py merge-yt   # evita repetir: agrega lo ya subido a YouTube ([src:slug]); si falla, sigue
```
Si faltan `YT_CLIENT_ID`, `YT_CLIENT_SECRET` o `YT_REFRESH_TOKEN`, hacer el clip igual, **no publicar**, y avisar
claramente en el resumen cuáles faltan. Si faltan solo `IG_USER_ID`/`IG_ACCESS_TOKEN` (Instagram aún no conectado),
publicar en YouTube normalmente, omitir Instagram y mencionarlo en una línea del resumen.

## 1. Descubrir
```
python3 pipeline/discover.py --top 15
```
Elegir **un** candidato: el más viral que cumpla (a) momento autocontenido que se pueda cortar en 15–60 s con
inicio y desenlace claros, (b) no repetido, (c) no es un anuncio/drop, (d) alterna streamers entre
corridas (mirar `state/published.json`: evitar el mismo streamer dos veces seguidas). Los clips de
habla hispana (`ES`) son prioridad, según la regla permanente de arriba.

## 2. Descargar y transcribir
```
python3 pipeline/fetch.py <slug>          # work/<slug>/src.mp4 (VOD en calidad Source con margen) + meta.json
python3 pipeline/transcribe.py <slug>     # work/<slug>/words.json y texto con tiempos
```
`meta.json` trae `clip_start`/`clip_end`: dónde está el clip original dentro de `src.mp4`. El margen antes/después
sirve para completar el contexto o el desenlace si el clip de Twitch se corta antes.

## 3. Mirar el material
```
python3 pipeline/edit.py sheet work/<slug>/src.mp4 work/<slug>/sheet.jpg 2.5   # hoja de contactos; abrirla con Read
python3 pipeline/edit.py frame work/<slug>/src.mp4 <t> work/<slug>/f.png       # fotograma a resolución completa
```
Con la hoja y los fotogramas decidir: recorte del juego (`game_crop`), recorte de la cámara del streamer
(`cam_crop`, o `null` si no hay), zonas sensibles y sus tiempos, y el chat/overlays que haya que evitar en el recorte.

## 4. Spec y subtítulos
Escribir `work/<slug>/spec.json` (formato en la cabecera de `pipeline/edit.py`):
- `segments`: 15–60 s en total. Empieza justo antes del gancho y termina en el desenlace/reacción. Cortes sobre
  la transcripción (`words.json`), no a ojo. Se pueden unir dos tramos si hay un salto muerto.
- `subs`: frases cortas, MAYÚSCULAS, ≤ 2 líneas de 20 caracteres, tiempos **relativos al clip final**;
  `hl: true` (amarillo) para la palabra/frase clave. Traducir al español si el streamer habla en inglés.
  Corregir lo que el ASR escuche mal (nombres, modismos, groserías); suavizar groserías fuertes con asteriscos.
  No poner títulos explicativos sobre lo que ya se ve.
- `blur`: cajas en coordenadas de `src.mp4` con ventana de tiempo, para lo sensible (paso 3).
```
python3 pipeline/edit.py render work/<slug>/spec.json
```
Revisar el resultado: extraer 3–4 fotogramas con `edit.py frame` sobre el mp4 final y comprobar que los subtítulos
no tapan la acción, el blur cubre lo que debe, y la duración está en 15–60 s. Si algo falla, corregir el spec y
volver a renderizar (máximo 2 reintentos).

## 5. Portadas
1. Fotograma de buena calidad (sin chat ni overlays en el recorte) con `edit.py frame`.
2. Recortar la cara del streamer (cuadrado) y mejorarla: `media_upload` → PUT con curl → `media_confirm` →
   `generate_image` con `seedream_5_5`, relación 1:1, resolución 2k, la cara como `image_references`,
   prompt: solo mejorar la calidad (nitidez, detalle), sin cambiar rasgos/expresión → `jobs_wait` → descargar.
3. Escribir `work/<slug>/cover.json` (formato en `pipeline/cover.py`) y correr
   `python3 pipeline/cover.py work/<slug>/cover.json`. Texto gigante blanco + amarillo, círculo/flecha roja
   sobre lo que importa, barra superior "STREAMER JUEGA GTA VI". En Reels, todo entre y=240 e y=1680.
4. Mirar ambas imágenes (Read) y corregir si hay texto cortado o tapando la cara.

## 6. Caption
Escribir `work/<slug>/caption.json`:
```
{"slug": "<slug>",
 "yt_title": "gancho corto con emoji + #Shorts",
 "yt_description": "1-2 líneas casuales + 'Clip de @streamer en Twitch: <url del clip>' + hashtags",
 "tags": ["GTA 6", "GTA VI", "<streamer>", "clips", "shorts"],
 "ig_caption": "caption casual + CTA (ej. 'Comenta y sígueme para más GTA 6 🔥') + crédito + 12-20 hashtags"}
```

## 7. Publicar (solo si hay credenciales)
```
python3 pipeline/publish_youtube.py upload work/<slug>/clip.mp4 work/<slug>/caption.json work/<slug>/cover_YT_1280x720.jpg
python3 pipeline/publish_instagram.py publish work/<slug>/clip.mp4 work/<slug>/caption.json [cover_url]
```
- YouTube primero. Verificar en la salida que `privacy` sea `public`; si salió `private`, avisarlo en el resumen.
- Instagram: la portada del Reel solo se acepta como URL pública. Opcional: copiar la portada de Reels a
  `covers/<slug>.jpg`, hacer commit + push, esperar a que
  `https://domingogodoy-ux.github.io/GTA6CLIPS/covers/<slug>.jpg` responda 200 y pasarla como `cover_url`.
  Si no se puede, publicar sin ella y enviar la portada en el chat.
- **No reintentar una publicación que pudo haberse completado** (riesgo de duplicado). Ante un error de red
  después de subir, comprobar primero con `publish_youtube.py recent` o en la respuesta si el video ya existe.
- Si una plataforma falla, igual publicar en la otra y reportar el fallo.

## 8. Registrar y entregar
```
python3 pipeline/state.py add --slug <slug> --vod <vod> --offset <offset> --title "<título>" --yt <id> --ig <id> --streamer <login>
git add state/published.json && git commit -m "Publica <slug>" && git push     # si no hay permiso de push, seguir
```
Enviar a la conversación con `SendUserFile`: el video final y las dos portadas (YouTube y Reels). Cerrar con un
resumen de 4–6 líneas con `SendUserMessage`: clip elegido y por qué, streamer, links publicados, si se difuminó algo,
y cualquier problema (credenciales ausentes, privacidad en privado, portada sin mejorar, token por vencer).
El token de Instagram es de usuario del sistema y no caduca. Si Instagram responde error de token/permisos, avisar claramente en el resumen.

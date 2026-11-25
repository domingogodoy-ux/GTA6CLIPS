# RUNBOOK — una corrida de clipping GTA VI (1 clip publicado por corrida)

Este documento lo sigue Claude en cada tarea programada (8:00, 12:00, 16:00, 20:00 y 22:00, hora de Chile).
Nadie supervisa la corrida: Claude decide con criterio, no hace preguntas y deja un resumen al final.
Todo se ejecuta desde la raíz del repositorio. Los pasos 1–3 son mecánicos; el criterio está en los pasos 4–8.

## Reglas permanentes del dueño (Domingo)
- Idioma de textos: español de Chile, tono casual. Nunca bajar la resolución del original (el render usa
  fuente 1080p/1440p y salida 1080x1920@60 con CRF 17). No abusar de zooms.
- **Prioridad a creadores en español**: la mayoría de los clips del día (al menos 3 de cada 5) deben ser de
  streamers que hablan español. `discover.py` ya les da más puntaje (x2.5) y acepta menos vistas (150); aun así,
  antes de elegir mira `state/published.json`: si en las últimas 24 h hubo menos de 3 clips en español por
  cada 5 publicados, elige un candidato `ES` aunque sea algo menos viral. Solo se publica uno en inglés si es
  claramente mucho mejor o si no hay ningún candidato en español de calidad aceptable (dilo en el resumen).
- **Tres categorías de creadores en español (`config.json`)**, de mayor a menor prioridad:
  1. `MUST` (x10): Rubius, AuronPlay, Ibai, IlloJuan, TheGrefg, DjMaRiiO. Si `discover.py` muestra un candidato `MUST`
     que cumpla los criterios del paso 1 **y tenga chispa (>= 40, o sea un momento gracioso)**, se elige ese antes que
     cualquier otro, aunque tenga pocas vistas, salvo que ya se haya publicado un clip del mismo streamer en las últimas
     8 h. Un clip aburrido de un MUST no se publica por ser MUST.
  2. `PRIO` (x4): Vegetta777, Carola, Vicens, Nissaxter, juansguarnizo, ElMariana, Perxitaa, Lolito, ElXokas, ElSpreen,
     Coscu, Knekro, Mixwell, Spursito, Willyrex, TazerCraft.
  3. `EMERG` (x3, mínimo 80 vistas): creadores en español activos en GTA VI con buen alcance (Vicesat, Alewang,
     Superblazing_, Padexxx_, Sinapsis, Ricky Strikis, Folagor, Peereira7, Alexby11, Rivers_gg, jcorko_, Kestico,
     Llobeti4, Paache_, Rene8808, SrTumbao, Wings667, Raptorgamer24, Zelika9, ElCamacho24, GazAdventures).
  Después van los demás clips en español y luego el resto. Para mover o agregar creadores basta editar
  `must_broadcasters`, `priority_broadcasters` o `emerging_broadcasters` en `config.json`.
- Publicar **público e inmediato**, sin revisión. 5 clips al día (uno por corrida).
- Contenido sensible (desnudez, sexo, drogas, violencia gráfica): **no se descarta, se difumina** solo la zona
  problemática (`blur` en el spec) y se publica igual. Excepción: si la escena es explícita de principio a fin y
  el blur taparía casi todo el encuadre, se salta ese candidato y se toma el siguiente.
- Las portadas con cara usan Nano Banana 2.1 (Higgsfield, ~1,5 créditos por imagen) para mejorar la cara **sin pedir confirmación de costo**
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

## 1. Descubrir y elegir lo más GRACIOSO (no lo más "normal")
```
python3 pipeline/preview.py --top 14      # ~2-3 min: baja cada clip en 360p, mide el audio y lo transcribe
```
Lo que funciona en redes es un **momento**: un remate, una reacción exagerada, un fail, un susto, una sorpresa o algo
absurdo que haga reír en los primeros segundos. Un streamer hablando tranquilo, explicando o narrando NO es un clip.
`preview.py` imprime una ficha por clip (audio + transcripción) y un ranking final con la `chispa` (0-100) más el
bonus por idioma/creador. Elegir **un** clip así:
0. Leer `CRITERIO_HUMOR.md` (ejemplos reales de lo que Domingo considera gracioso y lo que no). La `chispa` solo
   preselecciona por audio y texto: **no distingue humor de volumen** (un clip tierno con gritos puede salir alto).
   La decisión es tuya: para los 5 primeros escribir "gracioso porque… (segundo X)" y descartar los que no puedan.
1. Leer las transcripciones del ranking de arriba hacia abajo y quedarse con el primero que de verdad tenga gancho
   (risas, gritos, "no puede ser", un remate claro) y cumpla: (a) momento autocontenido que se corte en 15-60 s,
   (b) no repetido, (c) no es anuncio/drop, (d) no repite streamer dos corridas seguidas (`state/published.json`).
2. Exigir `chispa` >= 40 **y** que pase el filtro de `CRITERIO_HUMOR.md`. Si ninguno llega, correr `python3 pipeline/preview.py --top 25` para ampliar. Si aun así
   ninguno llega, publicar el mejor disponible y decir en el resumen que fue un día flojo.
3. Los creadores obligatorios (MUST) y prioritarios (PRIO) y el español siguen teniendo ventaja, pero solo cuentan si el
   clip tiene chispa: un clip aburrido de Rubius, Ibai o Auronplay pierde contra uno gracioso de otro streamer.
4. Antes de descargar, confirmar con el texto y los fotogramas que el chiste se entiende sin contexto; si hay que
   explicarlo, descartarlo.
`python3 pipeline/discover.py --top 15` sigue existiendo para ver la lista cruda por vistas.

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
- `segments`: 15–60 s en total (ideal 15–35 s). Empieza 1–2 s antes del gancho (nada de intro lenta: lo gracioso debe
  pasar en los primeros 3 s) y termina justo después del remate/reacción, sin estirar. Cortes sobre
  la transcripción (`words.json`), no a ojo. Se pueden unir dos tramos si hay un salto muerto.
- `subs`: frases cortas, MAYÚSCULAS, ≤ 2 líneas de 20 caracteres, tiempos **relativos al clip final**;
  `hl: true` (amarillo) para la palabra/frase clave. Traducir al español si el streamer habla en inglés.
  Corregir lo que el ASR escuche mal (nombres, modismos, groserías); suavizar groserías fuertes con asteriscos.
  No poner títulos explicativos sobre lo que ya se ve.
- `blur`: cajas en coordenadas de `src.mp4` con ventana de tiempo, para lo sensible (paso 3). **Siempre pequeño**:
  la caja ceñida solo a lo sensible (idealmente < 10 % del área del juego, nunca más de 15 %) y solo durante los
  segundos necesarios. Si `edit.py` imprime `AVISO: blur ...`, achicar la caja y volver a renderizar.
- `headline` (**obligatorio en todos los Reels/Shorts**): `{"text": "...", "tag": "VIRAL"}` → banner blanco arriba con el titular
  en negro, grande y en negrita, más etiqueta azul. Es el **hook de storytelling**: debe prometer algo entretenido que
  se paga al final del clip, sin spoilear el remate. Fórmulas: contraste irónico ("AURONPLAY es tan bueno con la gente
  mayor 🤍" y luego la empuja), curiosidad ("Lo que pasó cuando Rubius abrió esa puerta…"), apuesta ("No te vas a creer
  cómo termina esto"). Máx. ~8 palabras, ≤ 3 líneas, español, sin groserías, un ♥/🤍 al final es opcional. Debe ser
  verdad: lo que promete tiene que ocurrir en el clip. El primer subtítulo del clip refuerza el gancho (1–3 s) y el remate
  llega en el último tercio. El juego se mantiene a resolución completa (1080x1166) bajo el banner.
```
python3 pipeline/edit.py render work/<slug>/spec.json
```
Revisar el resultado: extraer 3–4 fotogramas con `edit.py frame` sobre el mp4 final y comprobar que los subtítulos
no tapan la acción, el blur cubre lo que debe, y la duración está en 15–60 s. Si algo falla, corregir el spec y
volver a renderizar (máximo 2 reintentos).

## 5. Portadas
1. Fotograma de buena calidad (sin chat ni overlays en el recorte) con `edit.py frame`.
2. Recortar la cara del streamer (cuadrado) y mejorarla: `media_upload` → PUT con curl → `media_confirm` →
   `generate_image` con `nano_banana_2_1`, relación 1:1, `resolution` 1k, `thinking_level` minimal, `use_unlim` false,
   `count` 1, la cara como `image_references`. Prompt probado: "Enhance this photo: increase sharpness, skin detail
   and overall image quality. Keep the exact same person, face features, expression, headset and framing. Do not
   change identity or expression." → `jobs_wait` → descargar. Una sola generación por portada (sin reintentos de pago).
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
Antes de editar nada, correr `python3 pipeline/publish_instagram.py check` con las credenciales exportadas. Si dice
`mal copiado`, re-exportar el token copiando el valor exacto de la tarea y repetir hasta que responda `ok`; así no
se pierde un Reel por un error de transcripción (ya pasó una vez con el error 190 de Meta).
```
python3 pipeline/publish_youtube.py upload work/<slug>/clip.mp4 work/<slug>/caption.json work/<slug>/cover_YT_1280x720.jpg
python3 pipeline/ig_cover_frame.py work/<slug>/clip.mp4 work/<slug>/cover_REELS_1080x1920.jpg work/<slug>/clip_ig.mp4
python3 pipeline/publish_instagram.py publish work/<slug>/clip_ig.mp4 work/<slug>/caption.json
```
- YouTube primero. Verificar en la salida que `privacy` sea `public`; si salió `private`, avisarlo en el resumen.
- Instagram: la portada del Reel **siempre** debe estar (regla del usuario). Se logra con `ig_cover_frame.py`:
  antepone la portada de Reels (1080x1920) como primer fotograma (1/60 s, sin recodificar el clip) y
  `publish_instagram.py` publica ese `clip_ig.mp4` con `thumb_offset=0`, así la miniatura es la portada.
  Sin GitHub Pages ni URL pública. Usar el nombre real del archivo de portada de Reels de `work/<slug>/`.
  Si `ig_cover_frame.py` falla, publicar el clip normal y reportarlo en el resumen. YouTube usa su portada 1280x720.
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

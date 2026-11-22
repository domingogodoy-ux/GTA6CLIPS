#!/usr/bin/env bash
# Instala las dependencias en una sesión nueva (idempotente). Uso: bash setup.sh
set -euo pipefail
TDL_VERSION="${TDL_VERSION:-1.56.5}"

echo "[1/4] ffmpeg"
command -v ffmpeg >/dev/null || { apt-get update -qq && apt-get install -y -qq ffmpeg; }

echo "[2/4] paquetes Python"
pip install -q --break-system-packages pillow numpy soundfile sherpa-onnx

echo "[3/4] TwitchDownloaderCLI $TDL_VERSION"
if [ ! -x "$HOME/tdl/TwitchDownloaderCLI" ]; then
  mkdir -p "$HOME/tdl" && cd "$HOME/tdl"
  curl -sSL -o tdl.zip "https://github.com/lay295/TwitchDownloader/releases/download/${TDL_VERSION}/TwitchDownloaderCLI-${TDL_VERSION}-Linux-x64.zip"
  python3 -c "import zipfile;zipfile.ZipFile('tdl.zip').extractall('.')" && rm tdl.zip
  chmod +x TwitchDownloaderCLI
fi

echo "[4/4] modelo de transcripción (Parakeet TDT 0.6B v3 int8, ~480 MB)"
M="$HOME/asr/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"
if [ ! -f "$M/encoder.int8.onnx" ]; then
  mkdir -p "$HOME/asr" && cd "$HOME/asr"
  curl -sSL -o m.tar.bz2 "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2"
  tar xjf m.tar.bz2 && rm m.tar.bz2
fi
echo "listo"

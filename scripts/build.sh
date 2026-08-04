#!/bin/bash
set -e

# Detect OS to handle path separator for pyinstaller --add-data correctly
if [ "$(expr substr $(uname -s) 1 5)" == "MINGW" ] || [ "$(expr substr $(uname -s) 1 4)" == "MSYS" ] || [ "$(expr substr $(uname -s) 1 6)" == "CYGWIN" ]; then
  SEP=";"
else
  SEP=":"
fi

OS_NAME=$(echo $(uname -s) | tr '[:upper:]' '[:lower:]')
if [ "$(expr substr $OS_NAME 1 5)" == "mingw" ] || [ "$(expr substr $OS_NAME 1 4)" == "msys" ] || [ "$(expr substr $OS_NAME 1 6)" == "cygwin" ]; then
  SUFFIX="-windows.exe"
elif [ "$OS_NAME" == "darwin" ]; then
  SUFFIX="-macos"
else
  SUFFIX="-linux"
fi

echo "Building CLI..."
uv run pyinstaller --name "job-pipeline-cli${SUFFIX}" --onefile main.py

echo "Building Web UI..."
uv run pyinstaller --name "job-pipeline-ui${SUFFIX}" --onefile \
  --add-data "src/web${SEP}src/web" \
  --copy-metadata streamlit \
  --hidden-import streamlit \
  run_ui.py

echo "Build complete. Executables are in dist/"

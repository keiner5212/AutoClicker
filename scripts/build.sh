#!/usr/bin/env bash
# Build the Linux executable with PyInstaller.
#
# Run:  bash scripts/build.sh [output-name]
# The pynput backend hidden imports live in autoclicker.spec, not here.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_DIR}"

OUTPUT_NAME="${1:-autoclicker-ubuntu-latest}"

if [ ! -d ".venv" ]; then
  bash "${SCRIPT_DIR}/setup.sh"
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! command -v pyinstaller >/dev/null 2>&1; then
  pip install pyinstaller
fi

AUTOCLICKER_NAME="${OUTPUT_NAME}" pyinstaller --clean autoclicker.spec

echo "built : dist/${OUTPUT_NAME}"

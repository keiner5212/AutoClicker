#!/usr/bin/env bash
# Run the autoclicker in the project venv.
#
# Prints what it is about to run and the build fingerprint of the source, so
# a stale or duplicated tree is visible immediately instead of showing up as
# "my changes did nothing".
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_DIR}"

if [ ! -d ".venv" ]; then
  bash "${SCRIPT_DIR}/setup.sh"
fi

# shellcheck disable=SC1091
source .venv/bin/activate

find . -path ./.venv -prune -o -name '__pycache__' -type d -print0 2>/dev/null \
  | xargs -0 rm -rf 2>/dev/null || true

echo "project : ${PROJECT_DIR}" >&2
echo "python  : $(command -v python)" >&2
echo "package : $(python -c 'import autoclicker; print(autoclicker.__file__)')" >&2
echo "build   : $(python -m autoclicker --build 2>/dev/null)" >&2

exec python -m autoclicker "$@"

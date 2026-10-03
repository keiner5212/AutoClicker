#!/usr/bin/env bash
# Run the autoclicker in the project venv.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_DIR}"

if [ ! -d ".venv" ]; then
  bash "${SCRIPT_DIR}/setup.sh"
fi

# shellcheck disable=SC1091
source .venv/bin/activate
exec python -m autoclicker "$@"

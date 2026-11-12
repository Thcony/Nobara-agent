#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    echo "Ambiente não encontrado. Rode ./install.sh primeiro."
    exit 1
fi

source .venv/bin/activate
exec python -m nobara_agent "$@"

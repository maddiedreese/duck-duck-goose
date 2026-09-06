#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -n "${DUCK_PYTHON:-}" ]]; then
  duck_python="$DUCK_PYTHON"
else
  if [[ ! -x .venv/bin/python ]]; then
    if command -v uv >/dev/null 2>&1; then
      uv venv --python 3.12 .venv
      uv pip install --python .venv/bin/python -r requirements.txt
    else
      python3 -m venv .venv
      .venv/bin/python -m pip install -r requirements.txt
    fi
  fi
  duck_python="$PWD/.venv/bin/python"
fi
"$duck_python" -m unittest -v test_game
"$duck_python" main.py "$@"

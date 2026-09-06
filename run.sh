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
# Use EGL on a headless Linux host; physics-only runs need no graphics context.
render_video=true
for duck_arg in "$@"; do
  if [[ "$duck_arg" == "--no-video" ]]; then render_video=false; fi
done
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
if [[ "$(uname -s)" == "Linux" && -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" && "$render_video" == true ]]; then
  export MUJOCO_GL="${MUJOCO_GL:-egl}"
fi
"$duck_python" -m unittest -v test_game
"$duck_python" main.py "$@"

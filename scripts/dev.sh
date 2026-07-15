#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PID_DIR="$ROOT/.devmind/pids"
mkdir -p "$PID_DIR"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command '$1' was not found. Install it manually and retry." >&2
    exit 1
  fi
}

require_command uv
require_command npm
require_command node

cd "$ROOT"
uv run python scripts/check_environment.py

uv run uvicorn devmind_api.main:app --host 127.0.0.1 --port 8000 &
echo "$!" > "$PID_DIR/api.pid"

npm --prefix apps/web run dev &
echo "$!" > "$PID_DIR/web.pid"

if [ "${WORKER_ENABLED:-false}" = "true" ]; then
  uv run python -m devmind_worker.runner &
  echo "$!" > "$PID_DIR/worker.pid"
fi

echo "DevMind AI started."
echo "API: http://127.0.0.1:8000"
echo "Web: http://127.0.0.1:5173"

#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PID_DIR="$ROOT/.devmind/pids"

if [ ! -d "$PID_DIR" ]; then
  echo "No DevMind AI PID directory found."
  exit 0
fi

for pid_file in "$PID_DIR"/*.pid; do
  [ -e "$pid_file" ] || continue
  pid="$(cat "$pid_file")"
  case "$pid" in
    ''|*[!0-9]*) ;;
    *)
      if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        echo "Stopped process $pid from $(basename "$pid_file")."
      fi
      ;;
  esac
  rm -f "$pid_file"
done

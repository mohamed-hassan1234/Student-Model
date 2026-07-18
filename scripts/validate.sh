#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
npm --prefix apps/web run lint
npm --prefix apps/web run typecheck
npm --prefix apps/web run test:run
npm --prefix apps/web run build
uv run python scripts/check_environment.py

if find . -name Dockerfile -o -name docker-compose.yml -o -name docker-compose.yaml | grep .; then
  echo "Prohibited Docker files found." >&2
  exit 1
fi

if grep -R -I -E "(api[_-]?key|password|secret)\s*=\s*['\"][^'\"<]" . \
  --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=dist \
  --exclude-dir=.mypy_cache --exclude-dir=.pytest_cache --exclude-dir=.ruff_cache \
  --exclude-dir=coverage; then
  echo "Potential secret patterns found. Review before continuing." >&2
  exit 1
fi

echo "All validation commands completed."

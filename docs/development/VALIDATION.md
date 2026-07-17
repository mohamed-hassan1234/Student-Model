# Validation

Run all available checks before marking the active phase complete.

## Backend

```powershell
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

## Frontend

```powershell
npm --prefix apps/web run lint
npm --prefix apps/web run typecheck
npm --prefix apps/web run test:run
npm --prefix apps/web run build
```

## Repository

```powershell
uv run python scripts/check_environment.py
scripts/validate.ps1
```

Unix-like:

```sh
./scripts/validate.sh
```

Validation includes prohibited Docker-file checks and a basic secret-pattern scan. If MongoDB is not installed or running, record that limitation in `docs/status/PROJECT_STATUS.md` rather than claiming the MongoDB connectivity check passed.

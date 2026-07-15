# Local Setup

## Requirements

- Python 3.12
- uv
- Node.js 20 or newer
- npm
- MongoDB Community Server, or a MongoDB Atlas URI configured through environment variables

Docker is not used.

## Environment

Copy `.env.example` to `.env` and adjust values. Do not commit `.env`.

## Install

```powershell
uv sync
npm install
npm --prefix apps/web install
```

## MongoDB

Start MongoDB manually using your local installation or configure `MONGODB_URI` for Atlas. Then run:

```powershell
uv run python scripts/check_environment.py --mongodb-only
uv run python scripts/bootstrap_mongodb.py
```

## Start Development

Windows:

```powershell
scripts/dev.ps1
```

Unix-like:

```sh
./scripts/dev.sh
```

Manual commands:

```powershell
uv run uvicorn devmind_api.main:app --host 127.0.0.1 --port 8000
npm --prefix apps/web run dev
uv run python -m devmind_worker.runner
```

The worker exits unless `WORKER_ENABLED=true`.

## Stop Development

Windows:

```powershell
scripts/stop.ps1
```

Unix-like:

```sh
./scripts/stop.sh
```

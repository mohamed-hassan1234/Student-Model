$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
npm --prefix apps/web run lint
npm --prefix apps/web run typecheck
npm --prefix apps/web run test:run
npm --prefix apps/web run build
uv run python scripts/check_environment.py

$DockerFiles = Get-ChildItem -Path $Root -Recurse -Force -File | Where-Object {
    $_.Name -match "^(Dockerfile|docker-compose\.ya?ml)$"
}
if ($DockerFiles.Count -gt 0) {
    throw "Prohibited Docker files found."
}

$SecretMatches = Get-ChildItem -Path $Root -Recurse -Force -File |
    Where-Object { $_.FullName -notmatch "\\node_modules\\|\\.venv\\|\\.git\\|\\dist\\|\\.mypy_cache\\|\\.pytest_cache\\|\\.ruff_cache\\|\\coverage\\" } |
    Select-String -Pattern "api[_-]?key\s*=|password\s*=|secret\s*=" -CaseSensitive:$false
if ($SecretMatches) {
    throw "Potential secret patterns found. Review before continuing."
}

Write-Host "All validation commands completed."

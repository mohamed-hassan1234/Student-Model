$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$PidDir = Join-Path $Root ".devmind\pids"
New-Item -ItemType Directory -Force -Path $PidDir | Out-Null

function Require-Command {
    param([string]$Name)
    $Command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $Command) {
        throw "Required command '$Name' was not found. Install it manually and retry."
    }
    return $Command.Source
}

$UvCommand = Require-Command "uv"
$NpmCommand = if (Get-Command "npm.cmd" -ErrorAction SilentlyContinue) {
    (Get-Command "npm.cmd").Source
} else {
    Require-Command "npm"
}
Require-Command "node" | Out-Null

Set-Location $Root
uv run python scripts/check_environment.py

$Api = Start-Process -FilePath $UvCommand -ArgumentList "run", "uvicorn", "devmind_api.main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory $Root -PassThru -WindowStyle Hidden
$Api.Id | Set-Content -Path (Join-Path $PidDir "api.pid")

$Web = Start-Process -FilePath $NpmCommand -ArgumentList "--prefix", "apps/web", "run", "dev" -WorkingDirectory $Root -PassThru -WindowStyle Hidden
$Web.Id | Set-Content -Path (Join-Path $PidDir "web.pid")

if ($env:WORKER_ENABLED -eq "true") {
    $Worker = Start-Process -FilePath $UvCommand -ArgumentList "run", "python", "-m", "devmind_worker.runner" -WorkingDirectory $Root -PassThru -WindowStyle Hidden
    $Worker.Id | Set-Content -Path (Join-Path $PidDir "worker.pid")
}

Write-Host "DevMind AI started."
Write-Host "API: http://127.0.0.1:8000"
Write-Host "Web: http://127.0.0.1:5173"

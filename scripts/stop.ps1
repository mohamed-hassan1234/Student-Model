$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$PidDir = Join-Path $Root ".devmind\pids"

if (-not (Test-Path $PidDir)) {
    Write-Host "No DevMind AI PID directory found."
    exit 0
}

Get-ChildItem -Path $PidDir -Filter "*.pid" | ForEach-Object {
    $ProcessId = Get-Content $_.FullName
    if ($ProcessId -match "^\d+$") {
        $Process = Get-Process -Id ([int]$ProcessId) -ErrorAction SilentlyContinue
        if ($null -ne $Process) {
            Stop-Process -Id $Process.Id
            Write-Host "Stopped process $($Process.Id) from $($_.Name)."
        }
    }
    Remove-Item -LiteralPath $_.FullName -Force
}

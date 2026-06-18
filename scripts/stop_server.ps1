# Stop service listening on a TCP port (Windows)
# Usage: .\scripts\stop_server.ps1 [-Port 8000]
# Default port: SERVICE_PORT from code\app\.env, else 8000

param(
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$AppDir = Join-Path $RepoRoot "code\app"
$EnvFile = Join-Path $AppDir ".env"

. (Join-Path $RepoRoot "scripts\ps_encoding.ps1")
Initialize-ScriptConsole

if ($Port -le 0 -and (Test-Path $EnvFile)) {
    $fromEnv = Get-Content $EnvFile | Where-Object { $_ -match '^SERVICE_PORT=' } |
        ForEach-Object { ($_ -split '=', 2)[1].Trim() }
    if ($fromEnv -match '^\d+$') {
        $Port = [int]$fromEnv
    }
}
if ($Port -le 0) {
    $Port = 8000
}

Write-Host "[stop] looking for listener on port $Port ..." -ForegroundColor Cyan

$connections = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
if ($connections.Count -eq 0) {
    Write-Host "[stop] no process is listening on port $Port" -ForegroundColor Yellow
    exit 0
}

$pids = @($connections | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -gt 0 })
if ($pids.Count -eq 0) {
    Write-Host "[stop] no process id found for port $Port" -ForegroundColor Yellow
    exit 0
}

$stopped = 0
foreach ($procId in $pids) {
    try {
        $proc = Get-Process -Id $procId -ErrorAction Stop
        Write-Host "[stop] stopping PID $procId ($($proc.ProcessName)) ..." -ForegroundColor Yellow
        Stop-Process -Id $procId -Force -ErrorAction Stop
        $stopped++
    } catch {
        Write-Host "[stop] failed to stop PID ${procId}: $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($stopped -gt 0) {
    Write-Host "[stop] done. freed port $Port ($stopped process(es))." -ForegroundColor Green
    exit 0
}

Write-Host "[stop] could not stop any process on port $Port" -ForegroundColor Red
exit 1

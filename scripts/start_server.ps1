# Start FastAPI server
# Usage: .\scripts\start_server.ps1 [-Port 8000] [-Reload]
# Note: Windows defaults to NO reload (reload can hang browser requests)

param(
    [int]$Port = 0,
    [switch]$Reload
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$AppDir = Join-Path $RepoRoot "code\app"
$EnvFile = Join-Path $AppDir ".env"
$EnvDemo = Join-Path $AppDir ".env.demo"

. (Join-Path $RepoRoot "scripts\conda_common.ps1")
. (Join-Path $RepoRoot "scripts\ps_encoding.ps1")
Initialize-ScriptConsole

if (-not (Test-Path $AppDir)) {
    Write-Error "App directory not found: $AppDir"
}

if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvDemo) {
        Copy-Item $EnvDemo $EnvFile
        Write-Host "[setup] Copied .env.demo -> .env. Edit LLM settings, then restart." -ForegroundColor Yellow
    } else {
        Write-Error "Missing .env and .env.demo"
    }
}

& (Join-Path $RepoRoot "scripts\setup_workspace.ps1") | Out-Null

Push-Location $AppDir
try {
    $env:PYTHONPATH = $AppDir
    if ($Port -gt 0) {
        $env:SERVICE_PORT = "$Port"
    }

    $hostPort = if ($Port -gt 0) { $Port } else {
        (Get-Content $EnvFile | Where-Object { $_ -match '^SERVICE_PORT=' } | ForEach-Object { ($_ -split '=', 2)[1].Trim() })
    }
    if (-not $hostPort) { $hostPort = "8000" }

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " NewHuman API (conda: $(Get-CondaEnvName))" -ForegroundColor Cyan
    Write-Host " Home: http://127.0.0.1:$hostPort/" -ForegroundColor Green
    Write-Host " Chat: http://127.0.0.1:$hostPort/chat" -ForegroundColor Green
    Write-Host " Docs: http://127.0.0.1:$hostPort/docs" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan

    $uvicornArgs = @(
        "-m", "uvicorn", "main:app",
        "--host", "127.0.0.1",
        "--port", $hostPort,
        "--log-level", "info"
    )
    if ($Reload) {
        Write-Host "[warn] --reload on Windows may hang; omit -Reload if browser cannot connect" -ForegroundColor Yellow
        $uvicornArgs += "--reload"
    }
    Invoke-CondaPython @uvicornArgs
} finally {
    Pop-Location
}

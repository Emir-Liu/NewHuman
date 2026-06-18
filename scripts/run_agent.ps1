# Terminal interactive agent (no HTTP server)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$AppDir = Join-Path $RepoRoot "code\app"
$EnvFile = Join-Path $AppDir ".env"

. (Join-Path $RepoRoot "scripts\conda_common.ps1")
. (Join-Path $RepoRoot "scripts\ps_encoding.ps1")
Initialize-ScriptConsole

if (-not (Test-Path $EnvFile)) {
    Write-Host "[hint] Configure code\app\.env first (copy from .env.demo)" -ForegroundColor Yellow
}

& (Join-Path $RepoRoot "scripts\setup_workspace.ps1") | Out-Null

Push-Location $AppDir
try {
    $env:PYTHONPATH = $AppDir
    Write-Host "conda env: $(Get-CondaEnvName)" -ForegroundColor Gray
    Invoke-CondaPython -m func.graph.run
} finally {
    Pop-Location
}

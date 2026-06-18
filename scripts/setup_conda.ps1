# Create or update NewHuman conda environment
# Usage: .\scripts\setup_conda.ps1 [-Recreate]

param(
    [switch]$Recreate
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$EnvFile = Join-Path $RepoRoot "environment.yml"

. (Join-Path $RepoRoot "scripts\conda_common.ps1")
$envName = Get-CondaEnvName

if (-not (Test-CondaCmd)) {
    Write-Error "conda not found. Install Miniconda/Anaconda/Miniforge, then re-run this script."
}

Push-Location $RepoRoot
try {
    if ($Recreate -and (Test-CondaEnvExists -Name $envName)) {
        Write-Host "Removing env: $envName" -ForegroundColor Yellow
        conda env remove -n $envName -y
    }

    if (Test-CondaEnvExists -Name $envName) {
        Write-Host "Updating env: $envName" -ForegroundColor Cyan
        conda env update -f $EnvFile --prune -y
    } else {
        Write-Host "Creating env: $envName" -ForegroundColor Cyan
        conda env create -f $EnvFile -y
    }

    Write-Host ""
    Write-Host "Done. Activate with:" -ForegroundColor Green
    Write-Host "  conda activate $envName"
    Write-Host ""
    Write-Host "Or run scripts directly (uses conda run):" -ForegroundColor Green
    Write-Host '  .\scripts\run_agent.ps1'
    Write-Host '  .\scripts\start_server.ps1'
} finally {
    Pop-Location
}

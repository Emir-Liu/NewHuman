# Activate NewHuman conda env in current PowerShell session
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
. (Join-Path $RepoRoot "scripts\conda_common.ps1")
. (Join-Path $RepoRoot "scripts\ps_encoding.ps1")
Initialize-ScriptConsole
$envName = Get-CondaEnvName

if (-not (Test-CondaCmd)) {
    Write-Error "conda not found"
}
if (-not (Test-CondaEnvExists -Name $envName)) {
    Write-Host "Env missing, creating..." -ForegroundColor Yellow
    & (Join-Path $RepoRoot "scripts\setup_conda.ps1")
}

(& conda shell.powershell hook) | Out-String | Invoke-Expression
conda activate $envName

Write-Host "Activated: $envName (Python: $(python --version))" -ForegroundColor Green
Write-Host "Suggested: `$env:PYTHONPATH = '$RepoRoot\code\app'" -ForegroundColor Gray

# Conda helpers for scripts/*.ps1
$script:CondaEnvName = if ($env:NEWHUMAN_CONDA_ENV) { $env:NEWHUMAN_CONDA_ENV } else { "newhuman" }

function Test-CondaCmd {
    return [bool](Get-Command conda -ErrorAction SilentlyContinue)
}

function Test-CondaEnvExists {
    param([string]$Name = $script:CondaEnvName)
    if (-not (Test-CondaCmd)) { return $false }
    $list = conda env list 2>$null | Out-String
    return $list -match "(?m)^\s*$([regex]::Escape($Name))\s"
}

function Ensure-CondaEnv {
    if (-not (Test-CondaCmd)) {
        Write-Error "conda not found. Run: .\scripts\setup_conda.ps1"
    }
    if (-not (Test-CondaEnvExists)) {
        Write-Error "Conda env '$($script:CondaEnvName)' missing. Run: .\scripts\setup_conda.ps1"
    }
}

function Invoke-CondaPython {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$PythonArgs
    )
    Ensure-CondaEnv | Out-Null
    & conda run --no-capture-output -n $script:CondaEnvName python @PythonArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Get-CondaEnvName {
    return $script:CondaEnvName
}

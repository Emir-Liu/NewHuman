# 运行 MVP 验收测试
# 用法:
#   .\scripts\run_tests.ps1                    # 全部（含 smoke）
#   .\scripts\run_tests.ps1 -Milestone M1      # 仅 M1 里程碑
#   .\scripts\run_tests.ps1 -SmokeOnly         # 仅健康检查（无需 LLM）
# 前置: .\scripts\setup_conda.ps1

param(
    [ValidateSet("M1", "M2", "M3", "M4", "M5", "ALL")]
    [string]$Milestone = "ALL",
    [switch]$SmokeOnly,
    [string]$BaseUrl = $env:TEST_BASE_URL
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

. (Join-Path $RepoRoot "scripts\conda_common.ps1")

if (-not $BaseUrl) {
    $BaseUrl = "http://127.0.0.1:8000"
}
$env:TEST_BASE_URL = $BaseUrl

Push-Location $RepoRoot
try {
    $pytestArgs = @("-m", "pytest", "-v", "--tb=short", "-ra")

    if ($SmokeOnly) {
        $pytestArgs += @("-m", "smoke")
    } elseif ($Milestone -ne "ALL") {
        $marker = "milestone_$($Milestone.ToLower())"
        $pytestArgs += @("-m", "$marker or smoke")
    }

    Write-Host "[test] conda: $(Get-CondaEnvName)" -ForegroundColor Gray
    Write-Host "[test] TEST_BASE_URL=$BaseUrl" -ForegroundColor Gray
    Write-Host "[test] pytest tests/" -ForegroundColor Cyan

    Invoke-CondaPython @pytestArgs tests/
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "`n[test] PASSED" -ForegroundColor Green
        Invoke-CondaPython "$RepoRoot\scripts\check_milestone.py" --from-pytest
    } else {
        Write-Host "`n[test] FAILED (exit $exitCode)" -ForegroundColor Red
        Invoke-CondaPython "$RepoRoot\scripts\check_milestone.py" --from-pytest --failed
    }

    exit $exitCode
} finally {
    Pop-Location
}

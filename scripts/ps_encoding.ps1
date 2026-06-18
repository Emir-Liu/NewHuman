# UTF-8 console for Windows PowerShell 5.x (avoid garbled CJK in Write-Host)
function Initialize-ScriptConsole {
    if ($env:OS -ne "Windows_NT") { return }
    try {
        $null = chcp 65001
    } catch {}
    try {
        [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
        $global:OutputEncoding = [Console]::OutputEncoding
    } catch {}
}

# Initialize workspace/default templates
# Usage: .\scripts\setup_workspace.ps1 [-Repair]
# -Repair: overwrite template files with UTF-8 content (fixes garbled text)

param(
    [switch]$Repair
)

$ErrorActionPreference = "Stop"

. (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "ps_encoding.ps1")
Initialize-ScriptConsole

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$WsRoot = Join-Path $RepoRoot "workspace\default"

$dirs = @(
    $WsRoot,
    (Join-Path $WsRoot "memory"),
    (Join-Path $WsRoot "skills\kb-qa")
)

foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
        Write-Host "[workspace] created directory: $d"
    }
}

$templates = @{
    "SOUL.md" = @"
# SOUL — Agent 人格

你是 NewHuman 个人 AI 助手。回复简洁、准确，优先使用工具获取事实。

- 语言：跟随 USER.md 设定；默认中文
- 风格：专业、友好
"@
    "AGENTS.md" = @"
# AGENTS — 行为准则

- 工作区根目录固定，已在系统提示中给出；**不要**为确认路径反复调用 Get-Location
- 用户只是聊天、寒暄、追问时，**不要**调用工具
- 需要文件内容时调用 read_file，不要编造
- 需要列目录时调用 list_dir（优先于 Get-ChildItem）
- 需要创建文件夹时调用 mkdir
- 需要写文件时调用 write_file
- 需要执行命令时调用 exec_powershell（仅当专用工具不够用时）
- 需要知识库时调用 search_knowledge
- 记忆相关使用 memory_* 工具

## 错误自愈

- 工具执行失败时：分析 ToolMessage，修正后再次调用工具，同一请求最多重试 3 次
- 用户说「帮我执行 / 你来做」时：不要问「是否继续」，直接做
- 不要用 markdown 代码块假装命令已执行；以工具返回为准
"@
    "USER.md" = @"
# USER

- 称呼：用户
- 语言：中文
"@
    "TOOLS.md" = @"
# TOOLS

MVP 可用工具见设计文档 §8.4。

- read_file / list_dir / write_file / mkdir — 工作区文件操作
- exec_powershell — 在 workspace 内执行 PowerShell
- search_knowledge — 知识库检索（M3+）
- memory_* — 长期记忆（M4+）
"@
    "MEMORY.md" = @"
# MEMORY

（长期记忆摘要，由 Agent 通过 memory_append 维护）
"@
    "skills\kb-qa\SKILL.md" = @"
# kb-qa

当用户询问知识库文档内容时：

1. 使用 search_knowledge 检索
2. 基于检索结果回答并注明来源
"@
}

$utf8 = New-Object System.Text.UTF8Encoding $false

foreach ($rel in $templates.Keys) {
    $path = Join-Path $WsRoot $rel
    $parent = Split-Path $path -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }

    if ($Repair -or -not (Test-Path $path)) {
        $existed = Test-Path $path
        [System.IO.File]::WriteAllText($path, $templates[$rel], $utf8)
        $action = if ($Repair -and $existed) { "repaired" } else { "created" }
        Write-Host "[workspace] $action template: $rel"
    }
}

Write-Host "[workspace] ready: $WsRoot"

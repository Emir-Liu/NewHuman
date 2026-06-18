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
    (Join-Path $WsRoot "skills\kb-qa"),
    (Join-Path $WsRoot "skills\skill-creator"),
    (Join-Path $WsRoot "skills\multi-agent")
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

- 工作区根目录固定，已在系统提示「工具使用规则」中给出；**不要**为确认路径反复调用 Get-Location
- 用户只是聊天、寒暄、追问时，**不要**调用工具
- **可用工具以系统提示中的工具表为准**（由 `tool_registry.py` 注册表动态生成），**不要**调用表外工具
- 需要读文件、列目录、写文件、执行命令等操作时，从已注册工具中选最合适的；**不要编造**工具结果或命令输出

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

可用工具以 `code/app/func/graph/tools/tool_registry.py` 中 `_MVP_TOOLS` 注册为准；
系统提示词会**自动**从注册表生成，无需在此重复维护列表。

修改工具：编辑 `tool_registry.py` → 重启服务 → Chat 点「新对话」。
"@
    "MEMORY.md" = @"
# MEMORY

长期记忆摘要（由 Agent 通过 memory_append / memory_update_summary 维护）。
详细日志写入 memory/YYYY-MM-DD.md；回忆时用 memory_search 或 memory_read。
"@
    "skills\kb-qa\SKILL.md" = @"
# kb-qa

当用户询问知识库文档内容时：

1. 使用 search_knowledge 检索
2. 基于检索结果回答并注明来源
"@
    "skills\skill-creator\SKILL.md" = @"
# skill-creator — 创建 Agent 技能

教 Agent 如何在工作区中创建新的 Skill（技能包）。

## 何时创建技能

- 用户反复使用同一类工作流（如「每周写周报」「整理会议纪要」）
- 需要固化领域知识或操作步骤（如项目特有的部署流程、代码规范）
- 需要记录工具组合用法（如「先 list_dir 再 read_file 再 memory_append」）
- 用户明确要求「创建一个 skill / 教你怎么做某事」

**不要**为一次性问答创建技能；技能应聚焦、可复用。

## 目录结构

```
skills/
└── <skill-name>/          # 小写、短横线分隔，如 weekly-report
    └── SKILL.md           # 必需，技能主文件
```

- 路径相对于工作区根目录，例如 `skills/my-skill/SKILL.md`
- 所有路径必须在 workspace 内，禁止访问 workspace 外

## SKILL.md 格式

```markdown
# <技能标题>

<第一段：一句话描述，会出现在系统提示的技能索引中>

## 何时使用

- 触发场景 1
- 触发场景 2

## 步骤

1. 第一步（可含具体工具调用说明）
2. 第二步
3. ...

## 示例

（可选）用户说什么 → Agent 怎么做
```

**要点：**
- 标题用 `#`；第一段或第一个非空行作为摘要（注入 prompt 索引）
- 步骤要具体、可执行，写明该用哪些工具
- 保持单一职责，一个 skill 解决一类任务

## 如何创建

1. 确认技能名称（小写英文 + 短横线，如 `git-commit-helper`）
2. `exec_powershell`：`New-Item -ItemType Directory -Force -Path skills/<skill-name>`
3. `exec_powershell`：`Set-Content -Path skills/<skill-name>/SKILL.md -Value '...' -Encoding UTF8`
4. （可选）`Get-Content skills/<skill-name>/SKILL.md -Encoding UTF8` 读回验证
5. 告知用户：新技能会在**新对话**中出现在「可用技能」索引里

## 命名规范

- 仅小写字母、数字、短横线：`^[a-z0-9]+(-[a-z0-9]+)*$`
- 名称应简短且表意，如 `kb-qa`、`skill-creator`、`code-review`
- 避免与已有技能重名（先用 `Get-ChildItem -Name skills` 检查）

## 维护

- 修改已有技能：`Get-Content` 读取后 `Set-Content` 更新
- 删除技能：`Remove-Item -Recurse -Force skills/<name>`

## 示例：创建一个简单技能

用户：「帮我创建一个 skill，用来总结 daily standup」

Agent 应：
1. 读取本文件（skill-creator）确认规范
2. `New-Item -ItemType Directory -Force -Path skills/standup-summary`
3. `Set-Content` 写入含「何时使用 / 步骤 / 示例」的 SKILL.md
4. 回复用户技能路径与用法
"@
    "skills\multi-agent\SKILL.md" = @"
# multi-agent — 多 Agent 任务分解与委派

教主 Agent 何时拆分任务、如何调用 `delegate_subagent` 并汇总结果。

## 何时使用

- 用户要求**对比**两个及以上方案、产品、技术选型
- 任务跨多个独立领域（如「调研 + 写代码 + 审查」）
- 需要分别收集信息后再综合结论
- 单 Agent 多轮工具调用仍难以覆盖的复杂请求

**不要**为简单单步操作委派（读一个文件、跑一条命令、寒暄）。

## 预设角色（list_agent_roles）

| role | 适用场景 |
|------|----------|
| researcher | 调研、资料检索、方案对比 |
| coder | 读写文件、实现脚本、执行命令 |
| reviewer | 审查输出、找风险与改进点 |
| summarizer | 合并多段结果为简洁报告 |

## 推荐流程

1. 理解用户目标，判断是否需要多 Agent
2. `list_agent_roles`（可选）确认角色
3. 拆成 2–4 个子任务，每个子任务的 `task` 须**自洽**（子 Agent 无父对话历史）
4. **顺序**调用 `delegate_subagent`（MVP 为同步顺序，非并行）
5. 主 Agent 综合各子结果，输出对比表或最终建议

## 示例

**用户：**「帮我调研 A 和 B 两个方案并对比」

**主 Agent 应：**
1. `delegate_subagent(task="调研方案 A：…", role="researcher", context="用户需要与 B 对比")`
2. `delegate_subagent(task="调研方案 B：…", role="researcher", context="用户需要与 A 对比")`
3. 综合两次 ToolMessage，输出对比维度（成本、复杂度、适用场景等）

**用户：**「分析这段代码并给出改进后的实现」

1. `delegate_subagent(task="审查以下代码并列出问题…", role="reviewer", context="<代码摘要>")`
2. `delegate_subagent(task="根据审查意见重写实现…", role="coder", context="<审查要点>")`
3. 主 Agent 呈现最终代码与变更说明

## 注意

- `context` 只写子任务必需信息，勿粘贴整段聊天记录
- 子 Agent 不能再调用 `delegate_subagent`（深度限制见 AGENT_MAX_SUBAGENT_DEPTH）
- 委派耗时受 SUBAGENT_TIMEOUT_SEC 限制
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

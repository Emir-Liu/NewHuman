# NewHuman — Cursor Agent 开发循环指南

> **完整文档：** [docs/2_开发文档/4_Agent自循环开发.md](docs/2_开发文档/4_Agent自循环开发.md)  
> **启动与测试：** [docs/2_开发文档/2_本地开发与脚本.md](docs/2_开发文档/2_本地开发与脚本.md) · [3_验收测试与里程碑.md](docs/2_开发文档/3_验收测试与里程碑.md)

本文档指导 AI Agent **按里程碑自开发、自测、自修**，直至 MVP 验收通过。

## 前置条件

1. 配置 `code/app/.env`（从 `.env.demo` 复制，填入 LLM / Embedding）
2. 创建 conda 环境：`.\scripts\setup_conda.ps1`
3. **Windows：在 PowerShell 中运行脚本，不要用 CMD**（见 [§1.1](docs/2_开发文档/2_本地开发与脚本.md#11-windows请使用-powershell不要用-cmd)）
4. （可选）激活：`conda activate newhuman`

## 标准循环（每个里程碑重复）

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ 读里程碑目标 │ ──► │ 读设计 §6.4  │ ──► │ 实现代码     │ ──► │ 跑里程碑测试 │
└─────────────┘     └──────────────┘     └─────────────┘     └──────┬───────┘
       ▲                                                            │
       │                     ┌──────────────┐                      │
       └──────────────────── │ 更新检查清单  │ ◄── 失败 ── 修 bug ─┘
                             └──────────────┘         通过
```

### Step 1 — 确认当前里程碑

```powershell
python scripts/check_milestone.py
```

输出中第一个 ⬜ 即为当前目标（通常从 **M1** 开始）。

### Step 2 — 阅读设计与需求

| 里程碑 | 需求文档 | 设计文档 | 主要落点 |
|--------|----------|----------|----------|
| M1 | REQ-004,005,010,020 | §3.2, §4, §6.4 | `build.py`, `nodes/`, `edges/`, `file_tool.py` |
| M2 | REQ-007,008 | §6.3, §6.4 | `workspace/manager.py`, `context_assembler.py` |
| M3 | REQ-009,015,019,023,024 | §8.4 | `tool_registry.py`, `web_tool.py`, `exec` |
| M4 | REQ-012~014,002 | §3.6 | `memory_tool.py`, stop 联调 |
| M5 | 全部 TC | §8.8 | 收尾、启用跳过的测试 |

### Step 3 — 启动服务（终端 1）

```powershell
.\scripts\start_server.ps1
```

### Step 4 — 运行测试（终端 2）

```powershell
# 仅 smoke（无需 LLM）
.\scripts\run_tests.ps1 -SmokeOnly

# 当前里程碑（例：M1）
.\scripts\run_tests.ps1 -Milestone M1
```

### Step 5 — 修复直到通过

- 测试失败 → 读 traceback → 改代码 → 重跑 **同一里程碑** 测试
- 不要跳过失败用例（`pytest.skip` 仅用于尚未实现的后续里程碑依赖）
- M1 通过后再进入 M2，依此类推

### Step 6 — 更新检查清单

MVP 全部通过后，在设计文档 §8.8 勾选对应项。

## Agent 单次会话推荐 Prompt

```
当前里程碑: M1
请按 docs/1_设计文档/MVP设计文档_v1.0.md §6.4 实现 ReAct 图与 read_file。
完成后运行 .\scripts\run_tests.ps1 -Milestone M1，失败则修复直到通过。
不要修改 docs 除非接口契约变化。
```

## 命令速查

| 命令 | 说明 |
|------|------|
| `.\scripts\setup_workspace.ps1` | 初始化 workspace 模板 |
| `.\scripts\start_server.ps1` | 启动 FastAPI |
| `.\scripts\run_tests.ps1 -SmokeOnly` | 健康检查 |
| `.\scripts\run_tests.ps1 -Milestone M1` | M1 验收 |
| `python scripts/check_milestone.py` | 里程碑门禁 |
| `cd code/app && python -m func.graph.run` | 终端调试 Agent |

## 约束（Agent 必须遵守）

1. **范围**：仅实现 MVP 需求文档 In-Scope 功能
2. **工具策略**：遵循 `config/tools_policy.yaml` allow/deny
3. **exec**：禁止 curl/wget；cwd 限定 workspace
4. **web_fetch**：SSRF 防护（block private IPs）
5. **不写文件工具**：MVP 禁用 write_file / edit_file / apply_patch
6. **最小 diff**：只改实现当前里程碑所需的文件

## 已知限制

- 集成测试依赖真实 LLM，无 mock
- TC-03 / TC-09 / TC-10 等需在对应工具就绪后移除 `pytest.skip`
- Nacos 注册失败不影响本地开发（lifespan 已容错）

---

*与 [MVP需求文档](docs/0_需求文档/MVP需求文档_v1.0.md) §8 里程碑、[MVP设计文档](docs/1_设计文档/MVP设计文档_v1.0.md) §6 代码结构对齐。*

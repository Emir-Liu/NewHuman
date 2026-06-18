# NewHuman

类 OpenClaw 的个人 AI 助手 MVP（Web API + LangGraph ReAct Agent）。

## 快速开始（Conda）

> **Windows 用户：** 请在 **PowerShell** 中执行下列命令，不要使用 CMD。详见 [本地开发与脚本 §1.1](docs/2_开发文档/2_本地开发与脚本.md#11-windows请使用-powershell不要用-cmd)。

```powershell
cd E:\personal_project\NewHuman

# 1. 创建 conda 环境（仅需一次）
.\scripts\setup_conda.ps1

# 2. 配置 LLM
copy code\app\.env.demo code\app\.env
# 编辑 code\app\.env

# 3. 初始化 workspace
.\scripts\setup_workspace.ps1

# 4a. 终端直接对话（推荐调试）
.\scripts\run_agent.ps1

# 4b. 浏览器聊天 / API
.\scripts\start_server.ps1
# http://127.0.0.1:8000/chat

# 5. 测试
.\scripts\run_tests.ps1 -SmokeOnly
```

**手动激活环境（可选）：**

```powershell
conda activate newhuman
# 或
.\scripts\activate.ps1
```

环境名默认为 `newhuman`，可通过环境变量 `NEWHUMAN_CONDA_ENV` 覆盖。

## 文档

| 文档 | 路径 |
|------|------|
| 需求（PRD） | [docs/0_需求文档/MVP需求文档_v1.0.md](docs/0_需求文档/MVP需求文档_v1.0.md) |
| 设计（SDD） | [docs/1_设计文档/MVP设计文档_v1.0.md](docs/1_设计文档/MVP设计文档_v1.0.md) |
| 本地开发与脚本 | [docs/2_开发文档/2_本地开发与脚本.md](docs/2_开发文档/2_本地开发与脚本.md) |
| 验收测试与里程碑 | [docs/2_开发文档/3_验收测试与里程碑.md](docs/2_开发文档/3_验收测试与里程碑.md) |
| Agent 自循环 | [docs/2_开发文档/4_Agent自循环开发.md](docs/2_开发文档/4_Agent自循环开发.md) |
| Cursor 快捷指南 | [AGENTS.md](AGENTS.md) |

## 里程碑

```powershell
conda activate newhuman
python scripts/check_milestone.py
```

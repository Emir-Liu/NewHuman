# 开发文档

本目录存放 NewHuman MVP 的**开发、运行、测试与 Agent 自循环**说明。

## 文档索引

| 文档 | 说明 |
|------|------|
| [1_开发规范.md](./1_开发规范.md) | Git、Commit、接口与日志规范 |
| [2_本地开发与脚本.md](./2_本地开发与脚本.md) | Conda 环境、启动脚本、workspace |
| [3_验收测试与里程碑.md](./3_验收测试与里程碑.md) | pytest 套件、TC 对照、里程碑门禁 |
| [4_Agent自循环开发.md](./4_Agent自循环开发.md) | Cursor Agent 按 M1→M5 自开发流程 |

## 关联文档

- [MVP 需求文档](../0_需求文档/MVP需求文档_v1.0.md) — REQ 与 TC 验收标准
- [MVP 设计文档](../1_设计文档/MVP设计文档_v1.0.md) — 架构与代码落点（§6）

## 快速命令

> **Windows：** 在 **PowerShell** 中运行 `.ps1` 脚本，不要用 CMD。

```powershell
.\scripts\setup_conda.ps1
.\scripts\setup_workspace.ps1
.\scripts\start_server.ps1
.\scripts\run_tests.ps1 -SmokeOnly
python scripts\check_milestone.py
```

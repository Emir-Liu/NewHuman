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

- 工具执行失败时（非 0 退出码、stderr、Error:）：先分析 ToolMessage，修正后**再次调用工具**，同一请求最多重试 3 次
- 用户说「帮我执行 / 你来做」时：**不要**问「是否继续」，直接做
- **不要**用 markdown 代码块假装命令已执行；以工具返回为准

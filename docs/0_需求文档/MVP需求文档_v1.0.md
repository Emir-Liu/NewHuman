# NewHuman — 类 OpenClaw 个人 AI 助手 MVP 需求文档

| 属性 | 内容 |
|------|------|
| 文档版本 | v1.2 |
| 创建日期 | 2026-06-16 |
| 文档类型 | 产品需求（PRD） |
| 项目代号 | NewHuman |
| 团队规模 | 1 人（全栈） |
| 关联设计 | [MVP设计文档 v1.0](../1_设计文档/MVP设计文档_v1.0.md) |
| 状态 | 草案 |

---

## 1. 背景与目标

### 1.1 背景

OpenClaw 展示了「本地优先 + Agent 运行时 + Workspace 驱动 + 工具调用」的个人 AI 助手架构。NewHuman 已有 FastAPI 对话 API、LangGraph 骨架、知识库与多 LLM Provider。

本 MVP 在 **仅 Web API** 前提下，交付可演示的个人 AI 助手后端，架构对齐 OpenClaw 能力子集，基于现有 Python 栈自建。

### 1.2 产品愿景

> 一个可通过 Web API 访问的、本地部署的个人 AI 助手：有记忆、会用工具、人格可配置，且数据留在自己的服务器上。

### 1.3 MVP 成功标准

| # | 标准 | 关联需求 | 验收 |
|---|------|----------|------|
| 1 | HTTP API 流式/阻塞对话可用 | REQ-001 ~ REQ-003 | TC-01 |
| 2 | Agent 自主调用读文件、记忆、知识库、命令行、网络工具 | REQ-010 ~ REQ-015, REQ-023, REQ-024 | TC-02~03, TC-08~09 |
| 3 | 多轮对话上下文连续 | REQ-006, REQ-021 | TC-04 |
| 4 | Bootstrap 文件影响 Agent 行为 | REQ-007, REQ-008 | TC-05 |
| 5 | 知识库 RAG 可被 Agent 调用 | REQ-015, REQ-019 | TC-03 |
| 6 | 单人 4~6 周可完成并演示 | 里程碑 M1~M5 | 全部 TC 通过 |

---

## 2. 产品定位

| 维度 | 说明 |
|------|------|
| 目标用户 | 开发者 / 个人用户（自用） |
| 部署方式 | 本地或私有 VPS |
| 入口 | **仅 Web API**（HTTP + SSE） |
| 参考 | [OpenClaw](https://docs.openclaw.ai/) Web-only 精简版 |

---

## 3. 范围定义

### 3.1 In Scope（MVP）

| 模块 | 需求概要 |
|------|----------|
| Gateway | 对话 API、停止生成、会话变量 |
| Agent Runtime | LangGraph ReAct、Tool Calling、流式输出 |
| Workspace | Bootstrap Markdown、Skills 目录 |
| Tools | 9 项基础工具：fs 只读、memory、KB、exec、网络（web_search / web_fetch） |
| Memory | 短期 checkpoint + 长期 MEMORY.md |
| Knowledge Base | 现有 KB API + Agent 检索工具 |
| Model | OpenAI / Ollama / vLLM，需 Tool Calling |

### 3.2 Out of Scope

| 项 | 说明 |
|----|------|
| Telegram / Slack 等渠道 | 已明确不做 |
| Control UI | MVP 用 Postman |
| Multi-agent / Cron / MCP / Browser / 语音 | P1 及以后 |
| 多用户租户隔离 | MVP 单用户 |

---

## 4. 需求列表（总表）

> 实现细节见 [MVP设计文档](../1_设计文档/MVP设计文档_v1.0.md)。工具对标见设计文档第 7 章。

### 4.1 功能需求

| ID | 模块 | 需求描述 | 优先级 | 验收 |
|----|------|----------|--------|------|
| **REQ-001** | Gateway | 提供 `POST /chat-messages`，支持 `streaming` 与 `blocking` 两种响应模式 | P0 | TC-01 |
| **REQ-002** | Gateway | 提供停止生成功能（`POST .../stop`），可中断进行中的流式任务 | P1 | TC-06 |
| **REQ-003** | Gateway | 提供 `GET /conversations/{id}/variables`，可查看会话 state 变量（调试） | P1 | — |
| **REQ-004** | Agent | 实现 LangGraph ReAct 循环：LLM 推理 ↔ 工具执行，直至无 tool_calls | P0 | TC-02 |
| **REQ-005** | Agent | LLM 须绑定工具 schema，模型可返回 function calling / tool_calls | P0 | TC-02 |
| **REQ-006** | Agent | 同一会话多轮对话须保留上下文（messages 历史） | P0 | TC-04 |
| **REQ-007** | Workspace | 提供单工作区 `workspace/default/`，含 Bootstrap 模板文件 | P0 | TC-05 |
| **REQ-008** | Workspace | 新 session 首轮须将 Bootstrap（AGENTS/SOUL/USER/TOOLS.md）注入 system prompt | P0 | TC-05 |
| **REQ-009** | Skills | 支持 `skills/*/SKILL.md`；prompt 仅注入 skill 索引，全文按需读取 | P1 | TC-03 |
| **REQ-010** | Tools | 提供 `read_file`：仅可读 workspace 内文件 | P0 | TC-02 |
| **REQ-011** | Tools | 提供 `list_dir`：仅可列 workspace 内目录 | P0 | — |
| **REQ-012** | Tools | 提供 `memory_search`：语义检索长期记忆 | P0 | TC-07 |
| **REQ-013** | Tools | 提供 `memory_get`：按路径读取记忆片段 | P0 | TC-07 |
| **REQ-014** | Tools | 提供 `memory_append`：追加内容到 MEMORY.md 或 memory/ | P1 | TC-07 |
| **REQ-015** | Tools | 提供 `search_knowledge`：检索知识库向量库 | P0 | TC-03 |
| **REQ-016** | Tools | MVP **禁止** Agent 调用写文件类工具；`exec` 须受 REQ-023 约束；网络须走 REQ-024 专用工具 | P0 | 安全审查 |
| **REQ-023** | Tools | 提供 `exec`：在 **workspace 目录** 内执行 shell 命令，返回 stdout/stderr 与退出码 | P0 | TC-08 |
| **REQ-024** | Tools | 提供网络访问工具：`web_search`（搜索）、`web_fetch`（抓取 URL 正文） | P0 | TC-09, TC-10 |
| **REQ-017** | Memory | 短期记忆：LangGraph checkpoint 按 `conversation_id` 持久化 messages | P0 | TC-04 |
| **REQ-018** | Memory | 长期记忆：MEMORY.md + memory/ 日志；不每轮全量注入 prompt | P1 | TC-07 |
| **REQ-019** | KB | 复用现有知识库 HTTP API；文档上传与 Agent 检索分离（写走 API，读走 Tool） | P0 | TC-03 |
| **REQ-020** | Model | 支持可配置 LLM Provider，**必须**支持 Tool Calling 与 Streaming | P0 | TC-01 |
| **REQ-021** | Session | `conversation_id` 映射为 LangGraph `thread_id`，会话元数据存 DB | P0 | TC-04 |
| **REQ-022** | Workspace | 服务启动或 setup 时可初始化 workspace 默认模板（可选 API） | P2 | — |

### 4.2 非功能需求

| ID | 类别 | 需求描述 | 优先级 |
|----|------|----------|--------|
| **REQ-NFR-001** | 性能 | 首 token 响应 < 3s（依赖 LLM）；单实例支持 1 并发演示 | P1 |
| **REQ-NFR-002** | 可用性 | 本地 `uvicorn` 一键启动，依赖 `.env` 配置 | P0 |
| **REQ-NFR-003** | 安全 | `read_file` / `list_dir` 限制在 workspace 内 | P0 |
| **REQ-NFR-007** | 安全 | `exec` 须限制工作目录为 workspace、命令超时、可选白名单；禁止任意路径与破坏性命令 | P0 |
| **REQ-NFR-004** | 安全 | API Key 鉴权 | P2（P1 可选） |
| **REQ-NFR-005** | 可观测 | 关键路径 Loguru 日志；可选 LangSmith 追踪 | P1 |
| **REQ-NFR-006** | 可维护 | 修改 Bootstrap Markdown 即可调整 Agent 行为，无需改代码 | P0 |
| **REQ-NFR-008** | 安全 | `web_search` / `web_fetch` 须限制超时、响应大小；`web_fetch` 仅允许 http/https，可选域名白名单 | P0 |

### 4.3 环境与依赖需求

| ID | 类别 | 需求描述 | 必须 |
|----|------|----------|------|
| **REQ-ENV-001** | 运行时 | Python 3.11+、FastAPI、LangGraph | 是 |
| **REQ-ENV-002** | 外部服务 | LLM API（Tool Calling + Streaming） | 是 |
| **REQ-ENV-003** | 外部服务 | Embedding API（知识库向量化） | 是 |
| **REQ-ENV-004** | 存储 | 向量库 Chroma 或 Milvus | 是 |
| **REQ-ENV-005** | 存储 | SQLite（会话/KB 元数据） | 是 |
| **REQ-ENV-006** | 联调 | Postman 或等效工具可调用 API | 是 |
| **REQ-ENV-007** | 外部服务 | 网络搜索 API（若 `web_search` 使用第三方搜索服务）或 LLM 内置搜索能力 | 视实现 |

### 4.4 Agent 工具需求（MVP 必须）

对标 OpenClaw `group:fs`（只读）+ `group:memory` + `group:runtime`（受控 exec）+ `group:web` + 项目 KB：

| ID | 工具名 | 需求说明 | 对标 |
|----|--------|----------|------|
| REQ-TOOL-01 | `read_file` | 读 workspace 文件 | OC `read` / Codex `read_file` |
| REQ-TOOL-02 | `list_dir` | 列 workspace 目录 | Codex `list_dir` |
| REQ-TOOL-03 | `memory_search` | 语义检索记忆 | OC `memory_search` |
| REQ-TOOL-04 | `memory_get` | 读取记忆片段 | OC `memory_get` |
| REQ-TOOL-05 | `memory_append` | 追加长期记忆 | OC 记忆写入约定 |
| REQ-TOOL-06 | `search_knowledge` | 知识库 RAG 检索 | 项目特有 |
| REQ-TOOL-07 | `exec` | 在 workspace 内执行 shell 命令 | OC `exec` / Codex `shell` |
| REQ-TOOL-08 | `web_search` | 联网搜索，返回摘要与链接 | OC `web_search` / Codex `web_search` |
| REQ-TOOL-09 | `web_fetch` | 抓取指定 URL 可读正文（Markdown/文本） | OC `web_fetch` |

**MVP 明确不提供：** `write_file`、`edit_file`、`apply_patch`（P1 再评估）。

#### 4.4.1 `exec` 命令行执行需求（REQ-023 / REQ-TOOL-07）

| 子项 | 需求描述 | 优先级 |
|------|----------|--------|
| REQ-023-01 | Agent 可通过 `exec` 工具执行 shell 命令，并获取 stdout、stderr、exit_code | P0 |
| REQ-023-02 | 命令默认在 `workspace/default/` 下执行（`cwd` 固定或可配置为 workspace） | P0 |
| REQ-023-03 | 单次命令执行超时（建议默认 30s，可配置） | P0 |
| REQ-023-04 | 支持命令白名单或 deny 列表（如禁止 `rm -rf /`、禁止访问 workspace 外路径） | P0 |
| REQ-023-05 | 命令及输出须写入日志，便于审计与调试 | P1 |
| REQ-023-06 | `exec` **不得**用于替代网络访问；curl/wget 等须 deny，联网统一走 `web_search` / `web_fetch` | P0 |

**典型场景：** 用户问「列出 workspace 下有哪些文件」→ Agent 调用 `exec` 执行 `dir`/`ls`；或「当前 Python 版本是多少」→ `python --version`。

#### 4.4.2 网络访问工具需求（REQ-024 / REQ-TOOL-08 ~ 09）

| 子项 | 需求描述 | 优先级 |
|------|----------|--------|
| REQ-024-01 | 提供 `web_search`：根据 query 返回搜索结果列表（标题、URL、摘要） | P0 |
| REQ-024-02 | 提供 `web_fetch`：抓取单个 http/https URL，返回可读正文（截断过长内容） | P0 |
| REQ-024-03 | 单次请求超时（建议默认 15s，可配置） | P0 |
| REQ-024-04 | 响应体大小上限（建议默认 512KB，可配置） | P0 |
| REQ-024-05 | `web_fetch` 禁止访问内网/localhost/私有 IP（SSRF 防护） | P0 |
| REQ-024-06 | 可选域名白名单或 deny 列表（配置化） | P1 |
| REQ-024-07 | 搜索与抓取请求须写日志（URL、状态码、耗时） | P1 |

**典型场景：** 用户问「今天 OpenAI 有什么新闻」→ `web_search`；「读取 https://example.com/docs 并总结」→ `web_fetch`。

---

## 5. 用户故事

| ID | 故事 | 优先级 | 需求 |
|----|------|--------|------|
| US-01 | 作为开发者，我希望通过 API 流式收到回复，以便集成 Web 前端 | P0 | REQ-001, REQ-020 |
| US-02 | 作为开发者，我希望 Agent 能检索知识库回答文档问题 | P0 | REQ-015, REQ-019 |
| US-03 | 作为开发者，我希望编辑 Markdown 配置人格，无需改代码 | P0 | REQ-007, REQ-008 |
| US-04 | 作为开发者，我希望多轮对话有上下文 | P0 | REQ-006, REQ-021 |
| US-05 | 作为开发者，我希望停止正在生成的回复 | P1 | REQ-002 |
| US-06 | 作为开发者，我希望 Agent 能读 workspace 与检索记忆 | P0 | REQ-010 ~ REQ-013 |
| US-07 | 作为开发者，我希望查看会话变量调试 Agent | P1 | REQ-003 |
| US-08 | 作为开发者，我希望跨会话记住偏好 | P1 | REQ-014, REQ-018 |
| US-09 | 作为开发者，我希望 Agent 能在 workspace 内执行 shell 命令，以便完成查版本、列目录等操作 | P0 | REQ-023, REQ-TOOL-07 |
| US-10 | 作为开发者，我希望 Agent 能搜索互联网并抓取网页内容，以便回答实时信息 | P0 | REQ-024, REQ-TOOL-08~09 |

---

## 6. 典型场景

**场景 A：知识问答** — 上传 PDF → POST 对话 → Agent 调用 `search_knowledge` → 流式回答（REQ-015, REQ-019）

**场景 B：多轮对话** — 同 `conversation_id` 追问，引用上文（REQ-006, REQ-017）

**场景 C：人格配置** — 编辑 `SOUL.md` → 新 session 语气变化（REQ-008）

**场景 D：命令行执行** — 用户问「在 workspace 里执行 dir / ls 并告诉我结果」→ Agent 调用 `exec` → 返回命令输出（REQ-023）

**场景 E：网络访问** — 用户问「搜索 LangGraph 最新文档」→ `web_search`；或「总结某 URL 内容」→ `web_fetch`（REQ-024）

---

## 7. 验收测试用例

| TC-ID | 前置条件 | 步骤 | 期望 | 需求 |
|-------|----------|------|------|------|
| TC-01 | 服务启动 | POST streaming「你好」 | 收到 SSE message | REQ-001 |
| TC-02 | workspace 有 SOUL.md | 「读取 SOUL.md 并总结」 | 调用 `read_file`，内容正确 | REQ-010 |
| TC-03 | KB 有文档 | 「根据文档，XX 是什么」 | 答案引用检索内容 | REQ-015 |
| TC-04 | 同 conversation_id | 两轮追问 | 第二轮理解指代 | REQ-006 |
| TC-05 | 修改 SOUL 为英文 | 新 session 发中文 | 英文回复 | REQ-008 |
| TC-06 | 长文本生成中 | POST stop | 生成终止 | REQ-002 |
| TC-07 | — | 「记住我叫小明」→ 新 session「我叫什么」 | 从 MEMORY 回答 | REQ-014, REQ-018 |
| TC-08 | workspace 可写 | 「执行 python --version 并告诉我结果」 | 调用 `exec`，返回到版本信息 | REQ-023 |
| TC-09 | 网络可用 | 「搜索 Python 3.12 新特性」 | 调用 `web_search`，返回含链接的摘要 | REQ-024 |
| TC-10 | 网络可用 | 「抓取 https://example.com 并一句话总结」 | 调用 `web_fetch`，返回页面摘要 | REQ-024 |

---

## 8. 里程碑（产品交付）

| 阶段 | 周期 | 交付物 | 验收需求 |
|------|------|--------|----------|
| M1 Agent 核心 | 第 1 周 | ReAct 图 + read_file + 流式 | REQ-004, REQ-005, REQ-010, REQ-020 |
| M2 Workspace | 第 2 周 | 模板 + Context 注入 | REQ-007, REQ-008 |
| M3 Tools 与 KB | 第 3 周 | search_knowledge + Skills + exec + web 工具 | REQ-009, REQ-015, REQ-019, REQ-023, REQ-024 |
| M4 Memory | 第 4 周 | memory 工具 + stop | REQ-012 ~ REQ-014, REQ-002 |
| M5 验收 | 第 5 周 | Postman 集合 + 文档 | 全部 TC |

---

## 9. 风险与约束

| 风险 | 影响 | 缓解 |
|------|------|------|
| LLM 不支持 Tool Calling | REQ-004/005 无法满足 | 选用 OpenAI 兼容模型 |
| 一人开发范围蔓延 | 延期 | 严格遵循 Out of Scope |
| exec 命令越权或破坏性操作 | 系统安全风险 | REQ-NFR-007 |
| web_fetch SSRF / 恶意 URL | 内网泄露或滥用 | REQ-NFR-008、REQ-024-05 |
| checkpoint 内存丢失 | 重启丢会话 | MVP 可接受；P1 Postgres |

---

## 10. 术语表

| 术语 | 说明 |
|------|------|
| Gateway | Web API 入口（FastAPI） |
| Agent Runtime | LangGraph LLM+Tool 循环 |
| Workspace | Agent 工作目录与 Bootstrap 文件 |
| Bootstrap | 注入 system prompt 的 Markdown |
| Skill | SKILL.md 任务指令包 |
| ReAct | 推理与工具交替执行 |

---

## 11. 文档修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-16 | 从 MVP需求设计文档 拆分；提取 REQ 需求列表 |
| v1.1 | 2026-06-16 | 新增 REQ-023 / REQ-TOOL-07：workspace 内受控命令行执行（exec） |
| v1.2 | 2026-06-16 | 新增 REQ-024 / REQ-TOOL-08~09：网络访问工具 web_search、web_fetch |

---

*需求变更须更新本文档 REQ 列表及版本号，并同步 [设计文档](../1_设计文档/MVP设计文档_v1.0.md) 追溯矩阵。*

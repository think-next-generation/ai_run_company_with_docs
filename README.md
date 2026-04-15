# ai_run_company_with_docs

> 基于文件范围驱动的人工智能运营系统 - 多 Agent 并行协作架构

## 概述

ai_run_company_with_docs 是一个企业级 AI 运营系统，通过文件范围边界实现多 Agent 并行协作。每个子系统（财务、法务、开发等）在独立的工作区中运行，通过 inbox/outbox 文件消息系统进行通信。

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI 运营公司架构                                  │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Orchestrator（总调度）                        │   │
│  │  - 监控系统状态                                        │   │
│  │  - 协调各子系统                                      │   │
│  │  - 人类交互入口                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐          │
│         ▼                    ▼                    ▼          │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │ 财务子系统  │     │ 法务子系统  │     │ 开发子系统  │       │
│  │             │     │             │     │             │       │
│  │ 文件边界    │     │ 文件边界    │     │ 文件边界    │       │
│  │ inbox/outbox│     │ inbox/outbox│     │ inbox/outbox│       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

## 核心特性

- **文件范围驱动**：每个 Agent 只能访问指定目录
- ** inbox/outbox 通信**：通过文件消息系统跨 Agent 通信
- **多工作区并行**：使用 cmux 终端实现多 Agent 并行
- **知识图谱**：整合 LLM Wiki 实现知识管理

## 项目结构

```
ai_run_company_with_docs/
├── .claude/                 # Claude Code 配置
│   └── skills/              # 本地 Skills
├── company-ops/            # Orchestrator（总调度）
│   ├── CLAUDE.md           # Agent 运行规范
│   ├── inbox/              # 接收消息
│   ├── outbox/             # 发送消息
│   ├── orchestrator/       # 监控脚本
│   ├── scripts/            # 工具脚本
│   └── shared/            # 共享工具
├── subsystems/             # 子系统目录
│   ├── _registry.json     # 子系统注册表
│   ├── 财务/             # 财务子系统
│   ├── 法务/             # 法务子系统
│   ├── develop/          # 开发子系统
│   ├── research/         # 研发子系统
│   └── <自定义>/        # 其他子系统
├── docs/                  # 文档
│   ├── superpowers/     # 内部规范和计划
│   └── architecture/    # 架构文档
├── tool-projects/         # 工具项目
│   └── task-system/      # 任务系统
└── chat/                 # 对话存档
```

## 快速开始

### 1. 初始化环境

```bash
cd company-ops
!cops:init
```

### 2. 启动 Orchestrator

```bash
!cops:orchestrator
```

### 3. 启动子系统

```bash
# 单个启动
!cops:start-subsystem 财务

# 或启动所有
!cops:startall
```

### 4. 查看状态

```bash
!cops:status
```

## 子系统

### 已注册的子系统

| 子系统 | 说明 | 类型 |
|--------|------|------|
| 财务 | 财务管理 | function |
| 法务 | 法律合规 | function |
| develop | 研发部门 | function |
| research | 研发部门 | function |

### 创建新子系统

```bash
!cops:new-subsystem <名称> --type=function
```

### 子系统文件结构

每个子系统包含：

```
subsystems/<name>/
├── CLAUDE.md             # Agent 运行规范
├── SPEC.md               # 规范文档
├── CONTRACT.yaml        # 交互契约
├── CAPABILITIES.yaml     # 能力定义
├── local-graph.json    # 本地知识图谱
├── inbox/              # 接收消息
├── outbox/             # 发送消息
├── state/              # 状态跟踪
├── data/               # 数据存储
├── src/                # 源代码
├── scripts/            # 脚本
├── libs/                # 本地库
├── docs/                # 文档
└── workspace/          # 工作空间
```

## 通信机制

### Agent 间通信

```
Orchestrator                         财务子系统
─────────────                       ──────────────
1. 写 msg_*.json 到 inbox/
2. cmux send 通知
                                   3. 读取消息
                                   4. 处理任务
                                   5. 写 reply_*.json 到 outbox/
6. 读取回复
```

### 消息格式

**请求消息** (`inbox/msg_*.json`):

```json
{
  "id": "msg_20260415_100000",
  "from": "orchestrator",
  "to": "财务",
  "type": "task",
  "content": "生成本月财务报表",
  "created_at": "2026-04-15T10:00:00Z"
}
```

**回复消息** (`outbox/reply_*.json`):

```json
{
  "id": "reply_20260415_100100",
  "in_reply_to": "msg_20260415_100000",
  "from": "财务",
  "to": "orchestrator",
  "status": "completed",
  "result": "报表已生成",
  "created_at": "2026-04-15T10:01:00Z"
}
```

## 知识管理

### Organization Graph

公司全局知识图谱：`company-ops/global-graph.json`

包含组织结构、目标、任务配置等。

### LLM Wiki

整合的 Wiki 系统：`~/wiki/`

用于知识沉淀和查询。

### 知识沉淀

```python
from company_ops.scripts.knowledge import KnowledgeAccumulator

acc = KnowledgeAccumulator()
result = acc.accumulate_task_spec(
    task_title="财务报告",
    spec_content=spec_text,
    priority="high"
)
```

## 相关工具

- [company-ops-plugin](https://github.com/think-next-generation/company-ops-plugin) - Claude Code 插件
- [cops](https://github.com/think-next-generation/cops) - 任务管理系统
- [llm-wiki](https://github.com/think-next-generation/llm-wiki) - 知识 Wiki

## 文档

- [系统工作流设计](docs/superpowers/specs/2026-04-09-system-workflow-design.md)
- [Orchestrator Agent 设计](docs/superpowers/specs/2026-04-08-orchestrator-agent-design.md)
- [cops 任务系统设计](docs/superpowers/specs/2026-04-07-cops-task-system-design.md)

## 许可证

MIT License

---

> 创建时间：2026-04-01
> 最后更新：2026-04-15
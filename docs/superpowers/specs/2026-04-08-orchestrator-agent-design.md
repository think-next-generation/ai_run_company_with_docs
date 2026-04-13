# Orchestrator Agent 设计规范

> **版本**: 2.0.0
> **创建日期**: 2026-04-08
> **更新日期**: 2026-04-09
> **状态**: Approved

---

## 1. 概述

### 1.1 目的

Orchestrator Agent 是公司运营系统的总调度，负责监控公司整体运营状态，协调各子系统 Agent 的工作，并通过 cc-connector 向人类提供决策建议。

### 1.2 运行位置

- **物理位置**: cmux 工作区
- **工作目录**: `company-ops/`
- **Agent 类型**: Claude Code

---

## 2. 身份定义

### 2.1 角色

```
名称: Orchestrator（公司总调度）
类型: 协调者
权限: 全局监控、任务分配建议、子系统协调
```

### 2.2 职责

| 职责 | 描述 | 频率 |
|------|------|------|
| 系统监控 | 检查任务系统状态 | 每 10 分钟 |
| 问题处理 | 发现未回答问题并处理 | 每 10 分钟 |
| 任务协调 | 分析任务状态，思考推进策略 | 每 10 分钟 |
| inbox 消息处理 | 检查并处理收件箱中的子系统消息 | 每 10 分钟 |
| 人类反馈 | 通过 cc-connector 推送建议 | 按需 |

---

## 3. 唤醒机制

### 3.1 CronCreate 周期轮询

使用 Claude Code 的 CronCreate 功能实现定时监控：

```
*/10 * * * * -> 执行监控循环
```

### 3.2 唤醒时的 Prompt

```
执行 Orchestrator 监控循环：

1. 检查任务系统: sqlite3 company-ops/subsystems/task-system/data/cops.db "SELECT id, title, status, priority FROM tasks ORDER BY updated_at DESC;"
2. 检查未回答问题: sqlite3 company-ops/subsystems/task-system/data/cops.db "SELECT id, question_text, urgency FROM questions WHERE answer IS NULL;"
3. 检查子系统状态: cat company-ops/subsystems/_registry.json
4. 检查 Orchestrator 收件箱: ls company-ops/inbox/ 2>/dev/null
5. 检查各子系统收件箱（了解跨 Agent 通信）:
   ls ../subsystems/财务/inbox/
   ls ../subsystems/法务/inbox/
6. 如果 inbox 中有消息，读取并处理，写回复到 outbox/，然后将原消息归档
6. 记录日志: echo "$(date -Iseconds) - 监控循环完成" >> company-ops/orchestrator/logs/monitor.log
```

### 3.3 CLAUDE.md 加载机制

Claude Code 从当前工作目录**向上**查找 CLAUDE.md 文件。子目录中的 CLAUDE.md 不会自动加载，只有在读取该子目录中的文件时才会懒加载。

Orchestrator 的 CLAUDE.md 位于 `company-ops/CLAUDE.md`，需确保工作目录为 `company-ops/` 或其父目录。

---

## 4. 监控内容

### 4.1 任务系统监控

```bash
# 任务列表
sqlite3 subsystems/task-system/data/cops.db "SELECT id, title, status, priority, assignees, blocked_by, updated_at FROM tasks ORDER BY updated_at DESC;"

# 未回答问题
sqlite3 subsystems/task-system/data/cops.db "SELECT id, task_id, question_text, urgency FROM questions WHERE answer IS NULL;"

# 最近事件
sqlite3 subsystems/task-system/data/cops.db "SELECT id, event_type, description, created_at FROM events ORDER BY created_at DESC LIMIT 10;"
```

### 4.2 子系统监控

```bash
# 查看子系统注册表
cat subsystems/_registry.json

# 检查子系统状态文件
cat subsystems/*/state/status.md
```

---

## 5. 决策逻辑

### 5.1 任务状态处理

| 任务状态 | 处理策略 |
|----------|----------|
| NEW（未分配） | 分析任务类型，建议分配给合适的子系统 |
| ASSIGNED（已分配） | 检查是否超时，必要时提醒 |
| IN_PROGRESS（进行中） | 监控进度，长期无更新则关注 |
| BLOCKED（阻塞） | 分析阻塞原因，协调解决 |
| WAITING（等待中） | 检查等待条件是否已满足 |
| REVIEW（待审核） | 提醒人类审核 |

### 5.2 问题处理

| 问题类型 | 处理策略 |
|----------|----------|
| 紧急问题 | 立即通过 cc-connector 推送给人类 |
| 普通问题 | 尝试回答或分配给合适的 Agent |
| 跨子系统问题 | 协调相关子系统协作解决 |

### 5.3 子系统异常处理

| 异常类型 | 处理策略 |
|----------|----------|
| Agent 停止 | 记录日志，通知人类 |
| 长期无活动 | 检查状态，考虑是否需要干预 |
| 错误状态 | 分析错误，提供修复建议 |

---

## 6. Agent 间通信协议

### 6.1 通信架构

三层机制配合实现 Agent 间通信：

1. **cmux send** — 即时通知：在 cmux 终端内通过 `cmux send --surface <id>` 向目标 tab 注入文本，立即唤醒对方 Agent
2. **inbox/outbox 文件系统** — 结构化消息：通过各角色独立目录传递完整的 JSON 消息和回复
3. **CronCreate 轮询** — 兜底机制：每 10 分钟检查 inbox 和 outbox，处理 cmux send 遗漏或未及时响应的消息

**通信方案选型**：

| 方案 | 结论 | 原因 |
|------|------|------|
| cc-connect relay | ❌ 不可行 | 每个 project 必须绑定独立的飞书 bot |
| cmux send（后台进程） | ❌ 不可行 | 无法从后台进程调用，仅在 cmux 终端内可用 |
| cmux send（终端内） | ✅ 配合使用 | Claude Code 会话内可通过 Bash 调用 |
| inbox/outbox | ✅ 核心机制 | 结构化消息传递 |
| CronCreate 轮询 | ✅ 兜底机制 | 简单可靠，内建于 Claude Code |

### 6.2 目录结构

```
company-ops/                    ← Orchestrator 工作目录
├── inbox/                      ← 发给 Orchestrator 的消息
├── outbox/                     ← Orchestrator 的回复
../subsystems/                  ← 子系统（父目录）
├── 财务/
│   ├── inbox/                 ← 发给财务的消息
│   └── outbox/                ← 财务的回复
├── 法务/
│   ├── inbox/                 ← 发给法务的消息
│   └── outbox/                ← 法务的回复
└── _registry.json
```

### 6.3 消息文件命名

格式: `{type}_{YYYYMMDD_HHMMSS}.json`

```
msg_20260409_103302.json       ← 消息
reply_20260409_103345.json     ← 回复
```

### 6.4 消息格式

**发送消息:**
```json
{
  "id": "msg_20260409_103302",
  "from": "orchestrator",
  "to": "finance",
  "type": "question|task_assignment|notification",
  "content": "消息内容",
  "created_at": "2026-04-09T10:33:02+08:00"
}
```

**回复消息:**
```json
{
  "id": "reply_20260409_103345",
  "in_reply_to": "msg_20260409_103302",
  "from": "finance",
  "to": "orchestrator",
  "type": "answer|status_update|ack",
  "content": "回复内容",
  "created_at": "2026-04-09T10:33:45+08:00"
}
```

### 6.5 通信流程

```
发送方 (Orchestrator)                           接收方 (财务子系统)
───────────────────                            ──────────────────
1. 写 msg_*.json 到 subsystems/财务/inbox/
2. cmux send --surface <id>
   "收到新消息，请读取 inbox"
                                               3. 收到注入文本，立即响应
                                               4. 读取并处理 subsystems/财务/inbox/ 消息
                                               5. 写 reply_*.json 到 subsystems/财务/outbox/
                                               6. 将原消息归档
                                               7. cmux send 通知发送方
8. CronCreate 轮询（兜底）
   检查 subsystems/财务/outbox/ 是否有新回复
9. 读取回复内容
```

### 6.6 向人类反馈

使用 cc-connector skill：

```
使用 cc-connector skill 向人类推送消息：
- 紧急通知
- 决策建议
- 日报/周报
```

---

## 7. 文件结构

```
company-ops/
├── CLAUDE.md                    # Orchestrator 身份定义和通信协议
├── .claude/
│   └── scheduled_tasks.json     # Cron 任务配置 (durable)
├── subsystems/
│   ├── _registry.json           # 子系统注册表
│   ├── task-system/             # 任务管理子系统 (Rust + SQLite)
│   │   └── data/cops.db         # 任务数据库
│   ├── 财务/
│   │   ├── inbox/                 # 发给财务的消息
│   │   ├── outbox/                # 财务的回复
│   │   └── state/
│   └── 法务/
│       ├── inbox/                 # 发给法务的消息
│       ├── outbox/                 # 法务的回复
│       └── state/
└── orchestrator/
    ├── inbox/                     # 发给 Orchestrator 的消息
    ├── outbox/                    # Orchestrator 的回复
    ├── logs/                      # 监控日志
    └── reports/                   # 生成的报告
```

---

## 8. 成功指标

| 指标 | 目标值 |
|------|--------|
| 监控响应时间 | < 30 秒 |
| 问题发现率 | 100% |
| 通知延迟 | < 1 分钟 |
| 消息处理延迟 | < 20 分钟（受 CronCreate 间隔限制） |
| 系统可用性 | 99% |

---

## 9. 实施计划

1. 创建 `company-ops/CLAUDE.md` 文件
2. 创建 `company-ops/inbox/` 和 `company-ops/outbox/` 目录
3. 确保各子系统目录下有 inbox/outbox 目录
4. 配置 CronCreate 定时任务（10 分钟间隔）
5. 测试监控循环
5. 测试 inbox/outbox 消息通信
6. 集成 cc-connector skill

---

*文档版本: 2.0.0*
*创建日期: 2026-04-08*
*更新日期: 2026-04-09*

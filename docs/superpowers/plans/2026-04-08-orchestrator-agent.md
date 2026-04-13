# Orchestrator Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create Orchestrator Agent that monitors company operations, coordinates subsystems via inbox/outbox file messaging, and provides feedback to humans via cc-connector.

**Architecture:** Claude Code with CronCreate-based monitoring loop (10 min interval). Uses cops CLI for task system monitoring, per-subsystem inbox/outbox directories for inter-agent communication, and cc-connector skill for human notifications.

**Tech Stack:** Claude Code, CronCreate, cops CLI, cc-connector skill

---

## File Structure Overview

```
company-ops/                    ← Orchestrator 工作目录
├── CLAUDE.md                    # Orchestrator identity and instructions
├── inbox/                       # 发给 Orchestrator 的消息
├── outbox/                      # Orchestrator 的回复
├── orchestrator/
│   ├── logs/                    # Monitoring logs
│   └── reports/                 # Generated reports
../subsystems/                   ← 子系统（父目录）
├── 财务/
│   ├── inbox/                   # 发给财务的消息
│   ├── outbox/                  # 财务的回复
│   └── CLAUDE.md
├── 法务/
│   ├── inbox/                   # 发给法务的消息
│   ├── outbox/                  # 法务的回复
│   └── CLAUDE.md
└── _registry.json               # Subsystem registry
```

---

## Task 1: Create Directory Structure

**Files:**
- Create: `company-ops/inbox/.gitkeep`
- Create: `company-ops/outbox/.gitkeep`
- Create: `company-ops/orchestrator/logs/.gitkeep`
- Create: `company-ops/orchestrator/reports/.gitkeep`
- 确保 `subsystems/财务/inbox/.gitkeep` 和 `subsystems/财务/outbox/.gitkeep` 存在
- 确保 `subsystems/法务/inbox/.gitkeep` 和 `subsystems/法务/outbox/.gitkeep` 存在

- [x] **Step 1: Create orchestrator directory structure**

```bash
mkdir -p company-ops/orchestrator/logs company-ops/orchestrator/reports
touch company-ops/orchestrator/logs/.gitkeep
touch company-ops/orchestrator/reports/.gitkeep
```

- [x] **Step 2: Create shared messages directory structure**

```bash
mkdir -p company-ops/inbox company-ops/outbox
```

- [ ] **Step 3: Verify directory creation**

Run: `ls -laR company-ops/inbox/ company-ops/outbox/ company-ops/orchestrator/`
Expected: Shows complete directory structure

- [ ] **Step 4: Commit**

```bash
git add company-ops/inbox company-ops/outbox company-ops/orchestrator/
git commit -m "feat(orchestrator): create directory structure for logs, reports, and message passing"
```

---

## Task 2: Create CLAUDE.md Identity File

**Files:**
- Create: `company-ops/CLAUDE.md`

- [x] **Step 1: Create CLAUDE.md with Orchestrator identity**

CLAUDE.md 包含:
- Orchestrator 身份定义
- 10 分钟间隔监控循环
- 监控步骤（SQLite 查询替代 cops CLI）
- Agent 间通信协议（inbox/outbox，日期格式文件命名）
- 日志记录

- [ ] **Step 2: Verify file creation**

Run: `head -50 company-ops/CLAUDE.md`
Expected: Shows the Orchestrator identity content with updated monitoring commands

- [ ] **Step 3: Commit**

```bash
git add company-ops/CLAUDE.md
git commit -m "feat(orchestrator): update CLAUDE.md with inbox/outbox communication protocol"
```

---

## Task 3: Update Monitoring Script

**Files:**
- Update: `company-ops/orchestrator/monitor.sh`

- [ ] **Step 1: Update monitoring script to use SQLite queries**

```bash
#!/bin/bash
# Orchestrator Monitoring Script
# Uses SQLite directly instead of cops CLI

set -e

DB="subsystems/task-system/data/cops.db"
LOG_FILE="orchestrator/logs/monitor.log"

echo "=== Orchestrator Monitoring $(date -Iseconds) ===" >> "$LOG_FILE"

# 1. Check tasks
echo "## Tasks" >> "$LOG_FILE"
sqlite3 "$DB" "SELECT id, title, status, priority FROM tasks ORDER BY updated_at DESC;" >> "$LOG_FILE" 2>&1 || echo "DB query failed" >> "$LOG_FILE"

# 2. Check unanswered questions
echo "## Unanswered Questions" >> "$LOG_FILE"
sqlite3 "$DB" "SELECT id, question_text FROM questions WHERE answer IS NULL;" >> "$LOG_FILE" 2>&1 || echo "No unanswered questions" >> "$LOG_FILE"

# 3. Check subsystem registry
echo "## Subsystem Status" >> "$LOG_FILE"
cat subsystems/_registry.json >> "$LOG_FILE" 2>&1 || echo "No registry found" >> "$LOG_FILE"

# 4. Check inbox
echo "## Inbox" >> "$LOG_FILE"
ls inbox/ >> "$LOG_FILE" 2>&1 || echo "Inbox empty" >> "$LOG_FILE"

# 5. Check subsystem inboxes (跨 Agent 通信)
echo "## Subsystem Inboxes" >> "$LOG_FILE"
ls ../subsystems/财务/inbox/ >> "$LOG_FILE" 2>&1 || echo "财务 inbox empty" >> "$LOG_FILE"
ls ../subsystems/法务/inbox/ >> "$LOG_FILE" 2>&1 || echo "法务 inbox empty" >> "$LOG_FILE"

# 6. Check subsystem outboxes (获取回复)
echo "## Subsystem Outboxes" >> "$LOG_FILE"
ls ../subsystems/财务/outbox/ >> "$LOG_FILE" 2>&1 || echo "财务 outbox empty" >> "$LOG_FILE"
ls ../subsystems/法务/outbox/ >> "$LOG_FILE" 2>&1 || echo "法务 outbox empty" >> "$LOG_FILE"

echo "=== Monitoring Complete ===" >> "$LOG_FILE"
```

- [ ] **Step 2: Test script execution**

Run: `cd company-ops && bash orchestrator/monitor.sh && cat orchestrator/logs/monitor.log | tail -20`
Expected: Shows monitoring output with SQLite query results

- [ ] **Step 3: Commit**

```bash
git add company-ops/orchestrator/monitor.sh
git commit -m "fix(orchestrator): update monitoring script to use SQLite queries"
```

---

## Task 4: Test CronCreate Integration

- [x] **Step 1: Create cron job with 10-minute interval**

```
CronCreate with:
- cron: "*/10 * * * *"
- prompt: "执行 Orchestrator 监控循环。检查任务系统、未回答问题、子系统状态和 inbox 消息。"
- recurring: true
```

- [ ] **Step 2: Verify cron job creation**

Run: Check that the scheduled task appears in the task list
Expected: Task shows with `*/10 * * * *` cron schedule

- [ ] **Step 3: Test manual execution**

Manually trigger the monitoring prompt to verify it works correctly.

---

## Task 5: Test Inbox/Outbox Communication

- [ ] **Step 1: Create test message**

```bash
filename="msg_$(date +%Y%m%d_%H%M%S).json"
cat > "inbox/$filename" << EOF
{
  "id": "msg_$(date +%Y%m%d_%H%M%S)",
  "from": "finance",
  "to": "orchestrator",
  "type": "status_update",
  "content": "测试消息",
  "created_at": "$(date -Iseconds)"
}
EOF
```

- [ ] **Step 2: Verify message in inbox**

Run: `ls inbox/`
Expected: Shows msg_YYYYMMDD_HHMMSS.json file

- [ ] **Step 3: Process message and write reply**

Read the message, process it, write reply to outbox, move original to processed.

- [ ] **Step 4: Verify reply and archival**

Run: `ls outbox/`
Expected: Reply in outbox, original in processed

---

## Task 6: Create cc-connector Integration Guide

**Files:**
- Create: `company-ops/orchestrator/cc-connector-guide.md`

- [x] **Step 1: Create cc-connector usage guide**

- [ ] **Step 2: Commit**

```bash
git add company-ops/orchestrator/cc-connector-guide.md
git commit -m "docs(orchestrator): add cc-connector usage guide"
```

---

## Task 7: Final Verification

- [ ] **Step 1: Verify directory structure**

Run: `ls -laR company-ops/inbox/ company-ops/outbox/ company-ops/orchestrator/`
Expected: Shows complete structure

- [ ] **Step 2: Verify CLAUDE.md with updated protocol**

Run: `cat company-ops/CLAUDE.md | grep -A5 "Agent 间通信协议"`
Expected: Shows inbox/outbox protocol with date-format naming

- [ ] **Step 3: Manual integration test**

1. Start Claude Code in company-ops/
2. Verify Orchestrator identity is loaded
3. Run monitoring manually
4. Test inbox/outbox message flow

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "feat(orchestrator): complete Orchestrator Agent with inbox/outbox communication"
```

---

## Summary

This plan covers **7 tasks** implementing:

- ✅ Directory structure for logs, reports, and message passing
- ✅ CLAUDE.md with Orchestrator identity and inbox/outbox protocol
- ✅ Monitoring script using SQLite queries
- ✅ CronCreate integration with 10-minute interval
- ✅ Inbox/outbox communication testing
- ✅ cc-connector usage guide
- ✅ Final verification and testing

**Key Components:**
- `company-ops/CLAUDE.md` - Orchestrator identity + communication protocol
- `company-ops/inbox/` - Orchestrator 收件箱
- `company-ops/outbox/` - Orchestrator 发件箱
- `company-ops/orchestrator/monitor.sh` - Monitoring script
- CronCreate scheduled task - Every 10 minutes

---

*Plan version: 2.0.0*
*Created: 2026-04-08*
*Updated: 2026-04-09*

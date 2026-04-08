# Orchestrator Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create Orchestrator Agent that monitors company operations, coordinates subsystems, and provides feedback to humans via cc-connector.

**Architecture:** Claude Code configuration with Cron-based monitoring loop. Uses cops CLI for task system monitoring, file system for subsystem communication, and cc-connector skill for human notifications.

**Tech Stack:** Claude Code, CronCreate, cops CLI, cc-connector skill

---

## File Structure Overview

```
company-ops/
├── CLAUDE.md                    # Orchestrator identity and instructions
├── orchestrator/
│   ├── logs/                    # Monitoring logs
│   └── reports/                 # Generated reports
├── subsystems/
│   ├── _registry.json           # (exists) Subsystem registry
│   ├── 财务/inbox/              # (exists) Receive messages
│   └── 法务/inbox/              # (exists) Receive messages
└── .claude/
    └── scheduled_tasks.json     # Cron task configuration
```

---

## Task 1: Create Directory Structure

**Files:**
- Create: `company-ops/orchestrator/logs/.gitkeep`
- Create: `company-ops/orchestrator/reports/.gitkeep`

- [ ] **Step 1: Create orchestrator directory structure**

```bash
mkdir -p company-ops/orchestrator/logs company-ops/orchestrator/reports
touch company-ops/orchestrator/logs/.gitkeep
touch company-ops/orchestrator/reports/.gitkeep
```

- [ ] **Step 2: Verify directory creation**

Run: `ls -la company-ops/orchestrator/`
Expected: Shows logs/ and reports/ directories with .gitkeep files

- [ ] **Step 3: Commit**

```bash
git add company-ops/orchestrator/
git commit -m "feat(orchestrator): create directory structure for logs and reports"
```

---

## Task 2: Create CLAUDE.md Identity File

**Files:**
- Create: `company-ops/CLAUDE.md`

- [ ] **Step 1: Create CLAUDE.md with Orchestrator identity**

```markdown
# Orchestrator - 公司总调度

## 身份

你是 Orchestrator（公司总调度），负责监控公司整体运营状态，协调各子系统 Agent 的工作。

你的工作目录是 `company-ops/`，这是公司运营的根目录。

## 职责

1. **系统监控**: 每 5 分钟检查任务系统状态
2. **问题处理**: 发现未回答问题并协调处理
3. **任务协调**: 分析任务状态，思考推进策略
4. **子系统协调**: 通过文件系统与子系统 Agent 通信
5. **人类反馈**: 通过 cc-connector skill 推送建议给人类

## 定时监控任务

你有一个定时任务，每 5 分钟唤醒一次执行监控循环。

### 监控步骤

1. **检查系统状态**
   ```bash
   cops status
   ```

2. **检查未回答问题**
   ```bash
   cops question list --unanswered
   ```

3. **查看任务看板**
   ```bash
   cops board show
   ```

4. **检查子系统状态**
   ```bash
   cat subsystems/_registry.json
   ```

### 决策逻辑

根据检查结果：

| 发现的问题 | 处理策略 |
|-----------|---------|
| 未分配的任务 (NEW) | 分析任务类型，思考应该分配给哪个子系统 |
| 阻塞的任务 (BLOCKED) | 分析阻塞原因，协调解决 |
| 长期无更新的任务 | 检查是否需要提醒相关 Agent |
| 未回答的问题 | 判断是否需要升级给人类 |
| 子系统异常 | 考虑如何处理，必要时通知人类 |

## 通信方式

### 与子系统通信

使用文件系统的 inbox/outbox 机制：

```bash
# 发送消息到子系统（例如财务）
echo '{
  "type": "task_reminder",
  "task_id": "xxx",
  "content": "请关注此任务的进度"
}' > subsystems/财务/inbox/message_$(date +%s).json

# 读取子系统发来的消息
cat subsystems/财务/outbox/*.json 2>/dev/null || echo "无新消息"
```

### 与人类通信

使用 cc-connector skill 推送重要通知：

- 紧急问题需要人类决策
- 重要里程碑完成
- 系统异常告警
- 日报/周报摘要

## 相关文档

- 任务系统设计: `docs/superpowers/specs/2026-04-07-cops-task-system-design.md`
- Orchestrator 设计: `docs/superpowers/specs/2026-04-08-orchestrator-agent-design.md`
- 公司章程: `CHARTER.md`

## 日志记录

每次监控循环后，在 `orchestrator/logs/` 目录记录监控结果：

```bash
# 记录监控日志
echo "$(date -Iseconds) - 监控循环完成" >> orchestrator/logs/monitor.log
```
```

- [ ] **Step 2: Verify file creation**

Run: `head -50 company-ops/CLAUDE.md`
Expected: Shows the Orchestrator identity content

- [ ] **Step 3: Commit**

```bash
git add company-ops/CLAUDE.md
git commit -m "feat(orchestrator): add CLAUDE.md with Orchestrator identity"
```

---

## Task 3: Create Monitoring Script

**Files:**
- Create: `company-ops/orchestrator/monitor.sh`

- [ ] **Step 1: Create monitoring script**

```bash
#!/bin/bash
# Orchestrator Monitoring Script
# This script is called by Claude Code's CronCreate

set -e

LOG_FILE="orchestrator/logs/monitor.log"
REPORT_FILE="orchestrator/reports/latest.md"

echo "=== Orchestrator Monitoring $(date -Iseconds) ===" | tee -a "$LOG_FILE"

# 1. Check system status
echo -e "\n## System Status" | tee -a "$LOG_FILE"
cops status 2>&1 | tee -a "$LOG_FILE" || echo "Error checking status" | tee -a "$LOG_FILE"

# 2. Check unanswered questions
echo -e "\n## Unanswered Questions" | tee -a "$LOG_FILE"
cops question list --unanswered 2>&1 | tee -a "$LOG_FILE" || echo "No unanswered questions" | tee -a "$LOG_FILE"

# 3. Check task board
echo -e "\n## Task Board" | tee -a "$LOG_FILE"
cops board show 2>&1 | tee -a "$LOG_FILE" || echo "Error checking board" | tee -a "$LOG_FILE"

# 4. Check subsystem registry
echo -e "\n## Subsystem Status" | tee -a "$LOG_FILE"
cat subsystems/_registry.json 2>&1 | tee -a "$LOG_FILE" || echo "No registry found" | tee -a "$LOG_FILE"

echo -e "\n=== Monitoring Complete ===" | tee -a "$LOG_FILE"
```

- [ ] **Step 2: Make script executable**

Run: `chmod +x company-ops/orchestrator/monitor.sh`
Expected: No output (success)

- [ ] **Step 3: Test script execution**

Run: `cd company-ops && ./orchestrator/monitor.sh 2>&1 | head -30`
Expected: Script runs and shows monitoring output

- [ ] **Step 4: Commit**

```bash
git add company-ops/orchestrator/monitor.sh
git commit -m "feat(orchestrator): add monitoring script"
```

---

## Task 4: Test CronCreate Integration

**Files:**
- Test: CronCreate functionality

- [ ] **Step 1: Verify CronCreate is available**

In Claude Code session, check that CronCreate tool is available.

- [ ] **Step 2: Create test cron job**

Use CronCreate to create a test job:
```
CronCreate with:
- cron: "*/5 * * * *"
- prompt: "执行 Orchestrator 监控循环。检查系统状态、未回答问题、任务看板和子系统状态。根据发现的问题，思考如何推进任务，必要时通过 cc-connector 通知人类。"
```

- [ ] **Step 3: Verify cron job creation**

Run: Check that the scheduled task appears in the task list
Expected: Task shows with correct cron schedule

- [ ] **Step 4: Test manual execution**

Manually trigger the monitoring prompt to verify it works correctly.

- [ ] **Step 5: Commit**

```bash
git add company-ops/.claude/ 2>/dev/null || true
git commit -m "feat(orchestrator): configure CronCreate for monitoring loop" || echo "No changes to commit"
```

---

## Task 5: Create cc-connector Integration Guide

**Files:**
- Create: `company-ops/orchestrator/cc-connector-guide.md`

- [ ] **Step 1: Create cc-connector usage guide**

```markdown
# cc-connector 使用指南

## 概述

cc-connector 是用于向人类推送消息的 skill。Orchestrator 使用它在以下场景通知人类：

## 使用场景

### 1. 紧急问题通知

当发现需要人类立即决策的问题时：

```
使用 cc-connector skill 发送消息：
- 类型: 紧急
- 内容: [问题描述] + [需要决策的选项]
```

### 2. 任务里程碑

当重要任务完成或达到里程碑时：

```
使用 cc-connector skill 发送消息：
- 类型: 进度更新
- 内容: [任务名称] + [完成内容] + [下一步计划]
```

### 3. 日报/周报

定期发送运营摘要：

```
使用 cc-connector skill 发送消息：
- 类型: 报告
- 内容: [时间范围] + [完成任务] + [进行中任务] + [阻塞问题]
```

### 4. 系统异常告警

当检测到子系统异常时：

```
使用 cc-connector skill 发送消息：
- 类型: 告警
- 内容: [异常描述] + [影响范围] + [建议处理方式]
```

## 调用方式

在 Claude Code 中，使用 Skill 工具调用 cc-connector：

```
Skill tool with:
- skill: "cc-connector"
- args: "[消息内容]"
```

## 消息格式建议

```
【Orchestrator 通知】

类型: [紧急/进度/报告/告警]

摘要: [一句话概述]

详情:
- [具体内容]

建议操作:
- [ ] [操作1]
- [ ] [操作2]

---
时间: [时间戳]
```
```

- [ ] **Step 2: Commit**

```bash
git add company-ops/orchestrator/cc-connector-guide.md
git commit -m "docs(orchestrator): add cc-connector usage guide"
```

---

## Task 6: Final Verification

**Files:**
- Verify: All components working together

- [ ] **Step 1: Verify directory structure**

Run: `tree company-ops/orchestrator/ 2>/dev/null || ls -laR company-ops/orchestrator/`
Expected: Shows complete directory structure

- [ ] **Step 2: Verify CLAUDE.md exists**

Run: `test -f company-ops/CLAUDE.md && echo "CLAUDE.md exists" || echo "CLAUDE.md missing"`
Expected: "CLAUDE.md exists"

- [ ] **Step 3: Verify monitoring script**

Run: `test -x company-ops/orchestrator/monitor.sh && echo "monitor.sh is executable" || echo "monitor.sh not executable"`
Expected: "monitor.sh is executable"

- [ ] **Step 4: Manual integration test**

1. Navigate to company-ops directory
2. Start Claude Code
3. Verify Orchestrator identity is loaded
4. Run monitoring script manually
5. Verify output is correct

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat(orchestrator): complete Orchestrator Agent setup" || echo "No changes to commit"
```

---

## Summary

This plan covers **6 tasks** implementing:

- ✅ Directory structure for logs and reports
- ✅ CLAUDE.md with Orchestrator identity and instructions
- ✅ Monitoring script for system checks
- ✅ CronCreate integration for periodic monitoring
- ✅ cc-connector usage guide
- ✅ Final verification and testing

**Key Components:**
- `company-ops/CLAUDE.md` - Orchestrator identity
- `company-ops/orchestrator/monitor.sh` - Monitoring script
- `company-ops/orchestrator/logs/` - Monitoring logs
- `company-ops/orchestrator/reports/` - Generated reports
- CronCreate scheduled task - Every 5 minutes

---

*Plan version: 1.0.0*
*Created: 2026-04-08*

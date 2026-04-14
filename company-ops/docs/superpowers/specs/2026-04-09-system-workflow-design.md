# 公司运营系统完整工作流程

> **版本**: 1.0.0
> **创建日期**: 2026-04-09
> **状态**: Draft

---

## 1. 目录结构与角色

```
company-ops/                           ← Orchestrator 工作目录
├── CLAUDE.md                          ← Orchestrator 身份 + 通信协议
├── inbox/                             ← 发给 Orchestrator 的消息
├── outbox/                            ← Orchestrator 的回复
├── orchestrator/
│   ├── logs/                         ← 监控日志
│   └── reports/                      ← 报告
├── subsystems/                        ← 子系统（注意：在 company-ops 内）
│   ├── _registry.json                 ← 子系统注册表
│   ├── task-system/                  ← cops 任务系统 (Rust + SQLite)
│   ├── 财务/                          ← 财务 Agent 工作目录
│   │   ├── CLAUDE.md
│   │   ├── inbox/                    ← 发给财务的消息
│   │   └── outbox/                   ← 财务的回复
│   ├── 法务/                          ← 法务 Agent 工作目录
│   │   ├── CLAUDE.md
│   │   ├── inbox/                    ← 发给法务的消息
│   │   └── outbox/                   ← 法务的回复
│   └── {新子系统}/                    ← 后续新增子系统
└── data/cops.db                       ← 任务数据库（通过 cops 安装）
```

**角色定义**：

| 角色 | 工作目录 | 职责边界 |
|------|----------|----------|
| Orchestrator | `company-ops/` | 任务创建、分配、监控。**不直接执行任何任务** |
| 部门 Agent | `company-ops/subsystems/{部门}/` | 执行分配给自己的任务，向 Orchestrator 汇报 |

---

## 2. 启动流程

### 2.1 打开 cmux

```bash
# 打开 cmux.app
open /Applications/cmux.app
```

### 2.2 启动 Orchestrator

```bash
# Tab 0: 启动 Orchestrator
cd ~/project/company-ops
cops-init  # alias: claudeglms -p "启动 Orchestrator 监控循环，创建 10 分钟间隔的定时监控任务"
```

Orchestrator 启动后：
1. 加载 `company-ops/CLAUDE.md`
2. 自动创建 CronCreate 10 分钟定时监控
3. 接管飞书 Orchestrator Bot（Bot 1）
4. 检查 `inbox/` 是否有积压消息

### 2.3 按需启动部门 Agent

```bash
# Orchestrator 发现需要启动某部门 Agent 时
# 人类手动在 cmux 中创建新 Tab 并启动：

# Tab N: 财务 Agent
cd ~/project/subsystems/财务
claude
```

> 后续子系统都在 `subsystems/` 下新建对应项目文件夹，每个项目可启动单个 Agent 或多 tab 组成团队。

---

## 3. 通信通道

### 3.1 通道矩阵

| 通道 | 用途 | 持久化 | 实时性 |
|------|------|--------|--------|
| **cmux 终端** | 人类 ↔ Agent 直接对话 | ❌ 无记录 | 即时 |
| **Feishu Bot 1 (Orchestrator)** | 人类 ↔ Orchestrator 远程交互 | ✅ 飞书记录 | 即时 |
| **Feishu Bot 2 (可分配)** | 人类 ↔ 部门 Agent 远程交互 | ✅ 飞书记录 | 即时 |
**inbox/outbox 文件** | Agent ↔ Agent 结构化消息（每个角色独立目录） | ✅ 文件持久 | 需轮询 |
| **cmux send** | Agent → Agent 即时通知 | ❌ 无记录 | 即时 |
| **cops CLI/DB** | 任务状态管理（唯一真相源） | ✅ SQLite | 按需 |

### 3.2 飞书 Bot 分配机制

```
┌─────────────────────────────────────────────────────┐
│              cc-connect (单实例)                      │
│                                                      │
│  Bot 1: Orchestrator Bot  ← 始终由 Orchestrator 接管 │
│                                                      │
│  Bot 2: 可分配 Bot                                   │
│  ├── 默认: 未分配                                    │
│  ├── Orchestrator 可将其分配给任意部门 Agent          │
│  ├── 分配后: 人类通过该 Bot 与部门 Agent 直接对话     │
│  └── 任务结束后: Orchestrator 回收 Bot                │
└─────────────────────────────────────────────────────┘
```

**分配流程**：
1. Orchestrator 识别某 Agent 需要与人类直接交互
2. Orchestrator 通过 cc-connect 将 Bot 2 分配给该 Agent
3. 人类通过 Bot 2 与 Agent 对话
4. 对话结束（任务完成或确认），Orchestrator 回收 Bot 2

### 3.3 三者关系：cmux 交互 + inbox/outbox + cops 任务

```
           cmux 交互                    inbox/outbox
          (对话/通知)              (建议/提醒/优化)+(结构化消息)
               │                           │
               ▼                           ▼
┌──────────────────────────────────────────────────┐
│                                                  │
│              cops 任务系统                        │
│           (唯一状态真相源)                         │
│                                                  │
│  • 记录所有任务状态                                │
│  • 记录任务分配（谁在做）                          │
│  • 记录状态变更历史                                │
│  • Orchestrator 由此判断 Agent 忙碌状态            │
│                                                  │
└──────────────────────────────────────────────────┘
```

**核心原则**：
- cops DB 是**唯一的任务状态真相源**
- 所有任务推进必须在 cops 中有明确的状态变更

### 3.4 inbox/outbox 的定位

inbox/outbox **不是**任务分配的必经通道。任务分配通过 cops + cmux send 完成。

**inbox/outbox 用于**：
- **改进建议** — "某部门执行任务过程中发现可优化的地方"
- **启发性反馈** — "我们认为某些内容可以这样优化"
- **错误提醒** — "执行过程中发现潜在问题"
- **跨 Agent 知识共享** — 不构成任务但有价值的经验传递

```
任务分配流程：  Orchestrator → cops 创建/指派 → cmux send 通知 → Agent 执行
建议/反馈流程： Agent A → 子系统A的 inbox/ → cmux send 通知 → Agent B 参考其 own outbox/
```

---

## 4. 任务生命周期

### 4.1 核心规则

1. **任务创建必须人类确认** — 正常对话不等于创建任务
2. **只有 Orchestrator 可以指派任务给其他 Agent**
3. **其他 Agent 只能创建指派给自己的任务**
4. **Orchestrator 不直接解决任何任务**
5. **任务状态变更必须记录在 cops 中**

### 4.2 任务状态流转

```
                    人类确认
                       │
                       ▼
  识别需求 → 草拟任务清单 → 创建任务(NEW) → 分配(ASSIGNED)
                                                        │
                              ┌─────────────────────────┘
                              ▼
                         IN_PROGRESS ──► COMPLETED
                              │               ▲
                              ▼               │
                           BLOCKED ────────► 解除阻塞
                              │
                              ▼
                           WAITING（等待人类确认）
```

### 4.3 任务创建指令

所有 Agent 都可以使用：

```bash
/cops:create "任务标题" --priority high --description "任务描述"
```

**创建规则**：
- Orchestrator：创建后可分配给任意 Agent
- 部门 Agent：创建后只能指派给自己（assignee = self）

### 4.4 完整任务流程

#### 场景 A：人类通过 Orchestrator 创建任务

```
步骤1: 人类与 Orchestrator 对话（cmux 或 飞书 Bot 1）
       人类: "我需要一份 Q2 财务预算报告"

步骤2: Orchestrator 识别需求，草拟任务清单
       Orchestrator: "我理解您需要以下任务：
         1. [任务] 编制 Q2 财务预算报告 (财务)
         2. [任务] 审核预算报告合规性 (法务)
       确认创建？"

步骤3: 人类确认
       人类: "确认"

步骤4: Orchestrator 创建任务
       cops create "编制 Q2 财务预算报告" --priority high --assignee 财务 （返回任务ID1）
       cops create "审核预算报告合规性" --priority medium --assignee 法务 （返回任务ID2）
       → cops DB: 任务状态 NEW → ASSIGNED

步骤5: Orchestrator 通知部门 Agent
       cmux send --surface <财务tab> "收到新任务，任务ID为：ID1"

步骤6: 财务 Agent 接收
       cops task start <task-id>    # 标记任务 IN_PROGRESS
       执行任务...

步骤7: 财务 Agent 完成
       cops task complete <task-id> # 标记任务 COMPLETED
       cmux send --surface <orchestrator-tab> "任务完成: Q2 财务预算报告"

步骤8: Orchestrator 汇报
       通过飞书 Bot 1 和 outbox/（消息都是发给人类） 通知人类
```

#### 场景 B：部门 Agent 识别需求需创建任务

```
步骤1: 财务 Agent 在执行过程中发现新需求
       "发现 Q1 报表有误，需要修正"

步骤2: 财务 Agent 向 Orchestrator 申请会话权限
       写入 company-ops/inbox/msg_*.json:   ← 发送给 Orchestrator
       {
         "type": "bot_request",
         "content": "发现 Q1 报表有误，可能需要修正，需与人类沟通",
         "request_bot": true
       }
       cmux send → Orchestrator

步骤3: Orchestrator 分配 Bot 2 给财务 Agent
       通过 cc-connect 将飞书 Bot 2 切换到财务 project

步骤4: 财务 Agent 通过 Bot 2 与人类对话
       财务 Agent: "发现 Q1 报表中 X 数据有误，建议创建修正任务，是否确认？"
       人类: "确认，请创建"

步骤5: 财务 Agent 创建任务（只能指派给自己）
       /cops:create "修正 Q1 报表数据" --assignee self

步骤6: 执行、完成、回收 Bot 2
       完成后标记 COMPLETED
       cmux send → Orchestrator
       Orchestrator 回收 Bot 2
```

#### 场景 C：Agent 间直接协作

```
步骤1: 财务 Agent 执行任务中需要法务意见
       写入法务的 inbox (../subsystems/法务/inbox/msg_*.json):
       {
         "type": "question",
         "content": "Q2 预算中涉及跨境支付，请确认合规要求",
         "from": "财务"
       }
       cmux send → 法务 Agent

步骤2: 法务 Agent 判断是否需要成为任务
       - 如果是简单问答 → 直接回复，写入财务的 outbox/
       - 如果需要深入工作 → 向 Orchestrator 申请创建任务

步骤3: 财务 Agent 继续执行，读取法务的回复 (../subsystems/法务/outbox/)
```

### 4.5 inbox 消息 vs 任务的关系

```
收到 inbox 消息
       │
       ▼
  判断消息类型
       │
       ├── 简单问答/信息同步 → 直接回复（outbox），不创建任务
       │
       └── 需要执行工作 → 向 Orchestrator 申请，人类确认后创建任务
```

---

## 5. Orchestrator 监控循环（CronCreate 10 分钟）

每次触发时：

```
1. 检查 cops 任务状态
   cops board show

2. 检查 Orchestrator 收件箱 (inbox/)
   处理人类和 Agent 发来的消息

3. 检查各子系统收件箱 (了解跨 Agent 通信)
   - ls ../subsystems/财务/inbox/
   - ls ../subsystems/法务/inbox/

4. 检查各子系统发件箱 (获取回复)
   - ls ../subsystems/财务/outbox/
   - ls ../subsystems/法务/outbox/

5. 检查 Agent 忙碌状态
   基于 cops 中 IN_PROGRESS 的任务判断每个 Agent 是否忙碌

6. 检查子系统状态
   cat ../subsystems/_registry.json

7. 处理待分配任务
   对于 NEW 状态的任务 → 研究任务领域 → 分配给合适的 Agent(如果没有合适的agent，可以与人类对话商议创建新子项目)

8. 记录日志
   echo "$(date -Iseconds) - 监控循环完成" >> orchestrator/logs/monitor.log
```

---

## 6. Agent 忙碌状态判断

Orchestrator 通过 cops CLI 判断：

cops task list --assignee 财务        # 查看某 agent 的任务
cops task list --status IN_PROGRESS --assignee 财务  # 查看忙碌状态
cops agent status #按照分配角色分类统计
cops agent status --agent 财务

**状态定义**：
| Agent 状态 | 含义 | 可否接受新任务 |
|------------|------|----------------|
| 空闲 | cops 中无 IN_PROGRESS 任务 | ✅ |
| 忙碌 | cops 中有 IN_PROGRESS 任务 | ⚠️ 视优先级 |
| 阻塞 | cops 中有 BLOCKED 任务 | ❌ 先解决阻塞 |

---

## 7. 权限矩阵

| 操作 | Orchestrator | 部门 Agent | 人类 |
|------|-------------|-----------|------|
| 创建任务 | ✅ 可创建 + 分配给任意 Agent | ✅ 仅限指派给自己 | ✅ 通过对话委托 |
| 指派任务 | ✅ | ❌ | ❌ |
| 开始任务（标记 IN_PROGRESS） | ❌ | ✅ 仅自己的任务 | ❌ |
| 完成任务（标记 COMPLETED） | ❌ | ✅ 仅自己的任务 | ✅ 确认完成 |
| 分配飞书 Bot 2 | ✅ | ❌ | ❌ |
| 发送 inbox 消息 | ✅ | ✅ 任意 Agent | ❌ |
| 直接与人类对话 | ✅（Bot 1） | ⚠️ 需申请 Bot 2 | ✅ |
| 通过 cmux 与人类对话 | ✅ | ✅ | ✅ |

---

## 8. 关键流程汇总

### 8.1 任务从创建到完成

```
人类表达需求
    │
    ▼
Orchestrator 识别需求
    │
    ▼
草拟任务清单，等待人类确认
    │
    ├── 人类确认 → /cops:create → 状态 NEW
    │
    └── 人类拒绝 → 记录对话，不创建任务

Orchestrator 分配任务
    │
    ▼
cmux send 通知 cops 状态: ASSIGNED
    │
    ▼
部门 Agent 接收
    │
    ▼
标记 IN_PROGRESS in cops
    │
    ▼
执行任务（过程中可与 Orchestrator/其他 Agent 通信）
    │
    ▼
完成 → 标记 COMPLETED in cops
    │
    ▼
cmux send 通知 Orchestrator
    │
    ▼
Orchestrator 汇报人类
```

### 8.2 飞书 Bot 分配流程

```
Agent 请求与人类直接交互
    │
    ▼
Agent → inbox/ (request_bot: true)
    │
    ▼
cmux send → Orchestrator
    │
    ▼
Orchestrator 评估请求
    │
    ├── 合理 → cc-connect 分配 Bot 2 给该 Agent
    │          Agent 通过 Bot 2 与人类对话
    │          对话结束 → Orchestrator 回收 Bot 2
    │
    └── 不合理 → 回复 Agent，建议通过 Orchestrator 中转
```

---

## 9. Orchestrator 系统管理职责

除了任务调度，Orchestrator 还负责统筹和管理所有可用资源，以及持续优化系统能力。

### 9.1 资源管理范围

| 资源类型 | 管理内容 | 示例 |
|----------|----------|------|
| **硬件资源** | 当前设备状态、磁盘空间、CPU/内存使用(检测磁盘空间不足并预警) | 公司其他服务器资产(不同类型硬件配置，服务器资产通过SSH-REMOTE skill 配置，介绍服务器清单和登陆命令) |
| **软件资源** | 软件资源包含当前mac设备上安装的软件、服务器上安装的软件（指为完成不同特定领域工作的工具软件\mcp\skills等，不包含非常基础的依赖包） | Agents是借助LLM的能力完成工作，它的特点是具有发散性，可以创造性的解决特定程序无法完成的工作，但具有不稳定、不确定性，我们倾向于为所有重复性+确定输出内容的工作都逐渐实现使用软件方式完成，程序或工作流 |
| **网络资源** | 外部服务连接状态、API 配额 | 监控飞书 Bot 连接状态 |
| **人力资源** | 人类可用时间、待处理决策 | 评估人类决策积压量 |

### 9.2 系统优化途径

Orchestrator 通过以下方式持续提升系统能力：

#### 途径 1：工作流优化

识别现有工作流中的瓶颈和低效环节，提出改进方案。

```
Orchestrator 监控中发现：
  "财务 Agent 平均任务完成时间从 2h 增长到 4h"
  → 分析原因：是否因为审批流程冗余？
  → 提出优化：简化审批步骤 / 提供模板
  → 与人类讨论确认后实施
```

#### 途径 2：与其他工作流集成

发现外部工具或服务可以扩展系统能力时，提议集成。

```
Orchestrator 识别到：
  "团队经常需要从网页提取数据"
  → 建议集成：引入 data-scraper-agent 或浏览器自动化工具 agent-browser
  → 评估方案后与人类确认
  → 创建集成任务，分配给技术 Agent
```

#### 途径 3：软件或skill升级与新软件安装

分析系统任务执行情况，发现可升级时提出建议。

```
Orchestrator 定期检查：
  - 已完成任务及任务完成途径，是否有重复性的共用步骤，中间遇到了什么问题，如何解决的，是否可以提取skill及添加额外程序和服务来提升任务完成速度和稳定性。
  - github上最热门的开源项目有哪些，都针对哪些使用场景，针对可能有用的软件项目，记录项目列表，避免后期查询时重复列举，并与人类就可能有用的项目展开讨论，如何优化和提升本地系统能力
  → 评估优化风险，制定软件优化范围，遵守最小化原则，不要盲目在全局安装skill
  → 人类确认后分配任务执行优化
```

### 9.3 系统管理监控项

在 CronCreate 10 分钟循环中增加：

```
1. 硬件状态检查
   df -h /                          # 磁盘空间
   sysctl hw.memsize                # 内存
   uptime                           # 系统负载

2. 服务状态检查
   cc-connect daemon status         # cc-connect 守护进程
   curl -s localhost:3000/api/status  # cops web 服务（如果启动）

3. Agent 健康状态
   基于 cops 中各 Agent所属任务 最近状态更新时间判断(需要完成的任务长时间未更新状态)
   超过 6 小时无更新的 Agent 标记为需要注意
```

**系统优化检查**：每日一次（不在 10 分钟循环中）

### 9.4 系统优化的任务化

系统优化建议也需要通过任务流程：

```
Orchestrator 发现优化机会
    │
    ▼
提出建议，等待人类确认
    │
    ├── 确认 → 创建优化任务 /cops:create
    │         → 分配给合适的 Agent 或自己协调创建新的agent来推进
    │
    └── 拒绝 → 记录讨论，暂不实施
```

**特殊权限**：对于低风险操作（如文档整理、日志清理），Orchestrator 可在获得人类一次性授权后自主执行，无需逐个确认。

---

## 10. 总结：Orchestrator 完整职责

| 职责 | 频率 | 说明 |
|------|------|------|
| 任务创建与分配 | 按需 | 识别需求 → 人类确认 → 创建 → 分配 |
| 系统监控 | 10 分钟 | 任务状态、Agent 忙碌度、inbox、硬件、服务 |
| 资源管理 | 10 分钟 | 当前设备状态、服务器资产 |
| 系统优化 | 每日一次 | 工作流改进、工具集成、版本升级 |
| 人类交互 | 按需 | 飞书 Bot 1 + cmux + outbox |
| Bot 分配管理 | 按需 | 分配/回收飞书 Bot 2 |
| Agent 协调 | 按需 | 跨 Agent 协作调度 |

---

*文档版本: 1.1.0*
*创建日期: 2026-04-09*
*更新日期: 2026-04-13*

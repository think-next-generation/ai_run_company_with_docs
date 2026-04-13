# 06 - 人类交互界面设计

> **版本**: v1.0.0
> **创建日期**: 2026-04-01

---

## 1. 人类交互架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          人类交互架构                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        人类角色                                      │    │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐    │    │
│  │   │ 愿景定义者  │    │ 决策审核者  │    │ 边界守护者          │    │    │
│  │   │             │    │             │    │                     │    │    │
│  │   │ - 定义使命  │    │ - 审核变更  │    │ - 设定安全边界      │    │    │
│  │   │ - 设定战略  │    │ - 处理异常  │    │ - 控制敏感资源      │    │    │
│  │   │             │    │ - 仲裁冲突  │    │ - 紧急停止          │    │    │
│  │   └─────────────┘    └─────────────┘    └─────────────────────┘    │    │
│  │                                                                      │    │
│  │   ┌─────────────────────────────────────────────────────────────┐   │    │
│  │   │                     协作参与者                               │   │    │
│  │   │                                                             │   │    │
│  │   │ - 日常任务指派 - 提供领域知识 - 反馈和评价                 │   │    │
│  │   └─────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      交互渠道                                       │    │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐    │    │
│  │   │   飞书界面   │    │  审核控制台  │    │    文档编辑器        │    │    │
│  │   │             │    │             │    │                     │    │    │
│  │   │ - 日常对话  │    │ - 待审核列表│    │ - 直接编辑规范      │    │    │
│  │   │ - 任务指派  │    │ - 决策记录  │    │ - 知识图谱管理      │    │    │
│  │   │ - 进度查询  │    │ - 权限管理  │    │ - 模板维护          │    │    │
│  │   └─────────────┘    └─────────────┘    └─────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      系统响应                                       │    │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐    │    │
│  │   │ 即时回复    │    │ 主动推送    │    │ 定期汇报            │    │    │
│  │   │             │    │             │    │                     │    │    │
│  │   │ - 任务确认  │    │ - 关键进展  │    │ - 日报/周报         │    │    │
│  │   │ - 问题回答  │    │ - 阻塞通知  │    │ - 指标统计          │    │    │
│  │   │ - 协商响应  │    │ - 决策请求  │    │ - 趋势分析          │    │    │
│  │   └─────────────┘    └─────────────┘    └─────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 飞书集成设计

### 2.1 交互模式

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          飞书交互模式                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    1. 任务分配对话                                   │    │
│  │                                                                      │    │
│  │   👤 创始人: @tech-agent 开发用户登录功能                            │    │
│  │                                                                      │    │
│  │   🤖 技术Agent:                                                      │    │
│  │   ┌────────────────────────────────────────────────────────────┐    │    │
│  │   │ ✅ 接收任务                                                  │    │    │
│  │   │                                                             │    │    │
│  │   │ 理解需求：开发用户登录功能                                   │    │    │
│  │   │ 预计时间：2小时                                              │    │    │
│  │   │                                                             │    │    │
│  │   │ 📋 执行计划：                                                │    │    │
│  │   │ 1. 设计登录API接口 (30分钟)                                  │    │    │
│  │   │ 2. 实现认证逻辑 (45分钟)                                     │    │    │
│  │   │ 3. 编写测试用例 (30分钟)                                     │    │    │
│  │   │ 4. 集成测试 (15分钟)                                         │    │    │
│  │   │                                                             │    │    │
│  │   │ ❓ 需要确认：                                                │    │    │
│  │   │ - 登录方式：账号密码 / 手机验证码 / 第三方登录？              │    │    │
│  │   └────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │   👤 创始人: 账号密码 + 手机验证码                                   │    │
│  │                                                                      │    │
│  │   🤖 技术Agent:                                                      │    │
│  │   ┌────────────────────────────────────────────────────────────┐    │    │
│  │   │ ✅ 已记录                                                    │    │    │
│  │   │ 更新预计时间：3小时                                          │    │    │
│  │   │ 开始执行...                                                  │    │    │
│  │   └────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    2. 进度汇报                                       │    │
│  │                                                                      │    │
│  │   🤖 技术Agent:                                                      │    │
│  │   ┌────────────────────────────────────────────────────────────┐    │    │
│  │   │ 📊 任务进度：用户登录功能                                    │    │    │
│  │   │                                                             │    │    │
│  │   │ ████████░░░░░░░░ 50%                                        │    │    │
│  │   │                                                             │    │    │
│  │   │ ✅ 已完成：                                                  │    │    │
│  │   │ - 登录API设计                                                │    │    │
│  │   │ - 账号密码认证逻辑                                           │    │    │
│  │   │                                                             │    │    │
│  │   │ 🔄 进行中：                                                  │    │    │
│  │   │ - 手机验证码集成                                             │    │    │
│  │   │                                                             │    │    │
│  │   │ ⏱️ 剩余时间：1.5小时                                         │    │    │
│  │   └────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    3. 阻塞通知                                       │    │
│  │                                                                      │    │
│  │   🤖 技术Agent:                                                      │    │
│  │   ┌────────────────────────────────────────────────────────────┐    │    │
│  │   │ ⚠️ 任务阻塞通知                                              │    │    │
│  │   │                                                             │    │    │
│  │   │ 任务：用户登录功能                                           │    │    │
│  │   │ 阻塞原因：需要短信服务API密钥                                 │    │    │
│  │   │                                                             │    │    │
│  │   │ 📋 需要的操作：                                              │    │    │
│  │   │ 1. 提供阿里云短信服务AccessKey                               │    │    │
│  │   │ 或                                                          │    │    │
│  │   │ 2. 授权使用其他短信服务                                      │    │    │
│  │   │                                                             │    │    │
│  │   │ 💡 建议优先级：1 > 2                                         │    │    │
│  │   └────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    4. 跨子系统协作                                   │    │
│  │                                                                      │    │
│  │   👤 创始人: @all 上线新产品页面                                     │    │
│  │                                                                      │    │
│  │   🤖 协调Agent:                                                      │    │
│  │   ┌────────────────────────────────────────────────────────────┐    │    │
│  │   │ 🤝 协作任务分解                                              │    │    │
│  │   │                                                             │    │    │
│  │   │ 1️⃣ @product-agent: 产品原型设计 (预计2小时)                  │    │    │
│  │   │ 2️⃣ @tech-agent: 前端开发 (依赖1，预计3小时)                  │    │    │
│  │   │ 3️⃣ @marketing-agent: 推广文案 (与2并行，预计1小时)           │    │    │
│  │   │                                                             │    │    │
│  │   │ 📅 时间线：                                                  │    │    │
│  │   │ [14:00] 产品开始设计                                         │    │    │
│  │   │ [16:00] 技术开始开发 + 营销开始文案                          │    │    │
│  │   │ [19:00] 预计完成                                             │    │    │
│  │   │                                                             │    │    │
│  │   │ ▶️ 开始执行？                                                │    │    │
│  │   └────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │   👤 创始人: 确认开始                                                │    │
│  │                                                                      │    │
│  │   🤖 协调Agent:                                                      │    │
│  │   ┌────────────────────────────────────────────────────────────┐    │    │
│  │   │ ✅ 协作任务已启动                                            │    │    │
│  │   │                                                             │    │    │
│  │   │ 产品Agent 开始工作...                                        │    │    │
│  │   │ 技术Agent 等待中...                                          │    │    │
│  │   │ 营销Agent 等待中...                                          │    │    │
│  │   └────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 消息类型定义

```typescript
// 飞书消息类型

interface FeishuMessage {
  msg_type: 'text' | 'interactive' | 'post';
  content: MessageContent;
}

// 任务确认消息
interface TaskConfirmMessage {
  type: 'task_confirm';
  task_id: string;
  task_name: string;
  estimated_duration: string;
  plan: PlanStep[];
  questions?: Question[];
}

// 进度汇报消息
interface ProgressMessage {
  type: 'progress';
  task_id: string;
  task_name: string;
  progress_percent: number;
  completed_items: string[];
  in_progress_items: string[];
  remaining_time: string;
}

// 阻塞通知消息
interface BlockerMessage {
  type: 'blocker';
  task_id: string;
  task_name: string;
  blocker_description: string;
  required_actions: Action[];
  suggested_priority: string;
}

// 协作请求消息
interface CollaborationMessage {
  type: 'collaboration';
  collaboration_id: string;
  task_name: string;
  participants: Participant[];
  timeline: TimelineEntry[];
  requires_confirmation: boolean;
}

// 决策请求消息
interface DecisionRequestMessage {
  type: 'decision_request';
  decision_id: string;
  context: string;
  options: DecisionOption[];
  impact: string;
  deadline?: Date;
}
```

---

## 3. 审核控制台设计

### 3.1 界面布局

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  审核控制台                                           🔔 3  👤 创始人        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 📋 待审核事项 (3)                                      筛选 ▼  排序 ▼ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 🔴 高优先级 - 需要立即决策                                    ⏰ 2小时前││
│  │                                                                          ││
│  │ 技术子系统请求修改API接口                                                ││
│  │ 影响: 产品、营销子系统需要适配                                           ││
│  │ 原因: 安全性增强                                                         ││
│  │                                                                          ││
│  │ ┌────────────────────────────────────────────────────────────────────┐  ││
│  │ │ 变更详情:                                                          │  ││
│  │ │ - 修改用户API返回格式                                              │  ││
│  │ │ - 移除敏感字段默认返回                                              │  ││
│  │ │ - 新增字段级权限控制                                                │  ││
│  │ │                                                                    │  ││
│  │ │ 影响评估:                                                          │  ││
│  │ │ - product: 需要更新API调用 (预计30分钟)                            │  ││
│  │ │ - marketing: 需要更新数据获取逻辑 (预计15分钟)                     │  ││
│  │ └────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                          ││
│  │ [查看详情] [✅ 批准] [❌ 拒绝] [🔄 协商修改]                            ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 🟡 中优先级 - 今日处理                                        ⏰ 5小时前││
│  │                                                                          ││
│  │ 产品子系统新增"用户画像"能力                                            ││
│  │ 依赖: 需要技术子系统提供数据支持                                        ││
│  │                                                                          ││
│  │ [查看详情] [✅ 批准] [🔄 协商]                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 🟢 低优先级 - 本周处理                                        ⏰ 1天前  ││
│  │                                                                          ││
│  │ 营销子系统请求访问部分用户数据                                          ││
│  │ 用途: 精准营销分析                                                      ││
│  │                                                                          ││
│  │ [查看详情] [✅ 批准] [❌ 拒绝]                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 📊 系统状态概览                                                         ││
│  │                                                                          ││
│  │ 子系统状态:                                                              ││
│  │ ┌─────────┬────────┬──────────┬────────────┐                            ││
│  │ │ 子系统  │ 状态   │ 当前任务 │ 完成率     │                            ││
│  │ ├─────────┼────────┼──────────┼────────────┤                            ││
│  │ │ tech    │ 🟢 活跃 │ 2       │ 85%       │                            ││
│  │ │ product │ 🟢 活跃 │ 1       │ 60%       │                            ││
│  │ │ marketing│ 🟡 等待 │ 0       │ -         │                            ││
│  │ │ service │ 🟢 活跃 │ 1       │ 40%       │                            ││
│  │ └─────────┴────────┴──────────┴────────────┘                            ││
│  │                                                                          ││
│  │ 今日指标:                                                                ││
│  │ - 完成任务: 5    - 进行中: 3    - 阻塞: 0                               ││
│  │ - 平均响应: 2.5小时                                                    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 审核操作API

```typescript
// 审核控制台API

interface ReviewConsoleAPI {

  // 获取待审核列表
  getPendingReviews(filter?: ReviewFilter): Promise<ReviewItem[]>;

  // 获取审核详情
  getReviewDetail(reviewId: string): Promise<ReviewDetail>;

  // 批准变更
  approveChange(reviewId: string, comment?: string): Promise<ApprovalResult>;

  // 拒绝变更
  rejectChange(reviewId: string, reason: string): Promise<RejectionResult>;

  // 请求协商
  requestNegotiation(reviewId: string, concerns: string[]): Promise<NegotiationSession>;

  // 获取系统状态
  getSystemStatus(): Promise<SystemStatus>;
}

interface ReviewItem {
  id: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  subsystem_id: string;
  change_type: ChangeType;
  impact_summary: string;
  created_at: Date;
  deadline?: Date;
}

interface ReviewDetail extends ReviewItem {
  full_description: string;
  change_diff: DiffResult;
  affected_subsystems: AffectedSubsystem[];
  risk_assessment: RiskAssessment;
  recommended_action: 'approve' | 'reject' | 'negotiate';
  similar_changes: HistoricalChange[];
}

interface ApprovalResult {
  success: boolean;
  message: string;
  applied_changes: string[];
  notifications_sent: string[];
}
```

---

## 4. 文档编辑器设计

### 4.1 编辑器功能

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  文档编辑器 - tech/SPEC.md                              💾 保存  📤 发布   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────┐  ┌─────────────────────────────────────────────┐ │
│  │ 📁 文件树             │  │ 编辑区                                      │ │
│  │                       │  │                                              │ │
│  │ 📂 company-ops/       │  │ # 技术研发子系统规范                         │ │
│  │   📄 CHARTER.md       │  │                                              │ │
│  │   📄 CONSTITUTION.yaml│  │ > 版本: 1.0.0                                │ │
│  │   📄 global-graph.json│  │ > 最后更新: 2026-04-01                       │ │
│  │   📂 subsystems/      │  │ > 负责Agent: tech-agent-001                  │ │
│  │     📂 tech/          │  │                                              │ │
│  │       📄 SPEC.md ◄    │  │ ## 1. 身份定义                               │ │
│  │       📄 CONTRACT.yaml│  │                                              │ │
│  │       📄 CAPABILITIES │  │ ### 1.1 基本信息                              │ │
│  │       📂 state/       │  │ - **名称**: 技术研发子系统                   │ │
│  │         📄 goals.md   │  │ - **标识**: tech                             │ │
│  │         📄 status.md  │  │ - **类型**: 核心                             │ │
│  │       📂 knowledge/   │  │                                              │ │
│  │     📂 product/       │  │ ### 1.2 使命                                 │ │
│  │     📂 marketing/     │  │ 通过AI Agent实现软件开发的自动化，           │ │
│  │   📂 shared/          │  │ 确保代码质量和系统稳定性。                   │ │
│  │                       │  │                                              │ │
│  │                       │  │ ## 2. 核心能力                               │ │
│  │                       │  │                                              │ │
│  │                       │  │ ### 2.1 能力清单                             │ │
│  │                       │  │ | 能力ID | 名称 | 描述 |                     │ │
│  │                       │  │ |--------|------|------|                     │ │
│  │                       │  │ | CAP-001| API设计| ...|                     │ │
│  │                       │  │                                              │ │
│  └───────────────────────┘  └─────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 🔍 验证状态                                            ✅ 格式正确    ││
│  │                                                                         ││
│  │ Schema: shared/schemas/spec.schema.json                                ││
│  │ 验证结果: ✅ 所有必填字段已填写                                        ││
│  │          ✅ 格式符合规范                                                ││
│  │          ⚠️ 建议: 能力详情可以更详细                                    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 📝 变更预览                                                             ││
│  │                                                                         ││
│  │ 当前编辑将触发: MINOR 版本更新 (1.0.0 → 1.1.0)                         ││
│  │ 影响范围: tech子系统内部                                                ││
│  │ 需要通知: 无                                                            ││
│  │                                                                         ││
│  │ [预览变更] [提交变更]                                                   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 编辑器功能

```typescript
// 文档编辑器功能

interface DocumentEditor {

  // 文件操作
  openFile(path: string): Promise<Document>;
  saveFile(path: string, content: string): Promise<SaveResult>;
  validateFile(path: string, content: string): Promise<ValidationResult>;

  // 变更分析
  analyzeChange(path: string, oldContent: string, newContent: string): Promise<ChangeAnalysis>;

  // 版本操作
  previewVersionChange(change: ChangeType): VersionPreview;
  commitChange(path: string, message: string): Promise<CommitResult>;

  // 模板操作
  getTemplate(type: DocumentType): Promise<string>;
  applyTemplate(content: string, template: string): Promise<string>;
}

interface ChangeAnalysis {
  change_type: ChangeType;
  affected_sections: string[];
  impact_summary: string;
  affected_subsystems: string[];
  requires_notification: boolean;
  requires_negotiation: boolean;
  suggested_version: string;
}

interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  suggestions: string[];
}
```

---

## 5. 通知与汇报系统

### 5.1 通知类型

```typescript
// 通知类型定义

enum NotificationType {
  // 即时通知
  TASK_CONFIRMED = 'task_confirmed',
  TASK_COMPLETED = 'task_completed',
  BLOCKER_OCCURRED = 'blocker_occurred',
  DECISION_NEEDED = 'decision_needed',

  // 定期汇报
  DAILY_SUMMARY = 'daily_summary',
  WEEKLY_REPORT = 'weekly_report',

  // 系统通知
  SUBSYSTEM_OFFLINE = 'subsystem_offline',
  VERSION_UPDATE = 'version_update',
  LEARNING_INSIGHT = 'learning_insight'
}

interface Notification {
  id: string;
  type: NotificationType;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  title: string;
  content: string;
  actions?: NotificationAction[];
  created_at: Date;
  read: boolean;
  source: string;  // subsystem_id
}

interface NotificationAction {
  label: string;
  type: 'link' | 'button' | 'reply';
  payload: any;
}
```

### 5.2 定期汇报

```typescript
// 定期汇报生成器

class ReportGenerator {

  // 生成日报
  async generateDailyReport(date: Date): Promise<DailyReport> {
    const tasks = await this.getTasksCompletedOn(date);
    const inProgress = await this.getTasksInProgress();
    const blockers = await this.getActiveBlockers();
    const metrics = await this.getDailyMetrics(date);

    return {
      date,
      summary: {
        tasks_completed: tasks.length,
        tasks_in_progress: inProgress.length,
        blockers: blockers.length
      },
      completed_tasks: tasks,
      in_progress_tasks: inProgress,
      active_blockers: blockers,
      metrics,
      highlights: this.extractHighlights(tasks, metrics),
      next_day_plan: this.generateNextDayPlan(inProgress)
    };
  }

  // 生成周报
  async generateWeeklyReport(weekStart: Date): Promise<WeeklyReport> {
    const dailyReports = await this.getDailyReportsForWeek(weekStart);
    const subsystemStats = await this.getSubsystemStats(weekStart);
    const learnings = await this.getLearningsForWeek(weekStart);
    const evolution = await this.getEvolutionEvents(weekStart);

    return {
      week: this.getWeekLabel(weekStart),
      overview: {
        total_tasks: this.sumTasks(dailyReports),
        completion_rate: this.calculateCompletionRate(dailyReports),
        avg_response_time: this.calculateAvgResponseTime(dailyReports)
      },
      subsystem_performance: subsystemStats,
      key_learnings: learnings,
      system_evolution: evolution,
      trends: this.analyzeTrends(dailyReports),
      recommendations: this.generateRecommendations(subsystemStats, learnings)
    };
  }
}
```

### 5.3 汇报消息格式

```markdown
# 📊 每日工作汇报 - 2026年4月1日

## 概要
- ✅ 完成任务: 5
- 🔄 进行中: 3
- ⚠️ 阻塞: 0

## 今日完成
| 子系统 | 任务 | 耗时 |
|--------|------|------|
| tech | 用户认证API | 3h |
| tech | 代码审查 | 1h |
| product | 需求文档更新 | 2h |
| marketing | 推广文案初稿 | 1.5h |
| service | 客户问题处理 | 0.5h |

## 进行中
| 子系统 | 任务 | 进度 | 预计完成 |
|--------|------|------|----------|
| tech | 数据库优化 | 60% | 明日 10:00 |
| product | 原型设计 | 40% | 明日 14:00 |
| marketing | 活动策划 | 20% | 后日 |

## 关键指标
- 平均响应时间: 2.5小时
- 任务完成率: 95%
- 客户满意度: 4.8/5

## 明日计划
1. 完成数据库优化
2. 完成原型设计
3. 启动前端开发（依赖原型完成）

---
🤖 由系统自动生成
```

---

## 6. 紧急操作

### 6.1 紧急停止机制

```typescript
// 紧急停止控制器

class EmergencyController {

  // 紧急停止所有Agent
  async emergencyStopAll(reason: string): Promise<EmergencyStopResult> {
    const results: StopResult[] = [];

    // 1. 停止所有活跃的Agent
    for (const subsystem of await this.getAllActiveSubsystems()) {
      const result = await this.stopSubsystem(subsystem.id);
      results.push(result);
    }

    // 2. 记录紧急停止事件
    await this.logEmergencyStop(reason, results);

    // 3. 通知人类
    await this.notifyHuman({
      type: 'emergency_stop',
      reason,
      affected_subsystems: results.map(r => r.subsystem_id),
      timestamp: new Date()
    });

    return {
      success: results.every(r => r.success),
      stopped_subsystems: results.filter(r => r.success).map(r => r.subsystem_id),
      failed_subsystems: results.filter(r => !r.success).map(r => r.subsystem_id),
      timestamp: new Date()
    };
  }

  // 停止单个子系统
  async stopSubsystem(subsystemId: string): Promise<StopResult> {
    try {
      // 1. 保存当前状态
      await this.saveSubsystemState(subsystemId);

      // 2. 取消进行中的任务
      await this.cancelActiveTasks(subsystemId);

      // 3. 终止Agent进程
      await this.terminateAgent(subsystemId);

      // 4. 更新状态
      await this.updateSubsystemStatus(subsystemId, 'stopped');

      return { subsystem_id: subsystemId, success: true };
    } catch (error) {
      return { subsystem_id: subsystemId, success: false, error: error.message };
    }
  }

  // 恢复运行
  async resumeSubsystem(subsystemId: string): Promise<ResumeResult> {
    // 1. 恢复状态
    await this.restoreSubsystemState(subsystemId);

    // 2. 重启Agent
    await this.startAgent(subsystemId);

    // 3. 恢复进行中的任务
    await this.resumeTasks(subsystemId);

    return { subsystem_id: subsystemId, success: true };
  }
}
```

### 6.2 紧急操作界面

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚠️ 紧急操作面板                                           🔴 系统运行中   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 🛑 紧急停止                                                             ││
│  │                                                                         ││
│  │ 警告：此操作将立即停止所有Agent和进行中的任务。                         ││
│  │                                                                         ││
│  │ 停止原因:                                                               ││
│  │ ┌─────────────────────────────────────────────────────────────────────┐ ││
│  │ │ [输入停止原因...]                                                    │ ││
│  │ └─────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                         ││
│  │ [🛑 紧急停止所有Agent]                                                 ││
│  │                                                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 🔧 子系统控制                                                           ││
│  │                                                                         ││
│  │ ┌─────────────┬──────────┬──────────────────────────────────────────┐  ││
│  │ │ 子系统      │ 状态     │ 操作                                     │  ││
│  │ ├─────────────┼──────────┼──────────────────────────────────────────┤  ││
│  │ │ tech        │ 🟢 运行中 │ [暂停] [停止] [重启]                     │  ││
│  │ │ product     │ 🟢 运行中 │ [暂停] [停止] [重启]                     │  ││
│  │ │ marketing   │ 🟡 暂停  │ [恢复] [停止] [重启]                     │  ││
│  │ │ service     │ 🟢 运行中 │ [暂停] [停止] [重启]                     │  ││
│  │ │ finance     │ 🔴 停止  │ [启动]                                    │  ││
│  │ └─────────────┴──────────┴──────────────────────────────────────────┘  ││
│  │                                                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ 📋 紧急操作历史                                                         ││
│  │                                                                         ││
│  │ 2026-04-01 10:30 - 系统启动                                             ││
│  │ 2026-03-30 18:00 - marketing 暂停 (维护)                                ││
│  │ 2026-03-28 09:00 - finance 停止 (非工作时间)                            ││
│  │                                                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*文档版本: v1.0.0*
*最后更新: 2026-04-01*

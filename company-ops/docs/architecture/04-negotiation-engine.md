# 04 - 动态协商引擎设计

> **版本**: v1.0.0
> **创建日期**: 2026-04-01

---

## 1. 协商引擎架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          动态协商引擎架构                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        协商入口                                      │    │
│  │   输入: 意图 + 上下文 + 来源                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     1. 意图理解层                                    │    │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐    │    │
│  │   │ 意图分类    │───►│ 实体抽取    │───►│ 关系识别            │    │    │
│  │   │ (任务/查询/ │    │ (目标/时间/ │    │ (依赖/冲突/协同)    │    │    │
│  │   │  协作/确认) │    │  资源/约束)  │    │                     │    │    │
│  │   └─────────────┘    └─────────────┘    └─────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     2. 能力匹配层                                    │    │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐    │    │
│  │   │ 查询注册表  │───►│ 图谱遍历    │───►│ 匹配评分            │    │    │
│  │   │             │    │             │    │ (可行性/适合度)     │    │    │
│  │   └─────────────┘    └─────────────┘    └─────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     3. 可行性评估层                                  │    │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐    │    │
│  │   │ 资源检查    │───►│ 约束验证    │───►│ 风险评估            │    │    │
│  │   │ (时间/人力/ │    │ (边界/权限/ │    │ (依赖风险/技术风险) │    │    │
│  │   │  工具)      │    │  规则)       │    │                     │    │    │
│  │   └─────────────┘    └─────────────┘    └─────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     4. 响应生成层                                    │    │
│  │                                                                      │    │
│  │   ┌───────────────────────────────────────────────────────────┐     │    │
│  │   │                    响应类型决策树                          │     │    │
│  │   │                                                            │     │    │
│  │   │   可行性 >= 0.9 ───────────────────► AcceptResponse       │     │    │
│  │   │        │                      │                           │     │    │
│  │   │        ▼                      ▼                           │     │    │
│  │   │   0.5-0.9 ──────────► PartialAcceptResponse               │     │    │
│  │   │        │                      │                           │     │    │
│  │   │        ▼                      ▼                           │     │    │
│  │   │   < 0.5 ─────────────► NegotiateResponse                  │     │    │
│  │   │                              │                            │     │    │
│  │   │                              ▼                            │     │    │
│  │   │                        RejectResponse                     │     │    │
│  │   └───────────────────────────────────────────────────────────┘     │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        协商输出                                      │    │
│  │   输出: 响应类型 + 计划/条件/替代方案 + 时间线                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 意图理解层

### 2.1 意图分类

```typescript
// 意图类型定义

enum IntentType {
  TASK_REQUEST = 'task_request',       // 任务请求
  QUERY = 'query',                     // 状态查询
  COLLABORATION = 'collaboration',     // 协作请求
  CONFIRMATION = 'confirmation',       // 确认请求
  FEEDBACK = 'feedback',               // 反馈提供
  CANCELLATION = 'cancellation',       // 取消请求
  MODIFICATION = 'modification'        // 修改请求
}

interface Intent {
  type: IntentType;
  confidence: number;
  description: string;
  entities: ExtractedEntities;
  relations: ExtractedRelations[];
  source: IntentSource;
  context: IntentContext;
}

interface ExtractedEntities {
  targets?: string[];      // 目标对象
  deadlines?: Date[];      // 截止时间
  resources?: string[];    // 资源需求
  constraints?: string[];  // 约束条件
  priorities?: string[];   // 优先级
}

interface ExtractedRelations {
  type: 'dependency' | 'conflict' | 'collaboration' | 'sequence';
  from: string;
  to: string;
  description?: string;
}
```

### 2.2 意图理解示例

```typescript
// 输入: "开发用户登录功能，需要产品和测试配合，本周五前完成"

const intent: Intent = {
  type: IntentType.COLLABORATION,
  confidence: 0.92,
  description: "开发用户登录功能，涉及跨子系统协作",
  entities: {
    targets: ["用户登录功能"],
    deadlines: [new Date("2026-04-04")], // 本周五
    resources: ["产品支持", "测试支持"],
    constraints: [],
    priorities: []
  },
  relations: [
    { type: 'collaboration', from: 'tech', to: 'product', description: '需要产品配合' },
    { type: 'collaboration', from: 'tech', to: 'service', description: '需要测试配合' }
  ],
  source: {
    type: 'human',
    id: 'founder',
    channel: 'feishu'
  },
  context: {
    conversation_id: 'conv-001',
    previous_intents: [],
    current_goals: []
  }
};
```

---

## 3. 能力匹配层

### 3.1 匹配算法

```typescript
// 能力匹配服务

interface CapabilityMatcher {
  // 主匹配方法
  match(intent: Intent): Promise<MatchResult[]>;

  // 计算匹配分数
  calculateScore(intent: Intent, subsystem: Subsystem): number;

  // 检查能力覆盖
  checkCoverage(intent: Intent, capabilities: Capability[]): CoverageResult;
}

interface MatchResult {
  subsystem: Subsystem;
  score: number;           // 总匹配分数 0-1
  coverage: CoverageResult;
  availability: number;    // 可用性 0-1
  estimated_response: string;
  recommendations: string[];
}

interface CoverageResult {
  fully_covered: string[];    // 完全覆盖的能力
  partially_covered: string[]; // 部分覆盖的能力
  not_covered: string[];      // 无法覆盖的能力
  coverage_score: number;     // 覆盖分数 0-1
}

// 匹配算法实现
class CapabilityMatcherImpl implements CapabilityMatcher {

  async match(intent: Intent): Promise<MatchResult[]> {
    const results: MatchResult[] = [];

    // 1. 从注册表获取所有子系统
    const subsystems = await this.registry.getAll();

    // 2. 对每个子系统计算匹配分数
    for (const subsystem of subsystems) {
      const score = this.calculateScore(intent, subsystem);
      const coverage = this.checkCoverage(intent, subsystem.capabilities);
      const availability = await this.checkAvailability(subsystem);

      if (coverage.coverage_score > 0) {
        results.push({
          subsystem,
          score: score * availability,
          coverage,
          availability,
          estimated_response: this.estimateResponse(subsystem, intent),
          recommendations: this.generateRecommendations(coverage)
        });
      }
    }

    // 3. 按分数排序
    return results.sort((a, b) => b.score - a.score);
  }

  calculateScore(intent: Intent, subsystem: Subsystem): number {
    let score = 0;

    // 能力匹配分数 (40%)
    const coverage = this.checkCoverage(intent, subsystem.capabilities);
    score += coverage.coverage_score * 0.4;

    // 历史成功率 (20%)
    score += subsystem.metrics.success_rate * 0.2;

    // 负载因素 (20%)
    score += (1 - subsystem.current_load) * 0.2;

    // 关系因素 (20%) - 是否有相关协作历史
    const relationScore = this.calculateRelationScore(intent, subsystem);
    score += relationScore * 0.2;

    return score;
  }
}
```

### 3.2 匹配示例

```typescript
// 匹配结果示例

const matchResults: MatchResult[] = [
  {
    subsystem: {
      id: 'tech',
      name: '技术研发子系统',
      capabilities: ['api-design', 'code-review', 'testing'],
      current_load: 0.3,
      metrics: { success_rate: 0.95 }
    },
    score: 0.85,
    coverage: {
      fully_covered: ['api-design', 'testing'],
      partially_covered: [],
      not_covered: [],
      coverage_score: 1.0
    },
    availability: 0.9,
    estimated_response: '2小时',
    recommendations: []
  },
  {
    subsystem: {
      id: 'product',
      name: '产品设计子系统',
      capabilities: ['requirements', 'prototype'],
      current_load: 0.5,
      metrics: { success_rate: 0.9 }
    },
    score: 0.72,
    coverage: {
      fully_covered: ['requirements'],
      partially_covered: [],
      not_covered: ['api-design', 'testing'],
      coverage_score: 0.33
    },
    availability: 0.8,
    estimated_response: '1小时',
    recommendations: ['可与tech子系统协作完成全部需求']
  }
];
```

---

## 4. 可行性评估层

### 4.1 评估维度

```typescript
// 可行性评估

interface FeasibilityAssessment {
  overall_score: number;      // 总可行性分数 0-1
  resource_feasibility: ResourceFeasibility;
  constraint_feasibility: ConstraintFeasibility;
  risk_assessment: RiskAssessment;
  recommendations: string[];
  blockers: Blocker[];
}

interface ResourceFeasibility {
  score: number;
  time: {
    available: number;      // 可用时间（小时）
    required: number;       // 需要时间（小时）
    feasible: boolean;
  };
  tools: {
    available: string[];    // 可用工具
    required: string[];     // 需要工具
    missing: string[];      // 缺失工具
  };
  dependencies: {
    resolved: Dependency[]; // 已解决的依赖
    pending: Dependency[];  // 待解决的依赖
    blocked: Dependency[];  // 阻塞的依赖
  };
}

interface ConstraintFeasibility {
  score: number;
  boundary_checks: {
    constraint: string;
    passed: boolean;
    message: string;
  }[];
  permission_checks: {
    resource: string;
    access: 'granted' | 'denied' | 'pending';
    reason?: string;
  }[];
}

interface RiskAssessment {
  score: number;
  risks: {
    type: 'dependency' | 'technical' | 'resource' | 'external';
    description: string;
    probability: number;   // 0-1
    impact: number;        // 0-1
    mitigation: string;
  }[];
}

interface Blocker {
  id: string;
  type: 'dependency' | 'permission' | 'resource' | 'knowledge';
  description: string;
  resolution_options: string[];
  auto_resolvable: boolean;
}
```

### 4.2 评估流程

```typescript
// 可行性评估器

class FeasibilityEvaluator {

  async assess(intent: Intent, matchResult: MatchResult): Promise<FeasibilityAssessment> {
    const resourceFeasibility = await this.assessResources(intent, matchResult);
    const constraintFeasibility = await this.assessConstraints(intent, matchResult);
    const riskAssessment = await this.assessRisks(intent, matchResult);
    const blockers = this.identifyBlockers(resourceFeasibility, constraintFeasibility);

    // 计算总分
    const overallScore = this.calculateOverallScore(
      resourceFeasibility,
      constraintFeasibility,
      riskAssessment
    );

    return {
      overall_score: overallScore,
      resource_feasibility: resourceFeasibility,
      constraint_feasibility: constraintFeasibility,
      risk_assessment: riskAssessment,
      recommendations: this.generateRecommendations(blockers),
      blockers: blockers
    };
  }

  private calculateOverallScore(
    resource: ResourceFeasibility,
    constraint: ConstraintFeasibility,
    risk: RiskAssessment
  ): number {
    // 权重分配
    const weights = {
      resource: 0.4,
      constraint: 0.35,
      risk: 0.25
    };

    return (
      resource.score * weights.resource +
      constraint.score * weights.constraint +
      risk.score * weights.risk
    );
  }
}
```

---

## 5. 响应生成层

### 5.1 响应类型定义

```typescript
// 协商响应类型

interface BaseResponse {
  type: 'accept' | 'partial_accept' | 'negotiate' | 'reject';
  confidence: number;
  processing_time_ms: number;
  subsystem_id: string;
}

interface AcceptResponse extends BaseResponse {
  type: 'accept';
  confidence: number;  // 0.9-1.0

  plan: {
    steps: PlanStep[];
    estimated_duration: string;
    required_resources: string[];
    milestones: Milestone[];
  };

  pre_conditions?: string[];
  assumptions: string[];
}

interface PartialAcceptResponse extends BaseResponse {
  type: 'partial_accept';
  confidence: number;  // 0.5-0.9

  accepted_parts: {
    description: string;
    estimated_duration: string;
  }[];

  need_help_parts: {
    description: string;
    from_subsystem: string;
    reason: string;
    critical: boolean;
  }[];

  alternative_timeline?: string;
  total_estimated_duration: string;
}

interface NegotiateResponse extends BaseResponse {
  type: 'negotiate';
  confidence: number;  // 0.3-0.5

  can_do_with_conditions: {
    condition: string;
    impact: string;
    required_from_human?: string;
  }[];

  alternatives: {
    description: string;
    trade_offs: string;
    estimated_duration: string;
  }[];

  blockers?: {
    description: string;
    possible_resolutions: string[];
  }[];

  questions?: {
    question: string;
    options?: string[];
    impact: string;
  }[];
}

interface RejectResponse extends BaseResponse {
  type: 'reject';
  confidence: number;  // < 0.3

  reason: string;
  detailed_explanation: string;

  suggestions: {
    description: string;
    alternative_subsystem?: string;
    required_changes?: string[];
  }[];

  escalate_to_human: boolean;
  escalation_reason?: string;
}

interface PlanStep {
  sequence: number;
  description: string;
  estimated_duration: string;
  dependencies: string[];
  deliverables: string[];
}

interface Milestone {
  name: string;
  criteria: string;
  estimated_time: string;
}
```

### 5.2 响应生成逻辑

```typescript
// 响应生成器

class ResponseGenerator {

  generate(feasibility: FeasibilityAssessment, intent: Intent): NegotiationResponse {
    const score = feasibility.overall_score;

    // 根据可行性分数决定响应类型
    if (score >= 0.9) {
      return this.generateAcceptResponse(feasibility, intent);
    } else if (score >= 0.5) {
      return this.generatePartialAcceptResponse(feasibility, intent);
    } else if (score >= 0.3) {
      return this.generateNegotiateResponse(feasibility, intent);
    } else {
      return this.generateRejectResponse(feasibility, intent);
    }
  }

  private generateAcceptResponse(
    feasibility: FeasibilityAssessment,
    intent: Intent
  ): AcceptResponse {
    // 生成执行计划
    const plan = this.generatePlan(intent, feasibility);

    // 识别前置条件
    const preConditions = feasibility.resource_feasibility.dependencies.pending
      .map(d => d.description);

    // 识别假设
    const assumptions = this.identifyAssumptions(intent, feasibility);

    return {
      type: 'accept',
      confidence: feasibility.overall_score,
      processing_time_ms: 0, // 由调用者填充
      subsystem_id: this.subsystemId,
      plan,
      pre_conditions: preConditions.length > 0 ? preConditions : undefined,
      assumptions
    };
  }

  private generatePartialAcceptResponse(
    feasibility: FeasibilityAssessment,
    intent: Intent
  ): PartialAcceptResponse {
    // 分解任务为可接受和需要帮助的部分
    const { acceptedParts, needHelpParts } = this.decomposeTask(intent, feasibility);

    return {
      type: 'partial_accept',
      confidence: feasibility.overall_score,
      processing_time_ms: 0,
      subsystem_id: this.subsystemId,
      accepted_parts: acceptedParts,
      need_help_parts: needHelpParts,
      total_estimated_duration: this.calculateTotalDuration(acceptedParts, needHelpParts)
    };
  }

  private generateNegotiateResponse(
    feasibility: FeasibilityAssessment,
    intent: Intent
  ): NegotiateResponse {
    // 生成条件和替代方案
    const conditions = this.generateConditions(feasibility);
    const alternatives = this.generateAlternatives(intent, feasibility);
    const blockers = feasibility.blockers;
    const questions = this.generateQuestions(intent, feasibility);

    return {
      type: 'negotiate',
      confidence: feasibility.overall_score,
      processing_time_ms: 0,
      subsystem_id: this.subsystemId,
      can_do_with_conditions: conditions,
      alternatives,
      blockers: blockers.length > 0 ? blockers : undefined,
      questions: questions.length > 0 ? questions : undefined
    };
  }

  private generateRejectResponse(
    feasibility: FeasibilityAssessment,
    intent: Intent
  ): RejectResponse {
    // 确定是否需要升级到人类
    const shouldEscalate = this.shouldEscalateToHuman(feasibility, intent);

    return {
      type: 'reject',
      confidence: feasibility.overall_score,
      processing_time_ms: 0,
      subsystem_id: this.subsystemId,
      reason: this.identifyPrimaryReason(feasibility),
      detailed_explanation: this.generateDetailedExplanation(feasibility),
      suggestions: this.generateSuggestions(intent, feasibility),
      escalate_to_human: shouldEscalate,
      escalation_reason: shouldEscalate ? this.getEscalationReason(feasibility) : undefined
    };
  }
}
```

---

## 6. 协商流程示例

### 6.1 完整协商流程

```
创始人: "@tech-agent 开发用户登录功能，本周五前完成"
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 意图理解                                                                 │
│    类型: TASK_REQUEST                                                       │
│    目标: 用户登录功能                                                        │
│    约束: 本周五前                                                            │
│    置信度: 0.95                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. 能力匹配                                                                 │
│    最佳匹配: tech子系统 (score: 0.88)                                       │
│    覆盖能力: api-design, testing                                            │
│    可用性: 0.9                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. 可行性评估                                                               │
│    资源可行性: 0.85 (时间充足，工具可用)                                     │
│    约束可行性: 0.95 (在边界内)                                               │
│    风险评估: 0.80 (依赖产品子系统提供需求)                                   │
│    总分: 0.87                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. 响应生成: PARTIAL_ACCEPT (0.87)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ✅ 可接受部分:                                                             │
│  - API接口设计和实现 (预计2小时)                                            │
│  - 认证逻辑开发 (预计1.5小时)                                               │
│  - 单元测试编写 (预计1小时)                                                 │
│                                                                             │
│  ⚠️ 需要协助:                                                               │
│  - 登录方式确认 (需要产品子系统)                                            │
│  - 设计稿参考 (需要产品子系统)                                              │
│                                                                             │
│  📅 总预计时间: 4.5小时 + 等待产品确认                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
技术Agent: "✅ 接收任务
          理解需求：开发用户登录功能
          预计时间：4.5小时（不含等待产品确认）

          📋 执行计划：
          1. 设计登录API接口 (30分钟)
          2. 实现认证逻辑 (1.5小时)
          3. 编写测试用例 (1小时)
          4. 集成测试 (30分钟)

          ❓ 需要确认：
          - 登录方式：账号密码 / 手机验证码 / 第三方登录？
          - 需要产品子系统提供需求文档和设计稿"
```

---

## 7. 多子系统协作协商

### 7.1 协作协商流程

```typescript
// 协作协商协调器

class CollaborationNegotiator {

  async negotiateCollaboration(
    intent: Intent,
    requiredSubsystems: string[]
  ): Promise<CollaborationResult> {

    // 1. 收集所有子系统的响应
    const responses = await Promise.all(
      requiredSubsystems.map(id => this.getNegotiationResponse(id, intent))
    );

    // 2. 分析协作可行性
    const analysis = this.analyzeCollaborationFeasibility(responses);

    // 3. 生成协作计划
    if (analysis.feasible) {
      return this.generateCollaborationPlan(intent, responses);
    } else {
      return this.generateAlternativeProposal(intent, responses, analysis);
    }
  }

  private analyzeCollaborationFeasibility(
    responses: NegotiationResponse[]
  ): CollaborationAnalysis {
    const allAccepted = responses.every(r => r.type === 'accept');
    const anyRejected = responses.some(r => r.type === 'reject');

    return {
      feasible: allAccepted && !anyRejected,
      confidence: this.calculateOverallConfidence(responses),
      blockers: this.identifyCollaborationBlockers(responses),
      timeline_conflicts: this.identifyTimelineConflicts(responses)
    };
  }

  private generateCollaborationPlan(
    intent: Intent,
    responses: AcceptResponse[]
  ): CollaborationResult {
    // 合并所有计划
    const mergedPlan = this.mergePlans(responses.map(r => r.plan));

    // 识别依赖关系
    const dependencies = this.identifyDependencies(responses);

    // 生成时间线
    const timeline = this.generateTimeline(mergedPlan, dependencies);

    return {
      type: 'collaboration_accepted',
      plan: mergedPlan,
      timeline,
      participants: responses.map(r => r.subsystem_id),
      total_estimated_duration: timeline.total_duration
    };
  }
}
```

### 7.2 协作协商示例

```
创始人: "@all 上线新产品页面"
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 协调Agent: 分析协作需求                                                     │
│                                                                             │
│ 识别需要的子系统:                                                           │
│ - product: 产品原型设计                                                     │
│ - tech: 前端开发                                                            │
│ - marketing: 推广文案                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼ (并行请求)
     ┌────┴────┬────────────┐
     ▼         ▼            ▼
  product    tech       marketing
  (ACCEPT)   (ACCEPT)   (ACCEPT)
     │         │            │
     └────┬────┴────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 协调Agent: 生成协作计划                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  🤝 协作任务分解                                                            │
│                                                                             │
│  1️⃣ @product: 产品原型设计 (预计2小时)                                      │
│  2️⃣ @tech: 前端开发 (依赖1，预计3小时)                                      │
│  3️⃣ @marketing: 推广文案 (与2并行，预计1小时)                               │
│                                                                             │
│  📅 时间线：                                                                │
│  [14:00] 产品开始设计                                                       │
│  [16:00] 技术开始开发 + 营销开始文案                                        │
│  [19:00] 预计完成                                                           │
│                                                                             │
│  ▶️ 开始执行？                                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*文档版本: v1.0.0*
*最后更新: 2026-04-01*

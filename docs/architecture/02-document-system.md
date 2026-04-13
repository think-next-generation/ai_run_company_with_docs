# 02 - 文档体系设计

> **版本**: v1.0.0
> **创建日期**: 2026-04-01

---

## 1. 目录结构设计

```
company-ops/
├── .system/                          # 系统级配置（隐藏目录）
│   ├── config.yaml                   # 全局配置
│   ├── graph-cache/                  # 图谱缓存
│   └── state-index.json              # 状态索引
│
├── CHARTER.md                        # 公司愿景/使命/价值观
├── CONSTITUTION.yaml                 # 核心规则（结构化）
├── global-graph.json                 # 全局知识图谱
├── LEARNING.md                       # 系统学习记录
├── EVOLUTION.md                      # 演进日志
│
├── subsystems/                       # 所有子系统
│   ├── _registry.json                # 子系统注册表
│   │
│   ├── tech/                         # 技术研发子系统
│   │   ├── SPEC.md                   # 子系统规范
│   │   ├── CONTRACT.yaml             # 交互契约
│   │   ├── CAPABILITIES.yaml         # 能力定义
│   │   ├── local-graph.json          # 子系统知识图谱
│   │   │
│   │   ├── state/                    # 状态目录
│   │   │   ├── goals.md              # 当前目标
│   │   │   ├── status.md             # 运行状态
│   │   │   ├── metrics.yaml          # 指标数据
│   │   │   └── history/              # 历史记录
│   │   │
│   │   ├── capabilities/             # 能力实现
│   │   │   ├── api-design.md
│   │   │   └── code-review.md
│   │   │
│   │   ├── knowledge/                # 知识库
│   │   │   ├── patterns/             # 模式库
│   │   │   ├── decisions/            # 架构决策记录
│   │   │   └── learnings/            # 学习记录
│   │   │
│   │   └── code/                     # 内置代码（可选）
│   │       ├── tools/
│   │       └── scripts/
│   │
│   ├── product/                      # 产品设计子系统
│   ├── marketing/                    # 市场营销子系统
│   ├── service/                      # 客户服务子系统
│   ├── finance/                      # 财务子系统
│   └── operations/                   # 运营管理子系统
│
├── shared/                           # 共享资源
│   ├── patterns/                     # 跨系统模式
│   ├── templates/                    # 文档模板
│   └── schemas/                      # JSON Schema
│
└── human/                            # 人类交互界面
    ├── inbox/                        # 待处理事项
    ├── reviews/                      # 待审核决策
    └── feedback/                     # 反馈记录
```

---

## 2. 全局文档格式

### 2.1 CHARTER.md（愿景文档）

```markdown
# 公司愿景

## 使命
[一句话描述公司存在的意义]

## 愿景
[描述公司未来的理想状态]

## 价值观
- 价值观1: [描述]
- 价值观2: [描述]

## 战略目标
### 2026年
- [ ] 目标1
- [ ] 目标2

## 原则
- [决策原则1]
- [决策原则2]
```

### 2.2 CONSTITUTION.yaml（核心规则）

```yaml
# CONSTITUTION.yaml - 系统宪法 v1.0.0

version: "1.0.0"
effective_date: "2026-04-01"

# 全局约束
global_constraints:
  # 安全边界
  security:
    - 敏感数据不得离开本地执行环境
    - 跨子系统数据访问需记录审计日志
    - 财务/法务操作需人工确认

  # 伦理边界
  ethics:
    - 不欺骗用户
    - 不隐瞒风险
    - 不承诺无法实现的功能

  # 资源边界
  resources:
    max_concurrent_agents: 10
    max_task_duration_hours: 8
    auto_shutdown_idle_minutes: 30

# 子系统通用规则
subsystem_rules:
  # 自主决策范围
  autonomy:
    can_decide:
      - 任务执行方法
      - 工具选择
      - 时间安排（在截止期内）
      - 技术方案选择

    must_confirm:
      - 跨子系统协作
      - 敏感数据访问
      - 外部服务调用
      - 规范修改

  # 演进规则
  evolution:
    independent_changes:
      - 能力实现细节
      - 内部状态管理
      - 知识库内容

    requires_negotiation:
      - 接口变更
      - 能力增减
      - 边界调整

# 人类角色权限
human_roles:
  founder:
    permissions:
      - 定义愿景和使命
      - 审核关键决策
      - 修改任何规范
      - 紧急停止系统
    interaction_channels:
      - feishu          # 日常交互
      - review_console  # 关键审核
      - direct_edit     # 直接编辑文档

# 冲突解决规则
conflict_resolution:
  priority_order:
    - human_directive   # 人类指令最高
    - constitution      # 宪法规则
    - subsystem_contract # 子系统契约
    - local_preference  # 本地偏好

  escalation:
    timeout_minutes: 30
    notify_human: true
```

---

## 3. 子系统文档格式

### 3.1 SPEC.md（子系统规范模板）

```markdown
# [子系统名称] 规范

> 版本: 1.0.0
> 最后更新: 2026-04-01
> 负责Agent: [Agent ID]

## 1. 身份定义

### 1.1 基本信息
- **名称**: [子系统名称]
- **标识**: [唯一标识符，如 tech, product]
- **类型**: [核心/支撑/服务]

### 1.2 使命
[一句话描述这个子系统存在的意义]

### 1.3 边界定义

**我能做什么**:
- [能力1]
- [能力2]

**我不能做什么**:
- [限制1]
- [限制2]

**我需要依赖**:
- [依赖1]: [来自哪个子系统]
- [依赖2]: ...

---

## 2. 核心能力

### 2.1 能力清单
| 能力ID | 名称 | 描述 | 输入 | 输出 |
|--------|------|------|------|------|
| CAP-001 | [能力名] | ... | ... | ... |

### 2.2 能力详情
[每个能力的详细描述，链接到 capabilities/ 目录]

---

## 3. 交互协议

### 3.1 我能提供
| 服务 | 触发条件 | 响应时间 | 格式 |
|------|----------|----------|------|
| [服务1] | ... | ... | ... |

### 3.2 我需要
| 需求 | 来源子系统 | 频率 | 必要性 |
|------|------------|------|--------|
| [需求1] | ... | ... | 必须/可选 |

### 3.3 交互示例
```
请求: [示例请求]
响应: [示例响应]
```

---

## 4. 决策框架

### 4.1 自主决策范围
- ✅ [我可以自主决定的事项]

### 4.2 需要确认的事项
- ⚠️ [需要人类或其他子系统确认的事项]

### 4.3 决策偏好
[描述在做决策时的偏好和权衡原则]

---

## 5. 演进规则

### 5.1 可独立修改
- [不需要协商的修改范围]

### 5.2 需要协商修改
- [需要通知/协商相关子系统的修改]

### 5.3 版本兼容性
[描述如何处理版本兼容性问题]

---

## 6. 状态与指标

### 6.1 当前状态
[链接到 state/status.md]

### 6.2 关键指标
[链接到 state/metrics.yaml]
```

### 3.2 CONTRACT.yaml（交互契约模板）

```yaml
# CONTRACT.yaml - 子系统交互契约 v1.0.0

version: "1.0.0"
subsystem_id: "tech"
last_updated: "2026-04-01"

# 提供的服务
provides:
  - service_id: "api-design"
    name: "API设计服务"
    description: "设计和定义RESTful/GraphQL API"
    version: "1.0.0"

    input_schema:
      type: object
      required:
        - feature_name
        - requirements
      properties:
        feature_name:
          type: string
          description: "功能名称"
        requirements:
          type: string
          description: "功能需求描述"
        style:
          type: string
          enum: [rest, graphql, grpc]
          default: rest

    output_schema:
      type: object
      properties:
        api_spec:
          type: object
          description: "OpenAPI/GraphQL Schema"
        documentation:
          type: string
          description: "API文档"

    sla:
      response_time_minutes: 30
      availability: 0.99

    dependencies:
      - subsystem: "product"
        need: "需求文档"

# 需要的服务
consumes:
  - service_id: "requirements"
    provider: "product"
    description: "产品需求文档"
    version_constraint: ">=1.0.0"
    frequency: "on-demand"

# 事件订阅
events:
  subscribes:
    - event: "product.requirements.updated"
      action: "review_impact"

  publishes:
    - event: "tech.api.deployed"
      payload:
        api_name: string
        version: string
        endpoints: array

# 变更历史
changelog:
  - version: "1.0.0"
    date: "2026-04-01"
    changes:
      - "初始版本"
```

### 3.3 CAPABILITIES.yaml（能力定义模板）

```yaml
# CAPABILITIES.yaml - 子系统能力定义

version: "1.0.0"
subsystem_id: "tech"

capabilities:
  - id: "CAP-001"
    name: "API设计与开发"
    description: "设计、实现和部署RESTful/GraphQL API"

    skills:
      - "OpenAPI规范编写"
      - "GraphQL Schema设计"
      - "数据库模型设计"
      - "代码实现"
      - "单元测试"

    tools:
      - name: "Claude Code"
        usage: "主要开发工具"
      - name: "SQLite"
        usage: "本地数据存储"

    quality_metrics:
      - name: "测试覆盖率"
        target: ">=80%"
      - name: "API响应时间"
        target: "<500ms"

    documentation: "./capabilities/api-design.md"

# 能力等级
maturity_levels:
  - level: 1
    name: "基础"
    description: "能够完成基本任务，需要指导"

  - level: 2
    name: "熟练"
    description: "能够独立完成任务，质量稳定"

  - level: 3
    name: "专家"
    description: "能够处理复杂场景，指导他人"

current_maturity:
  CAP-001: 2
```

---

## 4. 状态文件格式

### 4.1 state/goals.md

```markdown
# 当前目标

> 更新时间: 2026-04-01 10:30

## 本周目标 (2026-W14)

| 优先级 | 目标 | 来源 | 状态 | 截止日期 |
|--------|------|------|------|----------|
| P0 | 完成用户认证API | 外部指令 | 进行中 | 2026-04-03 |
| P1 | 优化数据库查询性能 | 运营涌现 | 待开始 | 2026-04-05 |
| P2 | 重构日志模块 | 内部自生 | 计划中 | 2026-04-07 |

## 本季度目标 (2026-Q2)

| 目标 | 关键结果 | 进度 |
|------|----------|------|
| 提升系统稳定性 | API可用性达到99.9% | 0% |
| 技术债务清理 | 完成5个遗留问题修复 | 20% |

## 长期目标

- [ ] 探索Rust重写核心模块
- [ ] 建立完整的CI/CD流水线
```

### 4.2 state/status.md

```markdown
# 运行状态

> 更新时间: 2026-04-01 10:30
> 状态: 🟢 正常运行

## 当前工作

### 进行中的任务
- T-001: 用户认证API开发
  - 进度: 60%
  - 预计完成: 2026-04-03
  - 阻塞: 无

### 等待中的任务
- T-002: 数据库优化（等待T-001完成）

## 资源状态
- Agent状态: 活跃
- 最后心跳: 2026-04-01 10:29
- 当前负载: 中等

## 近期完成
- T-000: API框架搭建 (2026-04-01)
```

### 4.3 state/metrics.yaml

```yaml
# 指标数据
updated_at: "2026-04-01T10:30:00Z"

# 任务指标
tasks:
  total: 15
  completed: 8
  in_progress: 2
  blocked: 0
  avg_completion_time_hours: 4.5

# 质量指标
quality:
  test_coverage: 0.82
  bug_rate: 0.05
  code_review_pass_rate: 0.95

# 协作指标
collaboration:
  cross_subsystem_requests: 3
  successful_negotiations: 3
  escalated_conflicts: 0

# 资源指标
resources:
  avg_response_time_ms: 350
  peak_concurrent_tasks: 2
  idle_time_percentage: 15
```

---

## 5. 版本控制策略

### 5.1 语义化版本

```
MAJOR.MINOR.PATCH

MAJOR: 破坏性变更，需要协商
MINOR: 增强性变更，向后兼容
PATCH: 兼容性修复，自动适应
```

### 5.2 变更分类

| 变更类型 | 示例 | 处理方式 |
|----------|------|----------|
| PATCH | 修复bug、优化描述 | 自动适应 |
| MINOR | 新增能力、扩展接口 | 通知+适应 |
| MAJOR | 删除能力、修改接口 | 协商机制 |

### 5.3 兼容性矩阵

```yaml
# 示例：兼容性矩阵
compatibility_matrix:
  tech:
    "1.0.x":
      compatible_with:
        product: ">=1.0.0"
        marketing: ">=1.0.0"
    "2.0.0":
      breaking_changes:
        - "API接口重构"
      requires_negotiation:
        - product
        - marketing
```

---

## 6. 文档验证

### 6.1 JSON Schema 验证

所有YAML/JSON文件都应对应一个Schema：

```
shared/schemas/
├── constitution.schema.json
├── contract.schema.json
├── capabilities.schema.json
├── registry.schema.json
└── graph.schema.json
```

### 6.2 文档完整性检查

```yaml
# 每个子系统必须包含的文件
required_files:
  - SPEC.md
  - CONTRACT.yaml
  - CAPABILITIES.yaml
  - local-graph.json
  - state/goals.md
  - state/status.md
  - state/metrics.yaml
```

---

*文档版本: v1.0.0*
*最后更新: 2026-04-01*

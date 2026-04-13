# 03 - 知识图谱设计

> **版本**: v1.0.0
> **创建日期**: 2026-04-01

---

## 1. 知识图谱架构

### 1.1 分层设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          知识图谱分层架构                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        全局知识图谱                                  │    │
│  │   ┌─────────┐    ┌─────────┐    ┌─────────┐                        │    │
│  │   │ 公司    │───►│ 愿景    │───►│ 使命    │                        │    │
│  │   └────┬────┘    └─────────┘    └─────────┘                        │    │
│  │        │                                                            │    │
│  │        ▼                                                            │    │
│  │   ┌─────────┐                                                      │    │
│  │   │子系统关系│───► [tech] ───► [product] ───► [marketing]          │    │
│  │   └─────────┘         │             │              │                │    │
│  └────────────────────────┼─────────────┼──────────────┼────────────────┘    │
│                           │             │              │                     │
│                           ▼             ▼              ▼                     │
│              ┌────────────────┐ ┌────────────────┐ ┌────────────────┐        │
│              │  tech 图谱     │ │  product 图谱  │ │  marketing图谱 │        │
│              │                │ │                │ │                │        │
│              │ - API设计     │ │ - 用户画像     │ │ - 渠道策略     │        │
│              │ - 架构决策    │ │ - 功能规划     │ │ - 活动记录     │        │
│              │ - 代码模式    │ │ - 原型历史     │ │ - 转化数据     │        │
│              └────────────────┘ └────────────────┘ └────────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 图谱职责划分

| 层级 | 存储内容 | 更新频率 | 访问权限 |
|------|----------|----------|----------|
| 全局图谱 | 公司、子系统、核心关系 | 周/重大变更 | 所有子系统只读 |
| 子系统图谱 | 目标、任务、决策、知识 | 实时 | 子系统读写，其他只读 |

---

## 2. 全局知识图谱 Schema

### 2.1 Schema 定义

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GlobalKnowledgeGraph",
  "type": "object",

  "properties": {
    "metadata": {
      "type": "object",
      "properties": {
        "version": { "type": "string" },
        "updated_at": { "type": "string", "format": "date-time" },
        "root_namespace": { "type": "string" }
      },
      "required": ["version", "updated_at"]
    },

    "entities": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "type": {
            "type": "string",
            "enum": ["company", "subsystem", "capability", "goal", "resource", "event", "pattern"]
          },
          "name": { "type": "string" },
          "description": { "type": "string" },
          "properties": { "type": "object" },
          "created_at": { "type": "string", "format": "date-time" },
          "updated_at": { "type": "string", "format": "date-time" }
        },
        "required": ["id", "type", "name"]
      }
    },

    "relations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "type": {
            "type": "string",
            "enum": [
              "owns", "provides", "consumes", "depends_on",
              "implements", "collaborates_with", "reports_to",
              "triggers", "blocks", "supports", "breaks_down_to"
            ]
          },
          "source": { "type": "string" },
          "target": { "type": "string" },
          "properties": { "type": "object" },
          "weight": { "type": "number", "minimum": 0, "maximum": 1 }
        },
        "required": ["type", "source", "target"]
      }
    },

    "views": {
      "type": "object",
      "description": "预定义的图谱视图",
      "properties": {
        "organizational": {
          "type": "array",
          "items": { "type": "string" }
        },
        "capability": {
          "type": "array",
          "items": { "type": "string" }
        },
        "dataflow": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    }
  },
  "required": ["metadata", "entities", "relations"]
}
```

### 2.2 实体类型定义

| 实体类型 | 标识前缀 | 描述 | 示例属性 |
|----------|----------|------|----------|
| company | company | 公司实体 | mission, vision, founded |
| subsystem | subsystem.{id} | 子系统 | status, maturity, agent_id |
| capability | capability.{subsystem}.{name} | 能力 | owner, level, metrics |
| goal | goal.{subsystem}.{id} | 目标 | status, priority, deadline |
| resource | resource.{type}.{id} | 资源 | type, location, access_level |
| event | event.{type}.{id} | 事件 | timestamp, payload, source |
| pattern | pattern.{domain}.{name} | 模式 | applicability, effectiveness |

### 2.3 关系类型定义

| 关系类型 | 方向 | 描述 | 权重说明 |
|----------|------|------|----------|
| owns | A → B | A拥有B | 1.0 (固定) |
| provides | A → B | A提供服务B | 依赖重要性 |
| consumes | A → B | A消费服务B | 依赖频率 |
| depends_on | A → B | A依赖B | 依赖强度 |
| implements | A → B | A实现B | 1.0 (固定) |
| collaborates_with | A ↔ B | A与B协作 | 协作频率 |
| triggers | A → B | A触发B | 触发概率 |
| blocks | A → B | A阻塞B | 阻塞程度 |
| supports | A → B | A支持B | 支持重要性 |
| breaks_down_to | A → B | A分解为B | 1.0 (固定) |

---

## 3. 全局图谱示例

```json
{
  "metadata": {
    "version": "1.0.0",
    "updated_at": "2026-04-01T10:00:00Z",
    "root_namespace": "company"
  },

  "entities": [
    {
      "id": "company",
      "type": "company",
      "name": "AI软件服务公司",
      "description": "一人AI股份有限公司",
      "properties": {
        "mission": "通过AI Agent实现公司运营自动化",
        "vision": "成为AI驱动的软件服务标杆",
        "founded": "2026-03-01"
      },
      "created_at": "2026-03-01T00:00:00Z",
      "updated_at": "2026-04-01T00:00:00Z"
    },

    {
      "id": "subsystem.tech",
      "type": "subsystem",
      "name": "技术研发子系统",
      "description": "负责软件开发、技术架构、代码审查",
      "properties": {
        "status": "active",
        "maturity": "level-2",
        "agent_id": "tech-agent-001"
      },
      "created_at": "2026-03-15T00:00:00Z",
      "updated_at": "2026-04-01T10:00:00Z"
    },

    {
      "id": "subsystem.product",
      "type": "subsystem",
      "name": "产品设计子系统",
      "description": "负责需求分析、原型设计、用户体验",
      "properties": {
        "status": "active",
        "maturity": "level-1",
        "agent_id": "product-agent-001"
      },
      "created_at": "2026-03-15T00:00:00Z",
      "updated_at": "2026-04-01T09:00:00Z"
    },

    {
      "id": "capability.tech.api-design",
      "type": "capability",
      "name": "API设计能力",
      "description": "设计和定义RESTful/GraphQL API",
      "properties": {
        "owner": "subsystem.tech",
        "level": 2,
        "metrics": {
          "test_coverage": 0.82,
          "avg_response_time_ms": 350
        }
      },
      "created_at": "2026-03-20T00:00:00Z",
      "updated_at": "2026-04-01T10:00:00Z"
    },

    {
      "id": "goal.tech.api-auth",
      "type": "goal",
      "name": "完成用户认证API",
      "description": "实现账号密码和手机验证码登录",
      "properties": {
        "status": "in_progress",
        "priority": "P0",
        "deadline": "2026-04-03",
        "progress": 0.6
      },
      "created_at": "2026-04-01T08:00:00Z",
      "updated_at": "2026-04-01T10:30:00Z"
    }
  ],

  "relations": [
    {
      "id": "rel-001",
      "type": "owns",
      "source": "company",
      "target": "subsystem.tech",
      "weight": 1.0,
      "properties": {
        "since": "2026-03-15"
      }
    },

    {
      "id": "rel-002",
      "type": "owns",
      "source": "company",
      "target": "subsystem.product",
      "weight": 1.0
    },

    {
      "id": "rel-003",
      "type": "provides",
      "source": "subsystem.tech",
      "target": "capability.tech.api-design",
      "weight": 0.9,
      "properties": {
        "since": "2026-03-20"
      }
    },

    {
      "id": "rel-004",
      "type": "depends_on",
      "source": "subsystem.tech",
      "target": "subsystem.product",
      "weight": 0.7,
      "properties": {
        "dependency_type": "requirements",
        "frequency": "on-demand"
      }
    },

    {
      "id": "rel-005",
      "type": "implements",
      "source": "goal.tech.api-auth",
      "target": "capability.tech.api-design",
      "weight": 1.0
    }
  ],

  "views": {
    "organizational": [
      "company",
      "subsystem.tech",
      "subsystem.product",
      "subsystem.marketing",
      "subsystem.service",
      "subsystem.finance",
      "subsystem.operations"
    ],
    "capability": [
      "capability.tech.api-design",
      "capability.tech.code-review",
      "capability.product.requirements",
      "capability.product.prototype"
    ],
    "dataflow": [
      "subsystem.product -> subsystem.tech",
      "subsystem.tech -> subsystem.service",
      "subsystem.marketing -> subsystem.product"
    ]
  }
}
```

---

## 4. 子系统图谱设计

### 4.1 子系统图谱 Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SubsystemKnowledgeGraph",
  "type": "object",

  "properties": {
    "metadata": {
      "type": "object",
      "properties": {
        "version": { "type": "string" },
        "subsystem_id": { "type": "string" },
        "updated_at": { "type": "string", "format": "date-time" }
      }
    },

    "entities": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "type": {
            "type": "string",
            "enum": ["goal", "task", "decision", "pattern", "learning", "resource"]
          },
          "name": { "type": "string" },
          "properties": { "type": "object" }
        }
      }
    },

    "relations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "enum": [
              "breaks_down_to", "depends_on", "blocks",
              "supports", "learns_from", "applies"
            ]
          },
          "source": { "type": "string" },
          "target": { "type": "string" }
        }
      }
    }
  }
}
```

### 4.2 子系统图谱示例 (tech)

```json
{
  "metadata": {
    "version": "1.0.0",
    "subsystem_id": "tech",
    "updated_at": "2026-04-01T10:30:00Z"
  },

  "entities": [
    {
      "id": "tech.goal.api-auth",
      "type": "goal",
      "name": "完成用户认证API",
      "properties": {
        "status": "in_progress",
        "priority": "P0",
        "deadline": "2026-04-03",
        "progress": 0.6,
        "source": "external_directive"
      }
    },

    {
      "id": "tech.task.design-api",
      "type": "task",
      "name": "设计认证API接口",
      "properties": {
        "status": "completed",
        "assignee": "tech-agent-001",
        "started_at": "2026-04-01T08:00:00Z",
        "completed_at": "2026-04-01T08:45:00Z"
      }
    },

    {
      "id": "tech.task.impl-password",
      "type": "task",
      "name": "实现账号密码认证",
      "properties": {
        "status": "completed",
        "assignee": "tech-agent-001"
      }
    },

    {
      "id": "tech.task.impl-sms",
      "type": "task",
      "name": "实现手机验证码认证",
      "properties": {
        "status": "in_progress",
        "assignee": "tech-agent-001"
      }
    },

    {
      "id": "tech.decision.use-jwt",
      "type": "decision",
      "name": "使用JWT进行认证",
      "properties": {
        "made_at": "2026-04-01T08:30:00Z",
        "made_by": "tech-agent-001",
        "rationale": "无状态、可扩展、适合分布式系统",
        "alternatives_considered": ["session-based", "oauth-only"]
      }
    },

    {
      "id": "tech.pattern.jwt-auth",
      "type": "pattern",
      "name": "JWT认证模式",
      "properties": {
        "applicability": "需要无状态认证的API",
        "effectiveness": 0.9,
        "usage_count": 3
      }
    },

    {
      "id": "tech.learning.field-permission",
      "type": "learning",
      "name": "字段级权限控制",
      "properties": {
        "learned_at": "2026-04-01T09:00:00Z",
        "context": "API响应包含敏感字段",
        "insight": "最小权限原则适用于所有API响应"
      }
    }
  ],

  "relations": [
    {
      "type": "breaks_down_to",
      "source": "tech.goal.api-auth",
      "target": "tech.task.design-api"
    },
    {
      "type": "breaks_down_to",
      "source": "tech.goal.api-auth",
      "target": "tech.task.impl-password"
    },
    {
      "type": "breaks_down_to",
      "source": "tech.goal.api-auth",
      "target": "tech.task.impl-sms"
    },
    {
      "type": "supports",
      "source": "tech.decision.use-jwt",
      "target": "tech.task.impl-password"
    },
    {
      "type": "applies",
      "source": "tech.task.impl-password",
      "target": "tech.pattern.jwt-auth"
    },
    {
      "type": "learns_from",
      "source": "tech.learning.field-permission",
      "target": "tech.task.design-api"
    }
  ]
}
```

---

## 5. 图谱操作API

### 5.1 查询接口

```typescript
// 图谱查询接口

interface GraphQuery {
  // 按ID获取实体
  getEntity(id: string): Promise<Entity | null>;

  // 按类型获取实体列表
  getEntitiesByType(type: EntityType): Promise<Entity[]>;

  // 获取实体的所有关系
  getRelations(entityId: string, direction?: 'in' | 'out' | 'both'): Promise<Relation[]>;

  // 路径查询
  findPath(fromId: string, toId: string, maxDepth?: number): Promise<Entity[][]>;

  // 子图查询
  getSubgraph(rootId: string, depth: number): Promise<{entities: Entity[], relations: Relation[]}>;

  // 模式匹配
  matchPattern(pattern: GraphPattern): Promise<{entities: Entity[], relations: Relation[]}>;
}

interface GraphPattern {
  entities: {
    variable: string;
    type?: EntityType;
    properties?: Record<string, any>;
  }[];
  relations: {
    from: string;
    to: string;
    type?: RelationType;
  }[];
}
```

### 5.2 更新接口

```typescript
// 图谱更新接口

interface GraphUpdate {
  // 添加实体
  addEntity(entity: Omit<Entity, 'id' | 'created_at' | 'updated_at'>): Promise<Entity>;

  // 更新实体
  updateEntity(id: string, properties: Record<string, any>): Promise<Entity>;

  // 删除实体（同时删除相关关系）
  deleteEntity(id: string): Promise<void>;

  // 添加关系
  addRelation(relation: Omit<Relation, 'id'>): Promise<Relation>;

  // 删除关系
  deleteRelation(id: string): Promise<void>;

  // 批量操作
  batch(operations: GraphOperation[]): Promise<void>;
}

type GraphOperation =
  | { type: 'add_entity'; data: Entity }
  | { type: 'update_entity'; id: string; data: Partial<Entity> }
  | { type: 'delete_entity'; id: string }
  | { type: 'add_relation'; data: Relation }
  | { type: 'delete_relation'; id: string };
```

### 5.3 查询示例

```typescript
// 查询示例

// 1. 获取所有子系统
const subsystems = await graph.getEntitiesByType('subsystem');

// 2. 查询tech子系统的所有能力
const techCapabilities = await graph.matchPattern({
  entities: [
    { variable: 'tech', type: 'subsystem', properties: { id: 'subsystem.tech' } },
    { variable: 'cap', type: 'capability' }
  ],
  relations: [
    { from: 'tech', to: 'cap', type: 'provides' }
  ]
});

// 3. 查找从product到tech的依赖路径
const path = await graph.findPath('subsystem.product', 'subsystem.tech');

// 4. 获取goal及其所有子任务
const goalSubgraph = await graph.getSubgraph('tech.goal.api-auth', 2);
```

---

## 6. 子系统注册表

### 6.1 注册表结构

```json
{
  "$schema": "./shared/schemas/registry.json",
  "version": "1.0.0",
  "updated_at": "2026-04-01T10:00:00Z",

  "subsystems": [
    {
      "id": "tech",
      "name": "技术研发子系统",
      "path": "./subsystems/tech/",
      "status": "active",
      "version": "1.0.0",

      "agent": {
        "type": "claude-code",
        "instance_id": "tech-agent-001",
        "last_heartbeat": "2026-04-01T10:29:00Z"
      },

      "capabilities": [
        "api-design",
        "code-review",
        "database-design"
      ],

      "provides": [
        {
          "service": "api-design",
          "version": "1.0.0",
          "endpoint": "negotiate"
        }
      ],

      "consumes": [
        {
          "service": "requirements",
          "provider": "product",
          "version": ">=1.0.0"
        }
      ],

      "metrics": {
        "tasks_completed": 8,
        "avg_response_time_ms": 350,
        "satisfaction_rate": 0.95
      }
    }
  ],

  "service_index": {
    "api-design": ["tech"],
    "requirements": ["product"],
    "marketing-plan": ["marketing"],
    "customer-support": ["service"]
  },

  "dependency_graph": {
    "tech": ["product"],
    "product": ["marketing"],
    "marketing": [],
    "service": ["tech", "product"],
    "finance": [],
    "operations": ["*"]
  }
}
```

### 6.2 能力发现服务

```typescript
// 能力发现服务

interface CapabilityDiscovery {
  // 按能力名称查找提供者
  findByCapability(capability: string): Promise<Subsystem[]>;

  // 按服务需求查找
  findByRequirement(requirement: ServiceRequirement): Promise<SubsystemMatch[]>;

  // 获取子系统依赖链
  getDependencyChain(subsystemId: string): Promise<Subsystem[]>;

  // 检查兼容性
  checkCompatibility(consumer: string, provider: string, service: string): Promise<CompatibilityResult>;
}

interface SubsystemMatch {
  subsystem: Subsystem;
  score: number;        // 匹配分数 0-1
  availability: number; // 可用性
  estimated_response: string; // 预计响应时间
}
```

---

## 7. 图谱缓存与同步

### 7.1 缓存策略

```yaml
# 缓存配置
cache_config:
  # 全局图谱
  global_graph:
    ttl_seconds: 300        # 5分钟缓存
    refresh_on_change: true # 文件变更时刷新

  # 子系统图谱
  subsystem_graph:
    ttl_seconds: 60         # 1分钟缓存
    refresh_on_change: true

  # 注册表
  registry:
    ttl_seconds: 600        # 10分钟缓存
    refresh_on_change: true
```

### 7.2 同步机制

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          图谱同步机制                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   文件变更事件          缓存更新             通知订阅者                      │
│   ─────────────        ─────────────        ─────────────                   │
│                                                                              │
│   global-graph.json ──► 清除全局缓存 ──► 通知所有子系统                     │
│                                                                              │
│   tech/local-graph.json ──► 清除tech缓存 ──► 通知相关子系统                 │
│                                                                              │
│   _registry.json ──► 清除注册表缓存 ──► 通知所有子系统                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*文档版本: v1.0.0*
*最后更新: 2026-04-01*

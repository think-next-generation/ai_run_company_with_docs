# LLM Wiki 集成设计 - 知识飞轮系统

> **版本**: 1.0.0
> **创建日期**: 2026-04-13
> **状态**: Draft

---

## 1. 背景与目标

### 1.1 现有系统

公司运营系统使用 `global-graph.json` 描述组织结构：
- **实体类型**：company, subsystem, capability, goal, task, resource, event, pattern, decision, learning
- **关系类型**：owns, provides, depends_on, collaborates_with, triggers, supports, breaks_down_to, learns_from, applies
- **用途**：组织架构、职责边界、目标追踪

### 1.2 集成目标

将 llm-wiki 作为公司运营的核心知识引擎，实现：

1. **双图谱并行查询** — 查询组织图谱 + 知识图谱 → LLM 整合答案
2. **知识自动沉淀** — 重要任务完成后自动沉淀 + 知识缺口时提示沉淀
3. **决策与度量追踪** — 新增 decision, metric 实体类型

---

## 2. 架构设计

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Knowledge Engine                        │
│                    (统一查询入口)                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Query Router                        │   │
│  │     并行查询 → 结果整合 → 返回结构化答案               │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│           ┌─────────────┴─────────────┐                     │
│           ▼                           ▼                     │
│  ┌─────────────────────┐    ┌─────────────────────┐         │
│  │ Organization Graph  │    │     LLM Wiki         │         │
│  │  (global-graph.json)│    │   (知识沉淀+查询)     │         │
│  └─────────────────────┘    └─────────────────────┘         │
│           │                           │                     │
│           ▼                           ▼                     │
│  - entity: company            - Raw Sources               │
│  - entity: subsystem          - Wiki Pages                │
│  - entity: capability         - Knowledge Graph            │
│  - entity: goal                                            │
│  - entity: resource                                        │
│  - entity: decision ◄新                                    │
│  - entity: metric ◄新                                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 职责 | 位置 |
|------|------|------|
| Knowledge Engine | 统一查询入口，并行调用双图谱 | `.system/lib/graph/` |
| Query Router | 解析意图，分发查询，整合结果 | 同上 |
| Wiki Ingest | 知识沉淀触发与执行 | 同上 |
| Organization Graph | 组织图谱存储与查询 | `global-graph.json` |
| LLM Wiki | 外部依赖，文档知识存储 | 独立安装 |

---

## 3. 实体扩展

### 3.1 新增实体类型

在 `global-graph.json` 中新增：

```json
{
  "id": "decision.2026.001",
  "type": "decision",
  "name": "采用双图谱并行查询方案",
  "properties": {
    "category": "technical",
    "status": "approved",
    "decided_at": "2026-04-13",
    "decided_by": "human",
    "alternatives_considered": ["松散耦合", "分层架构"],
    "rationale": "提供最佳用户体验，单一入口"
  },
  "tags": ["architecture", "knowledge"],
  "created_at": "2026-04-13T00:00:00Z",
  "updated_at": "2026-04-13T00:00:00Z"
}
```

```json
{
  "id": "metric.task-completion-rate",
  "type": "metric",
  "name": "任务完成率",
  "properties": {
    "category": "performance",
    "unit": "percentage",
    "current_value": 85,
    "target_value": 90,
    "measured_at": "2026-04-13",
    "frequency": "weekly"
  },
  "tags": ["kpi", "tasks"],
  "created_at": "2026-04-13T00:00:00Z",
  "updated_at": "2026-04-13T00:00:00Z"
}
```

### 3.2 实体类型枚举扩展

更新 `graph.schema.json`：

```json
"type": {
  "enum": [
    "company",
    "subsystem",
    "capability",
    "goal",
    "task",
    "resource",
    "event",
    "pattern",
    "decision",      // 新增
    "metric",        // 新增
    "learning"
  ]
}
```

---

## 4. 查询接口设计

### 4.1 统一查询 API

```python
class KnowledgeEngine:
    """统一知识查询入口"""

    async def query(self, question: str) -> QueryResult:
        """并行查询双图谱，返回整合结果"""
        # 1. 并行查询
        org_task = self.query_organization_graph(question)
        wiki_task = self.query_llm_wiki(question)

        org_result, wiki_result = await asyncio.gather(org_task, wiki_task)

        # 2. LLM 整合
        integrated = await self.integrate_results(question, org_result, wiki_result)

        return QueryResult(
            answer=integrated.answer,
            sources={
                "organization": org_result.sources,
                "wiki": wiki_result.sources
            },
            confidence=integrated.confidence
        )
```

### 4.2 查询示例

**问题**: "财务子系统当前目标是什么？"

```python
# Organization Graph 查询
result = query_graph("财务 子系统 目标", types=["goal", "subsystem"])
# 返回: subsystem.财务 → goal.company.q2-financial-report

# LLM Wiki 查询
result = query_wiki("财务 子系统 目标")
# 返回: 相关文档页面

# LLM 整合
"财务子系统目前有两个目标：
1. 完成 Q2 财务报告（目标 ID: goal.company.q2-financial-report）
2. 优化报销流程（参考文档: financial_process_optimization.md）"
```

---

## 5. 知识沉淀机制

### 5.1 沉淀触发规则

| 触发条件 | 沉淀内容 | 确认方式 |
|---------|---------|---------|
| 任务完成（重要） | 任务流程、决策、结果 | 自动 |
| 发现知识缺口 | 相关调研结果 | 提示确认 |
| 人工确认 | 任意内容 | 手动触发 |

### 5.2 沉淀流程

```
任务完成
    │
    ▼
判断是否为"重要任务"？
    │
    ├── 否 → 不沉淀
    │
    └── 是 → 生成沉淀内容
              │
              ▼
         自动写入 LLM Wiki
         (Raw Sources + Wiki Pages)
```

### 5.3 知识缺口发现

```
Agent 查询知识
    │
    ▼
无相关结果 或 结果不足
    │
    ▼
标记"知识缺口"
    │
    ▼
提示 Agent: "是否需要沉淀此知识？"
    │
    ├── 否 → 忽略
    │
    └── 是 → 触发 Ingest
```

---

## 6. 人类独立使用

两个系统均可被人类独立使用和维护。

### 6.1 Organization Graph（组织图谱）

**用途**：查询和修改公司组织结构、职责、能力、目标

**查询方式**：
```bash
# 直接读取 JSON 文件
cat company-ops/global-graph.json

# 或使用 jq 查询
jq '.entities[] | select(.type=="subsystem")' company-ops/global-graph.json

# 查询特定实体
jq '.entities[] | select(.id=="subsystem.财务")' company-ops/global-graph.json

# 查询关系
jq '.relations[] | select(.source=="company")' company-ops/global-graph.json
```

**修改方式**：
- 直接编辑 `global-graph.json`
- 遵循 `graph.schema.json` 验证

**使用示例**：
```
问题："我们有哪些子系统？"
操作：jq '.entities[] | select(.type=="subsystem") | .name' global-graph.json
返回：["财务管理子系统", "法务合规子系统", "产品线容器"]
```

### 6.2 LLM Wiki（知识图谱）

**安装与启动**：

```bash
# 方式 1：桌面应用（推荐）
# 下载 https://github.com/nashsu/llm_wiki/releases
# 解压后运行 .app

# 方式 2：Docker
docker run -d -p 3000:3000 -v ~/llm-wiki:/app/data nashsu/llm-wiki

# 方式 3：CLI（适用于自动化）
npm install -g llm-wiki-cli
llm-wiki init ~/company-wiki
```

**使用流程**：

```
1. 启动应用
   → 打开 http://localhost:3000

2. 配置 LLM
   → Settings → 选择 OpenAI / Anthropic / 本地模型

3. 导入知识源
   → Sources → 添加文件夹/文件
   → 点击 "Ingest" 开始构建 Wiki

4. 查询知识
   → 输入问题 → LLM 从 Wiki 中提取答案

5. 维护 Wiki
   → Review → 审核 LLM 生成的内容
   → Lint → 清理和优化链接
```

**核心操作**：

| 操作 | 命令/操作 | 说明 |
|------|---------|------|
| Ingest | `llm-wiki ingest <folder>` | 摄入文档，生成 Wiki |
| Query | `llm-wiki query "<question>"` | 查询知识 |
| Lint | `llm-wiki lint` | 清理死链接和维护 |
| Review | Web UI → Review | 人工审核生成内容 |
| Graph | Web UI → Graph | 可视化知识图谱 |

### 6.3 统一知识查询

当两个系统都可用时，Agent 可以使用统一查询：

```python
from knowledge_engine import KnowledgeEngine

engine = KnowledgeEngine()

# 统一查询
result = await engine.query("如何报销差旅费用？")

# 返回格式
# {
#   "answer": "差旅报销流程如下...",
#   "sources": {
#     "organization": [...],  // 来自组织图谱
#     "wiki": [...]          // 来自 Wiki
#   }
# }
```

---

## 7. 实现计划

### Phase 1：基础设施

1. 安装 llm-wiki CLI 到本地
2. 扩展 graph.schema.json（添加 decision, metric）
3. 更新 global-graph.json 实体定义

### Phase 2：查询接口

1. 创建 `.system/lib/graph/knowledge_engine.py`
2. 实现 Query Router
3. 实现双图谱并行查询

### Phase 3：知识沉淀

1. 实现自动沉淀触发器
2. 实现知识缺口检测
3. 配置沉淀确认流程

---

## 8. 技术约束

### 8.1 安装方式选择

| 方式 | CLI | 桌面应用 | 说明 |
|------|-----|---------|------|
| **nashsu/llm_wiki** | ⚠️ 无独立CLI | ✅ 完整功能 | 桌面应用，可命令行调用 |
| **sdyckjq-lab/llm-wiki-skill** | ✅ Claude Code Skill | ❌ | 可嵌入 Claude Code |
| **Karpathy 原版** | ✅ 纯文本 | ❌ | 需要 LLM 交互 |

**推荐方案**：安装 nashsu/llm_wiki 桌面应用，同时提供 CLI 封装

- 桌面应用支持 `--headless` 模式或 API 调用
- 用于自动化时可通过命令行触发 ingest/query
- 保留 GUI 供人类独立使用和维护

### 8.2 技术要求

- llm-wiki 桌面应用提供 HTTP API（默认端口 3000）
- 或通过命令行调用：`llm-wiki-cli ingest/query/lint`
- 查询需要 LLM 调用（有成本）
- 知识沉淀需要额外 LLM 调用

---

## 9. 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| LLM 调用成本高 | 增量缓存 + 预算控制 |
| 双图谱查询延迟 | 并行执行 + 超时控制 |
| 知识质量 | 人工审核流程 |
| 集成复杂度 | 渐进式实现 |

---

## 10. 验收标准

- [ ] 双图谱并行查询正常工作
- [ ] 查询结果可被 LLM 正确整合
- [ ] 重要任务完成后自动沉淀
- [ ] 知识缺口可被检测和提示
- [ ] decision 和 metric 实体可正常存储和查询
- [ ] 与现有工作流无缝集成
- [ ] 人类可独立使用两个系统
- [ ] 统一查询示例可用

---

*文档版本: 1.0.0*
*创建日期: 2026-04-13*

# LLM Wiki 集成设计 - 知识飞轮系统

> **版本**: 2.0.0
> **创建日期**: 2026-04-13
> **更新日期**: 2026-04-13
> **状态**: 已完成

---

## 1. 背景与目标

### 1.1 现有系统

公司运营系统使用 `global-graph.json` 描述组织结构：
- **实体类型**：company, subsystem, capability, goal, task, resource, event, pattern, decision, learning
- **关系类型**：owns, provides, depends_on, collaborates_with, triggers, supports, breaks_down_to, learns_from, applies
- **用途**：组织架构、职责边界、目标追踪

### 1.2 集成目标

将 LLM Wiki 作为公司运营的核心知识引擎，实现：

1. **双图谱并行查询** — 查询组织图谱 + 知识图谱 → LLM 整合答案
2. **知识自动沉淀** — 重要任务完成后自动沉淀 + 知识缺口时提示沉淀
3. **决策与度量追踪** — 新增 decision, metric 实体类型

### 1.3 技术选型变更

经过调研，发现 **Hermes Agent 的 llm-wiki skill** 更适合我们的需求：

| 特性 | Hermes llm-wiki | nashsu/llm_wiki |
|------|----------------|-----------------|
| **依赖** | 纯 Markdown 文件 | 桌面应用 + 数据库 |
| **部署** | 零依赖，即插即用 | 需要安装运行 |
| **集成** | Claude Code Skill | 需 API 调用 |
| **来源** | NousResearch/hermes-agent | 独立项目 |

**参考项目**：https://github.com/NousResearch/hermes-agent/tree/main/skills/research/llm-wiki

---

## 2. 架构设计

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Knowledge Engine                        │
│                    (统一查询入口)                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Query Router                       │   │
│  │     并行查询 → 结果整合 → 返回结构化答案              │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│           ┌─────────────┴─────────────┐                     │
│           ▼                           ▼                     │
│  ┌─────────────────────┐    ┌─────────────────────┐         │
│  │ Organization Graph │    │    LLM Wiki         │         │
│  │  (global-graph.json)│    │ (company-ops/wiki/) │         │
│  └─────────────────────┘    └─────────────────────┘         │
│           │                           │                     │
│           ▼                           ▼                     │
│  - entity: company            - raw/sources               │
│  - entity: subsystem          - entities/                 │
│  - entity: capability         - concepts/                  │
│  - entity: goal              - comparisons/                │
│  - entity: resource          - queries/                    │
│  - entity: decision ◄新       - SCHEMA.md                  │
│  - entity: metric ◄新        - index.md                   │
│                                - log.md                     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Wiki 目录结构

基于 Karpathy 的 LLM Wiki 方法论：

```
company-ops/wiki/
├── SCHEMA.md              # 约定、规则、标签分类
├── index.md               # 内容目录（每页一行摘要）
├── log.md                 # 操作日志（追加写）
├── raw/                   # Layer 1: 原始资料（不可变）
│   ├── articles/          # 网络文章
│   ├── papers/            # 论文
│   ├── transcripts/       # 会议记录
│   └── assets/            # 图片素材
├── entities/              # Layer 2: 实体页（人物、组织、产品）
├── concepts/             # Layer 2: 概念页
├── comparisons/          # Layer 2: 对比分析
├── queries/              # Layer 2: 保存的查询结果
└── _archive/             # 归档页
```

### 2.3 核心组件

| 组件 | 职责 | 位置 |
|------|------|------|
| Knowledge Engine | 统一查询入口，并行调用双图谱 | `.system/lib/graph/` |
| Query Router | 解析意图，分发查询，整合结果 | 同上 |
| Wiki Ingest | 知识沉淀触发与执行 | 同上 |
| Organization Graph | 组织图谱存储与查询 | `global-graph.json` |
| LLM Wiki Skill | 文件驱动的知识引擎 | Claude Code Skill |

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
    "decision",
    "metric",
    "learning"
  ]
}
```

---

## 4. Wiki Skill 安装

### 4.1 安装步骤

从 NousResearch/hermes-agent 复制 llm-wiki skill 到公司运营系统：

```bash
# 1. 创建 skills 目录（如果不存在）
mkdir -p company-ops/.claude/skills

# 2. 复制 llm-wiki skill
cp -r <hermes-agent-repo>/skills/research/llm-wiki company-ops/.claude/skills/

# 3. 或创建符号链接（推荐，便于更新）
ln -s <hermes-agent-repo>/skills/research/llm-wiki company-ops/.claude/skills/llm-wiki
```

### 4.2 配置

在 `company-ops/CLAUDE.md` 或 `~/.claude/settings.json` 中配置：

```yaml
skills:
  config:
    wiki:
      path: ~/project/company-ops/wiki
```

### 4.3 初始化 Wiki

首次使用需要初始化 Wiki 结构：

```bash
# 创建目录结构
mkdir -p wiki/{raw/{articles,papers,transcripts,assets},entities,concepts,comparisons,queries,_archive}

# 创建核心文件
touch wiki/SCHEMA.md wiki/index.md wiki/log.md
```

---

## 5. 查询接口设计

### 5.1 统一查询 API

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

### 5.2 查询示例

**问题**: "财务子系统当前目标是什么？"

```python
# Organization Graph 查询
result = query_graph("财务 子系统 目标", types=["goal", "subsystem"])
# 返回: subsystem.财务 → goal.company.q2-financial-report

# LLM Wiki 查询
result = query_wiki("财务 子系统 目标")
# 返回: 相关 Wiki 页面

# LLM 整合
"财务子系统目前有两个目标：
1. 完成 Q2 财务报告（目标 ID: goal.company.q2-financial-report）
2. 优化报销流程（参考文档: financial-process-optimization.md）"
```

---

## 6. Wiki 核心操作

### 6.1 Ingest（摄入）

当用户提供文档时：

1. **捕获原始文档**
   - 保存到 `raw/articles/` 或 `raw/papers/`
   - 命名要有意义：`raw/articles/财务报销流程-2026.md`

2. **检查现有内容**
   - 搜索 `index.md` 和现有页面
   - 避免重复创建

3. **创建/更新 Wiki 页面**
   - 新实体/概念：创建页面
   - 已有内容：更新并更新 `updated` 日期
   - 添加 `[[wikilinks]]` 交叉引用

4. **更新导航**
   - 添加新页面到 `index.md`
   - 追加到 `log.md`

### 6.2 Query（查询）

当用户询问 Wiki 相关问题时：

1. 读取 `index.md` 找到相关页面
2. 读取相关 Wiki 页面
3. LLM 综合答案
4. 有价值的答案保存到 `queries/`

### 6.3 Lint（清理）

定期检查 Wiki 健康度：

- 孤立页面（无 inbound 链接）
- 死链接（指向不存在的页面）
- 过期内容（90天未更新）
- 矛盾内容
- 页面大小（>200行需拆分）

---

## 7. 知识沉淀机制

### 7.1 沉淀触发规则

| 触发条件 | 沉淀内容 | 确认方式 |
|---------|---------|---------|
| 任务完成（重要） | 任务流程、决策、结果 | 自动 |
| 发现知识缺口 | 相关调研结果 | 提示确认 |
| 人工确认 | 任意内容 | 手动触发 |

### 7.2 沉淀流程

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
         写入 LLM Wiki
         (raw/ + entities/ + concepts/)
```

### 7.3 知识缺口发现

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
提示: "是否需要沉淀此知识？"
    │
    ├── 否 → 忽略
    │
    └── 是 → 触发 Ingest
```

---

## 8. 人类独立使用

两个系统均可被人类独立使用和维护。

### 8.1 Organization Graph（组织图谱）

**查询方式**：
```bash
# 直接读取 JSON 文件
cat company-ops/global-graph.json

# 使用 jq 查询
jq '.entities[] | select(.type=="subsystem")' company-ops/global-graph.json
```

**修改方式**：直接编辑 `global-graph.json`

### 8.2 LLM Wiki（知识图谱）

**初始化新 Wiki**：
```bash
# 1. 创建目录结构
mkdir -p wiki/{raw/{articles,papers,transcripts,assets},entities,concepts,comparisons,queries,_archive}

# 2. 初始化 SCHEMA.md
cat > wiki/SCHEMA.md << 'EOF'
# Wiki Schema

## Domain
公司运营知识库

## Conventions
- 文件名：小写字母、连字符、无空格
- 每个页面以 YAML frontmatter 开头
- 使用 [[wikilinks]] 链接页面
- 更新时必须修改 updated 日期
- 每个操作追加到 log.md
EOF

# 3. 初始化 index.md
cat > wiki/index.md << 'EOF'
# Wiki Index

> 内容目录。每页一行摘要。
EOF

# 4. 初始化 log.md
cat > wiki/log.md << 'EOF'
# Wiki Log

> 操作日志
EOF
```

**使用流程**：

```
1. Ingest（摄入）
   → 提供文档 URL 或文件
   → 自动生成 Wiki 页面

2. Query（查询）
   → 输入问题
   → 从 Wiki 综合答案

3. Lint（清理）
   → 检查孤立页面、死链接
   → 报告问题
```

**Obsidian 集成**：
- Wiki 目录可直接作为 Obsidian vault
- 支持 `[[wikilinks]]`、Graph View、Dataview

### 8.3 统一知识查询

当两个系统都可用时：

```python
from knowledge_engine import KnowledgeEngine

engine = KnowledgeEngine()

# 统一查询
result = await engine.query("如何报销差旅费用？")

# 返回格式
# {
#   "answer": "差旅报销流程如下...",
#   "sources": {
#     "organization": [...],
#     "wiki": [...]
#   }
# }
```

---

## 9. 实现计划

### Phase 1：基础设施

1. 从 Hermes Agent 复制 llm-wiki skill
2. 初始化 `company-ops/wiki/` 目录结构
3. 扩展 graph.schema.json（添加 decision, metric）
4. 更新 global-graph.json 实体定义

### Phase 2：查询接口

1. 创建 `.system/lib/graph/knowledge_engine.py`
2. 实现 Query Router
3. 实现双图谱并行查询

### Phase 3：知识沉淀

1. 实现自动沉淀触发器
2. 实现知识缺口检测
3. 配置沉淀确认流程

---

## 10. 技术要求

- **Wiki Skill**：来自 NousResearch/hermes-agent
- **存储**：纯文件系统，零依赖
- **查询**：需要 LLM 调用
- **知识沉淀**：需要 LLM 调用
- **可与 Obsidian 集成**：直接作为 vault 使用

---

## 11. 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| LLM 调用成本高 | 增量缓存 + 预算控制 |
| 双图谱查询延迟 | 并行执行 + 超时控制 |
| 知识质量 | 人工审核流程 |
| 集成复杂度 | 渐进式实现 |

---

## 12. 验收标准

- [x] llm-wiki skill 已安装
- [x] Wiki 目录结构正确初始化（~/wiki/）
- [ ] 双图谱并行查询正常工作
- [ ] 查询结果可被 LLM 正确整合
- [ ] 重要任务完成后自动沉淀
- [ ] 知识缺口可被检测和提示
- [x] decision 和 metric 实体类型已定义
- [ ] 与现有工作流无缝集成
- [x] 人类可独立使用两个系统
- [ ] 统一查询示例可用

---

*文档版本: 2.0.0*
*创建日期: 2026-04-13*
*更新日期: 2026-04-13*

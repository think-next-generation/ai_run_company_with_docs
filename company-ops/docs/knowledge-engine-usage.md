# Knowledge Engine Usage Guide

## Quick Start

### Query Knowledge

```bash
cd company-ops
python .system/lib/graph/query_knowledge.py "财务 子系统"
```

### Programmatic Usage

```python
from knowledge_engine import KnowledgeEngine
import asyncio

async def query():
    engine = KnowledgeEngine()
    result = await engine.query("Claude Code")
    print(result.answer)
    print("Sources:", result.sources)

asyncio.run(query())
```

### Knowledge Accumulation

```python
from accumulator import KnowledgeAccumulator

acc = KnowledgeAccumulator()

# Auto-accumulate based on priority
result = acc.accumulate_task_result(
    task_title="完成财务报告",
    task_result="生成了 Q2 财务报告，包含收入、支出、利润分析",
    priority="high",
    tags=["finance", "report"],
    entities=["财务部", "Q2"],
    concepts=["财务报表", "利润分析"]
)

print(result)
```

## Configuration

- Organization Graph: `company-ops/global-graph.json`
- Wiki: `~/wiki/`

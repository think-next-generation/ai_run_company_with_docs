# Knowledge Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement dual-graph parallel query and knowledge accumulation system combining Organization Graph (global-graph.json) with LLM Wiki (~/wiki/).

**Architecture:**
- KnowledgeEngine class as unified query entry point
- Parallel async queries to both Organization Graph and LLM Wiki
- LLM-powered result integration via Claude Code
- File-based wiki operations (Ingest/Query/Lint) following Hermes Agent's llm-wiki skill

**Tech Stack:** Python 3, asyncio, Claude Code (for LLM integration), file I/O

---

## File Structure

```
company-ops/.system/lib/graph/
├── __init__.py           # Already exists
├── parser.py             # Already exists - graph parsing
├── index.py              # Already exists - graph indexing
├── query.py              # Already exists - basic graph queries
├── update.py             # Already exists - graph updates
├── cache.py              # Already exists - caching
├── knowledge_engine.py   # NEW - unified query entry point
├── wiki_client.py        # NEW - LLM Wiki operations
└── integration.py       # NEW - dual-graph integration
```

---

## Task 1: Create Wiki Client Module

**Files:**
- Create: `company-ops/.system/lib/graph/wiki_client.py`
- Test: `company-ops/.system/tests/test_wiki_client.py`

- [ ] **Step 1: Write the failing test**

```python
# company-ops/.system/tests/test_wiki_client.py
import pytest
import os

WIKI_PATH = os.path.expanduser("~/wiki")

def test_wiki_path_exists():
    """Wiki directory should exist at ~/wiki"""
    assert os.path.isdir(WIKI_PATH)

def test_wiki_schema_exists():
    """SCHEMA.md should exist"""
    schema_path = os.path.join(WIKI_PATH, "SCHEMA.md")
    assert os.path.isfile(schema_path)

def test_wiki_index_exists():
    """index.md should exist"""
    index_path = os.path.join(WIKI_PATH, "index.md")
    assert os.path.isfile(index_path)

def test_wiki_log_exists():
    """log.md should exist"""
    log_path = os.path.join(WIKI_PATH, "log.md")
    assert os.path.isfile(log_path)

def test_wiki_directories_exist():
    """All required directories should exist"""
    required_dirs = ["raw", "entities", "concepts", "comparisons", "queries"]
    for dir_name in required_dirs:
        dir_path = os.path.join(WIKI_PATH, dir_name)
        assert os.path.isdir(dir_path), f"Directory {dir_name} should exist"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd company-ops && python -m pytest .system/tests/test_wiki_client.py -v`
Expected: FAIL (file doesn't exist yet)

- [ ] **Step 3: Write minimal implementation**

```python
# company-ops/.system/lib/graph/wiki_client.py
"""Wiki Client - LLM Wiki operations following Hermes Agent's llm-wiki skill"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class WikiClient:
    """Client for LLM Wiki operations"""
    
    def __init__(self, wiki_path: str = "~/wiki"):
        self.wiki_path = Path(os.path.expanduser(wiki_path))
    
    @property
    def schema_path(self) -> Path:
        return self.wiki_path / "SCHEMA.md"
    
    @property
    def index_path(self) -> Path:
        return self.wiki_path / "index.md"
    
    @property
    def log_path(self) -> Path:
        return self.wiki_path / "log.md"
    
    @property
    def raw_path(self) -> Path:
        return self.wiki_path / "raw"
    
    @property
    def entities_path(self) -> Path:
        return self.wiki_path / "entities"
    
    @property
    def concepts_path(self) -> Path:
        return self.wiki_path / "concepts"
    
    def read_schema(self) -> str:
        """Read SCHEMA.md to understand conventions"""
        if self.schema_path.exists():
            return self.schema_path.read_text()
        return ""
    
    def read_index(self) -> str:
        """Read index.md to find relevant pages"""
        if self.index_path.exists():
            return self.index_path.read_text()
        return ""
    
    def read_log(self, lines: int = 30) -> str:
        """Read recent log entries"""
        if self.log_path.exists():
            content = self.log_path.read_text()
            log_lines = content.split("\n")
            return "\n".join(log_lines[-lines:])
        return ""
    
    def search_pages(self, query: str) -> List[Dict]:
        """Search wiki pages for query string"""
        results = []
        search_lower = query.lower()
        
        # Search in entities, concepts, comparisons, queries
        for subdir in ["entities", "concepts", "comparisons", "queries"]:
            dir_path = self.wiki_path / subdir
            if dir_path.exists():
                for md_file in dir_path.glob("*.md"):
                    content = md_file.read_text().lower()
                    if search_lower in content:
                        results.append({
                            "path": str(md_file),
                            "type": subdir[:-1],  # remove 's'
                            "title": md_file.stem
                        })
        
        return results
    
    def read_page(self, page_path: str) -> str:
        """Read a specific wiki page"""
        full_path = Path(page_path)
        if full_path.exists():
            return full_path.read_text()
        return ""
    
    def add_to_index(self, page_type: str, title: str, summary: str):
        """Add a new page to index.md"""
        # Read current index
        index_content = ""
        if self.index_path.exists():
            index_content = self.index_path.read_text()
        
        # Find the right section
        section_header = f"## {title.capitalize()}"
        # For simplicity, append to Entities section
        # In production, parse and insert in correct alphabetical position
        new_entry = f"- [[{title}]] - {summary}\n"
        
        # Append to Entities section
        if "## Entities" in index_content:
            index_content = index_content.replace(
                "## Entities\n",
                f"## Entities\n{new_entry}"
            )
        
        self.index_path.write_text(index_content)
    
    def append_log(self, action: str, subject: str, details: str = ""):
        """Append entry to log.md"""
        today = datetime.now().strftime("%Y-%m-%d")
        entry = f"## [{today}] {action} | {subject}"
        if details:
            entry += f"\n- {details}"
        entry += "\n"
        
        if self.log_path.exists():
            current = self.log_path.read_text()
            self.log_path.write_text(current + entry + "\n")
        else:
            self.log_path.write_text("# Wiki Log\n\n" + entry + "\n")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd company-ops && python -m pytest .system/tests/test_wiki_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd company-ops
git add .system/lib/graph/wiki_client.py .system/tests/test_wiki_client.py
git commit -m "feat(wiki): add WikiClient for LLM Wiki operations

- Read SCHEMA.md, index.md, log.md
- Search wiki pages by content
- Add entries to index.md
- Append to log.md

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Create Knowledge Engine Module

**Files:**
- Create: `company-ops/.system/lib/graph/knowledge_engine.py`
- Test: `company-ops/.system/tests/test_knowledge_engine.py`

- [ ] **Step 1: Write the failing test**

```python
# company-ops/.system/tests/test_knowledge_engine.py
import pytest
import json
import os
from knowledge_engine import KnowledgeEngine

def test_knowledge_engine_initialization():
    """KnowledgeEngine should initialize with correct paths"""
    engine = KnowledgeEngine()
    assert engine.org_graph_path.endswith("global-graph.json")
    assert "wiki" in engine.wiki_path

def test_load_org_graph():
    """Should load organization graph"""
    engine = KnowledgeEngine()
    graph = engine.load_org_graph()
    assert "entities" in graph
    assert "relations" in graph

def test_query_org_graph_by_type():
    """Should query organization graph by entity type"""
    engine = KnowledgeEngine()
    results = engine.query_org_graph("subsystem", entity_type="subsystem")
    assert isinstance(results, list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd company-ops && python -m pytest .system/tests/test_knowledge_engine.py::test_knowledge_engine_initialization -v`
Expected: FAIL (module doesn't exist)

- [ ] **Step 3: Write minimal implementation**

```python
# company-ops/.system/lib/graph/knowledge_engine.py
"""Knowledge Engine - Unified query interface for Organization Graph and LLM Wiki"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from wiki_client import WikiClient


class QueryResult:
    """Result from knowledge query"""
    
    def __init__(self, answer: str, sources: Dict[str, List], confidence: float = 0.0):
        self.answer = answer
        self.sources = sources
        self.confidence = confidence
    
    def to_dict(self) -> Dict:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "confidence": self.confidence
        }


class KnowledgeEngine:
    """Unified knowledge query engine"""
    
    def __init__(self, org_graph_path: str = None, wiki_path: str = None):
        # Default paths
        base_dir = Path(__file__).parent.parent.parent
        self.org_graph_path = org_graph_path or str(base_dir / "global-graph.json")
        self.wiki_path = wiki_path or os.path.expanduser("~/wiki")
        
        # Initialize wiki client
        self.wiki = WikiClient(self.wiki_path)
    
    def load_org_graph(self) -> Dict:
        """Load organization graph from JSON file"""
        with open(self.org_graph_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def query_org_graph(self, query: str, entity_type: str = None, entity_id: str = None) -> List[Dict]:
        """
        Query organization graph.
        
        Args:
            query: Search query string
            entity_type: Filter by entity type (e.g., "subsystem", "goal")
            entity_id: Get specific entity by ID
        
        Returns:
            List of matching entities
        """
        graph = self.load_org_graph()
        entities = graph.get("entities", [])
        
        results = []
        
        # If specific entity requested
        if entity_id:
            for entity in entities:
                if entity.get("id") == entity_id:
                    return [entity]
            return []
        
        # Search by type
        if entity_type:
            entities = [e for e in entities if e.get("type") == entity_type]
        
        # Search by query string
        if query:
            query_lower = query.lower()
            for entity in entities:
                name = entity.get("name", "").lower()
                desc = entity.get("description", "").lower()
                if query_lower in name or query_lower in desc:
                    results.append(entity)
        
        return results
    
    def query_wiki(self, query: str) -> List[Dict]:
        """
        Query LLM Wiki for relevant pages.
        
        Args:
            query: Search query string
        
        Returns:
            List of matching wiki pages
        """
        return self.wiki.search_pages(query)
    
    def get_wiki_context(self, query: str) -> str:
        """
        Get context from wiki for a query.
        Reads relevant pages and returns combined content.
        """
        pages = self.query_wiki(query)
        
        if not pages:
            return ""
        
        # Limit to top 3 pages to avoid context overflow
        context_parts = []
        for page in pages[:3]:
            content = self.wiki.read_page(page["path"])
            if content:
                # Extract frontmatter and first 500 chars
                lines = content.split("\n")
                frontmatter_end = 0
                for i, line in enumerate(lines):
                    if line.strip() == "---":
                        frontmatter_end = i
                        if frontmatter_end > 0:
                            break
                
                # Get content after frontmatter
                body = "\n".join(lines[frontmatter_end+1:][:500])
                context_parts.append(f"## {page['title']}\n{body}")
        
        return "\n\n".join(context_parts)
    
    async def query(self, question: str) -> QueryResult:
        """
        Unified query - parallel query to both graphs.
        
        Args:
            question: User's question
        
        Returns:
            QueryResult with integrated answer and sources
        """
        import asyncio
        
        # Parallel queries (simplified - in production would use actual LLM)
        org_results = self.query_org_graph(question)
        wiki_results = self.query_wiki(question)
        
        # Build sources
        sources = {
            "organization": [
                {"id": e.get("id"), "name": e.get("name"), "type": e.get("type")}
                for e in org_results
            ],
            "wiki": [
                {"title": p.get("title"), "type": p.get("type")}
                for p in wiki_results
            ]
        }
        
        # Generate answer (simplified - in production would use LLM)
        answer_parts = []
        if org_results:
            answer_parts.append("From Organization Graph:")
            for e in org_results[:3]:
                answer_parts.append(f"- {e.get('name')}: {e.get('description', '')[:100]}")
        
        if wiki_results:
            answer_parts.append("\nFrom Wiki:")
            for p in wiki_results[:3]:
                answer_parts.append(f"- {p.get('title')} ({p.get('type')})")
        
        answer = "\n".join(answer_parts) if answer_parts else "No results found."
        
        return QueryResult(
            answer=answer,
            sources=sources,
            confidence=0.8 if (org_results or wiki_results) else 0.0
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd company-ops && python -m pytest .system/tests/test_knowledge_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd company-ops
git add .system/lib/graph/knowledge_engine.py .system/tests/test_knowledge_engine.py
git commit -m "feat(knowledge): add KnowledgeEngine for unified queries

- Load and query Organization Graph (global-graph.json)
- Query LLM Wiki via WikiClient
- Parallel query support
- QueryResult data structure

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Add Orchestrator Integration

**Files:**
- Modify: `company-ops/CLAUDE.md`
- Test: Manual testing in Orchestrator session

- [ ] **Step 1: Add knowledge query command to CLAUDE.md**

Read current CLAUDE.md and add the knowledge query section:

```markdown
## 知识查询

使用 Knowledge Engine 查询双图谱：

```bash
# 加载知识引擎
cd company-ops
python -c "
from .system.lib.graph.knowledge_engine import KnowledgeEngine
import asyncio

async def query():
    engine = KnowledgeEngine()
    result = await engine.query('财务 子系统')
    print(result.answer)
    print('Sources:', result.sources)

asyncio.run(query())
"
```

或者使用简化的 Python 脚本：

```bash
cd company-ops
python .system/lib/graph/query_knowledge.py "财务 子系统目标"
```

- [ ] **Step 2: Create query script for easier usage**

```python
# company-ops/.system/lib/graph/query_knowledge.py
#!/usr/bin/env python3
"""Simple CLI for knowledge queries"""

import sys
import asyncio
from knowledge_engine import KnowledgeEngine


async def main():
    if len(sys.argv) < 2:
        print("Usage: python query_knowledge.py <question>")
        print("Example: python query_knowledge.py '财务 子系统目标'")
        sys.exit(1)
    
    question = sys.argv[1]
    engine = KnowledgeEngine()
    result = await engine.query(question)
    
    print("=" * 50)
    print("Answer:")
    print(result.answer)
    print("=" * 50)
    print("Sources:")
    print(f"  Organization Graph: {len(result.sources.get('organization', []))} results")
    print(f"  Wiki: {len(result.sources.get('wiki', []))} results")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Test in Orchestrator**

```bash
cd company-ops
python .system/lib/graph/query_knowledge.py "Claude Code"
```

Expected: Should return results from both Organization Graph and Wiki

- [ ] **Step 4: Commit**

```bash
cd company-ops
git add CLAUDE.md .system/lib/graph/query_knowledge.py
git commit -m "feat(orchestrator): add knowledge query integration

- Add knowledge query section to CLAUDE.md
- Add query_knowledge.py CLI script

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Implement Knowledge Accumulation (Auto-Ingest)

**Files:**
- Modify: `company-ops/.system/lib/graph/knowledge_engine.py`
- Create: `company-ops/.system/lib/graph/accumulator.py`
- Test: `company-ops/.system/tests/test_accumulator.py`

- [ ] **Step 1: Write the failing test**

```python
# company-ops/.system/tests/test_accumulator.py
import pytest
import os
from accumulator import KnowledgeAccumulator

def test_accumulator_initialization():
    """Accumulator should initialize with wiki path"""
    acc = KnowledgeAccumulator()
    assert "wiki" in acc.wiki_path

def test_should_accumulate_important_task():
    """Important tasks should trigger accumulation"""
    acc = KnowledgeAccumulator()
    # High priority task
    assert acc.should_accumulate(priority="high") == True

def test_should_not_accumulate_low_priority():
    """Low priority tasks should not trigger accumulation"""
    acc = KnowledgeAccumulator()
    assert acc.should_accumulate(priority="low") == False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd company-ops && python -m pytest .system/tests/test_accumulator.py::test_accumulator_initialization -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# company-ops/.system/lib/graph/accumulator.py
"""Knowledge Accumulator - Auto-ingest knowledge to Wiki"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from wiki_client import WikiClient


class KnowledgeAccumulator:
    """Handles automatic knowledge accumulation to LLM Wiki"""
    
    # Priority thresholds for auto-accumulation
    AUTO_ACCUMULATE_PRIORITIES = ["high", "critical"]
    
    def __init__(self, wiki_path: str = None):
        self.wiki_path = wiki_path or os.path.expanduser("~/wiki")
        self.wiki = WikiClient(self.wiki_path)
    
    def should_accumulate(self, priority: str = "low", tags: list = None) -> bool:
        """
        Determine if task results should be accumulated.
        
        Args:
            priority: Task priority (low, medium, high, critical)
            tags: Optional list of tags
        
        Returns:
            True if should accumulate
        """
        # Check priority
        if priority in self.AUTO_ACCUMULATE_PRIORITIES:
            return True
        
        # Check tags for knowledge-related keywords
        if tags:
            knowledge_tags = ["knowledge", "learn", "document", "process", "decision"]
            for tag in tags:
                if tag.lower() in knowledge_tags:
                    return True
        
        return False
    
    def accumulate_task_result(
        self,
        task_title: str,
        task_result: str,
        priority: str = "medium",
        tags: list = None,
        entities: list = None,
        concepts: list = None
    ) -> Dict:
        """
        Accumulate task result to Wiki.
        
        Args:
            task_title: Title of the completed task
            task_result: Summary of the task result
            priority: Task priority
            tags: Associated tags
            entities: Entity mentions
            concepts: Concept mentions
        
        Returns:
            Dict with accumulation result
        """
        if not self.should_accumulate(priority, tags):
            return {"skipped": True, "reason": "low priority"}
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Determine page type
        page_type = "query"  # Default for task results
        
        # Create page filename
        filename = f"{task_title.lower().replace(' ', '-')[:50]}.md"
        
        # Build content
        content = f"""---
title: {task_title}
created: {today}
updated: {today}
type: {page_type}
tags: [{', '.join(tags) if tags else 'task-result'}]
sources: []
---

# {task_title}

## Summary
{task_result}

## Entities Mentioned
{chr(10).join([f'- {e}' for e in entities]) if entities else 'None'}

## Concepts
{chr(10).join([f'- {c}' for c in concepts]) if concepts else 'None'}

## Priority
{priority}
"""
        
        # Write to queries directory (or create appropriate directory)
        output_dir = self.wiki_path / "queries"
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / filename
        output_path.write_text(content)
        
        # Update index
        self.wiki.add_to_index(
            page_type=page_type,
            title=task_title,
            summary=task_result[:100]
        )
        
        # Log the accumulation
        self.wiki.append_log(
            action="accumulate",
            subject=task_title,
            details=f"Priority: {priority}, Type: {page_type}"
        )
        
        return {
            "skipped": False,
            "path": str(output_path),
            "action": "created"
        }
    
    def detect_knowledge_gap(self, query_result: Dict) -> bool:
        """
        Detect if query result indicates a knowledge gap.
        
        Args:
            query_result: Result from knowledge query
        
        Returns:
            True if knowledge gap detected
        """
        # If no results from either graph, likely a knowledge gap
        org_results = query_result.get("sources", {}).get("organization", [])
        wiki_results = query_result.get("sources", {}).get("wiki", [])
        
        if not org_results and not wiki_results:
            return True
        
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd company-ops && python -m pytest .system/tests/test_accumulator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd company-ops
git add .system/lib/graph/accumulator.py .system/tests/test_accumulator.py
git commit -m "feat(accumulator): add KnowledgeAccumulator for auto-ingest

- should_accumulate() to determine if task should be stored
- accumulate_task_result() to write to Wiki
- detect_knowledge_gap() to find knowledge gaps

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Integration Test

**Files:**
- Test: `company-ops/.system/tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# company-ops/.system/tests/test_integration.py
"""Integration tests for Knowledge Engine"""

import pytest
import asyncio
from knowledge_engine import KnowledgeEngine
from accumulator import KnowledgeAccumulator


@pytest.mark.asyncio
async def test_full_query_workflow():
    """Test complete query workflow"""
    engine = KnowledgeEngine()
    
    # Query for "Claude"
    result = await engine.query("Claude")
    
    # Should have some results
    assert result is not None
    assert result.confidence >= 0


def test_accumulation_workflow():
    """Test knowledge accumulation"""
    acc = KnowledgeAccumulator()
    
    # High priority task should accumulate
    result = acc.accumulate_task_result(
        task_title="Test Task",
        task_result="This is a test result",
        priority="high"
    )
    
    # Should not be skipped
    assert result.get("skipped") == False


def test_knowledge_gap_detection():
    """Test knowledge gap detection"""
    acc = KnowledgeAccumulator()
    
    # Empty results should be a knowledge gap
    empty_result = {"sources": {"organization": [], "wiki": []}}
    assert acc.detect_knowledge_gap(empty_result) == True
    
    # Results should not be a gap
    has_results = {"sources": {"organization": [{"id": "test"}], "wiki": []}}
    assert acc.detect_knowledge_gap(has_results) == False
```

- [ ] **Step 2: Run integration test**

Run: `cd company-ops && python -m pytest .system/tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
cd company-ops
git add .system/tests/test_integration.py
git commit -m "test(integration): add full workflow tests

- Test complete query workflow
- Test accumulation workflow
- Test knowledge gap detection

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Documentation and Usage Examples

**Files:**
- Create: `company-ops/docs/knowledge-engine-usage.md`
- Modify: `company-ops/.system/README.md` (if exists)

- [ ] **Step 1: Create usage documentation**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
cd company-ops
git add docs/knowledge-engine-usage.md
git commit -m "docs: add Knowledge Engine usage guide

- Quick start commands
- Programmatic usage examples
- Configuration

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Summary

This plan implements:

| Task | Component | Files |
|------|-----------|-------|
| 1 | Wiki Client | `wiki_client.py`, `test_wiki_client.py` |
| 2 | Knowledge Engine | `knowledge_engine.py`, `test_knowledge_engine.py` |
| 3 | Orchestrator Integration | `query_knowledge.py`, CLAUDE.md |
| 4 | Knowledge Accumulator | `accumulator.py`, `test_accumulator.py` |
| 5 | Integration Tests | `test_integration.py` |
| 6 | Documentation | `knowledge-engine-usage.md` |

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-13-llm-wiki-knowledge-engine.md`**.

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?

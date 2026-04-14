"""Knowledge Accumulator - Auto-ingest knowledge to Wiki

Follows Hermes Agent's llm-wiki skill Ingest workflow:
1. Capture raw source
2. Check what already exists (avoid duplicates)
3. Write/update wiki pages with [[wikilinks]] cross-references
4. Update navigation (index.md, log.md)
5. Report what changed
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Set


class KnowledgeAccumulator:
    """Handles automatic knowledge accumulation to LLM Wiki"""

    # Priority thresholds for auto-accumulation
    AUTO_ACCUMULATE_PRIORITIES = ["high", "critical"]

    # Minimum links required per page (Hermes requirement)
    MIN_OUTBOUND_LINKS = 2

    def __init__(self, wiki_path: str = None):
        self.wiki_path = wiki_path or os.path.expanduser("~/wiki")
        from wiki_client import WikiClient
        self.wiki = WikiClient(self.wiki_path)

    def should_accumulate(self, priority: str = "low", tags: List[str] = None) -> bool:
        """
        Determine if task results should be accumulated.
        """
        if priority in self.AUTO_ACCUMULATE_PRIORITIES:
            return True

        if tags:
            knowledge_tags = ["knowledge", "learn", "document", "process", "decision"]
            for tag in tags:
                if tag.lower() in knowledge_tags:
                    return True

        return False

    def _extract_entities_from_spec(self, spec_content: str) -> List[str]:
        """Extract entity mentions from spec content."""
        entities = []

        # Extract task names (Task N: pattern)
        task_pattern = r'(?:Task|任务)\s*(\d+)[:：]\s*([^\n]+)'
        tasks = re.findall(task_pattern, spec_content)
        for task_id, task_name in tasks:
            entities.append(f"Task {task_id}: {task_name.strip()}")

        # If no tasks found, extract section titles as entities
        if not entities:
            section_pattern = r'^#{1,3}\s+([^\n]+)'
            sections = re.findall(section_pattern, spec_content, re.MULTILINE)
            entities.extend([s.strip() for s in sections[:10]])

        # Extract tool/command patterns
        tool_pattern = r'`(cops|cmux|claude|git|python|npm|cargo)`'
        tools = re.findall(tool_pattern, spec_content)
        entities.extend([f"tool: {t}" for t in set(tools)])

        # Extract skill patterns
        skill_pattern = r'(?:skill|Skill)[:：]\s*([^\n]+)'
        skills = re.findall(skill_pattern, spec_content)
        entities.extend([s.strip() for s in skills[:5]])

        # Extract file paths
        file_pattern = r'(?:file|文件|path|路径)[:：]?\s*`?([^/\s]+\.\w+)`?'
        files = re.findall(file_pattern, spec_content)
        entities.extend([f"file: {f}" for f in files[:5]])

        return entities

    def _extract_concepts_from_spec(self, spec_content: str) -> List[str]:
        """Extract concept mentions from spec content."""
        concepts = []

        # Extract table content (for comparison concepts)
        table_pattern = r'\|\s*([^|]+?)\s*\|'
        table_cells = re.findall(table_pattern, spec_content)
        for cell in table_cells[:10]:
            cell = cell.strip()
            if cell and len(cell) < 50:
                concepts.append(cell)

        # Extract important terms from sections
        section_pattern = r'^#{1,3}\s+([^\n]+)'
        sections = re.findall(section_pattern, spec_content, re.MULTILINE)
        for section in sections:
            # Skip numbering prefix like "1.", "2.1", etc
            clean = re.sub(r'^\d+(\.\d+)*\s+', '', section.strip())
            if clean and len(clean) < 60:
                concepts.append(clean)

        # Extract key terms from bold text
        bold_pattern = r'\*\*([^*]+)\*\*'
        bolds = re.findall(bold_pattern, spec_content)
        concepts.extend([b.strip() for b in bolds[:5]])

        return list(set(concepts))  # Remove duplicates

    def _check_existing_content(self, title: str, summary: str) -> Dict:
        """Check if similar content already exists (Hermes Ingest step 2)."""
        index_content = self.wiki.read_index()

        # Search for similar titles
        title_lower = title.lower()
        if title_lower in index_content.lower():
            return {"exists": True, "reason": "title_exists"}

        # Check summary for keywords
        summary_keywords = set(summary.lower().split()[:5])
        for line in index_content.split('\n'):
            if '- [[' in line:
                existing_keywords = set(line.lower().split())
                if len(summary_keywords & existing_keywords) >= 3:
                    return {"exists": True, "reason": "similar_content"}

        return {"exists": False}

    def _find_wikilink_candidates(self, entities: List[str], concepts: List[str]) -> List[str]:
        """Find potential wikilinks for cross-referencing."""
        candidates = []

        # Search existing wiki pages
        all_pages = (
            list((self.wiki.entities_path).glob("*.md")) +
            list((self.wiki.concepts_path).glob("*.md")) +
            list((self.wiki.comparisons_path).glob("*.md"))
        )

        existing_titles = {p.stem for p in all_pages}

        for entity in entities[:5]:
            entity_clean = entity.lower().replace(' ', '-')
            for existing in existing_titles:
                if entity_clean in existing or existing in entity_clean:
                    candidates.append(f"[[{existing}]]")

        # Add default links if not enough found
        if len(candidates) < self.MIN_OUTBOUND_LINKS:
            default_links = ["[[knowledge-engine]]", "[[task-system]]"]
            for link in default_links:
                if link not in candidates:
                    candidates.append(link)

        return candidates[:self.MIN_OUTBOUND_LINKS]

    def accumulate_task_spec(
        self,
        task_title: str,
        spec_content: str,
        spec_file_path: str = None,
        priority: str = "medium",
        tags: List[str] = None,
        force: bool = False,
    ) -> Dict:
        """
        Accumulate task spec with full execution details.

        Args:
            task_title: Title of the completed task
            spec_content: Full spec content (implementation plan)
            spec_file_path: Path to the spec file (for source tracking)
            priority: Task priority
            tags: Associated tags
            force: Force recreation if already exists

        Returns:
            Dict with accumulation result and improvements for Orchestrator
        """
        if not self.should_accumulate(priority, tags):
            return {"skipped": True, "reason": "low priority"}

        today = datetime.now().strftime("%Y-%m-%d")

        # Extract entities and concepts from spec
        entities = self._extract_entities_from_spec(spec_content)
        concepts = self._extract_concepts_from_spec(spec_content)

        # Step 2: Check existing content (skip if force=True)
        if not force:
            existing_check = self._check_existing_content(task_title, spec_content[:200])
            if existing_check["exists"]:
                return {
                    "skipped": True,
                    "reason": existing_check["reason"],
                    "message": f"Similar content already exists: {existing_check['reason']}. Use force=True to overwrite."
                }

        # Determine page type based on content
        content_lower = spec_content.lower()
        if "compare" in content_lower or " vs " in content_lower or "对比" in content_lower:
            page_type = "comparison"
        elif "concept" in content_lower or "architecture" in content_lower or "设计" in content_lower or "design" in content_lower:
            page_type = "concept"
        elif "plan" in content_lower or "implementation" in content_lower or "实施" in content_lower:
            page_type = "query"
        else:
            page_type = "concept"

        # Generate wikilinks
        wikilinks = self._find_wikilink_candidates(entities, concepts)
        wikilinks_text = '\n'.join([f"- {link}" for link in wikilinks]) if wikilinks else "- (no cross-references found)"

        # Build content following Hermes schema
        content = f"""---
title: {task_title}
created: {today}
updated: {today}
type: {page_type}
tags: [{', '.join(tags) if tags else 'task-result, knowledge'}]
sources: [{spec_file_path or 'direct-input'}]
---

# {task_title}

## Execution Summary
This document captures the task execution flow, tools used, and knowledge gained.

## Spec File
{f'Reference: {spec_file_path}' if spec_file_path else 'Direct input'}

## Tasks Executed
```spec
{spec_content[:2000]}
```

## Entities Extracted
{chr(10).join([f'- {e}' for e in entities]) if entities else '- None'}

## Concepts Covered
{chr(10).join([f'- {c}' for c in concepts]) if concepts else '- None'}

## Cross-References
{wikilinks_text}

## Priority
{priority}

## Knowledge Gained
<!-- Fill in: What was learned from executing this task -->

## Related Tasks
<!-- Fill in: Related task IDs or titles -->
"""

        # Determine output directory
        if page_type == "comparison":
            output_dir = self.wiki_path + "/comparisons"
        elif page_type == "concept":
            output_dir = self.wiki_path + "/concepts"
        else:
            output_dir = self.wiki_path + "/queries"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create filename
        filename = f"{task_title.lower().replace(' ', '-')[:50]}.md"
        output_path = output_dir / filename
        output_path.write_text(content)

        # Step 4: Update navigation
        self.wiki.add_to_index(
            page_type=page_type,
            title=task_title,
            summary=spec_content[:100].replace('\n', ' ')
        )

        # Log the accumulation
        self.wiki.append_log(
            action="ingest",
            subject=task_title,
            details=f"Priority: {priority}, Type: {page_type}, Entities: {len(entities)}"
        )

        # ============================================
        # 返回 Orchestrator 可执行的改进建议
        # ============================================
        improvements = self._generate_improvements(
            task_title=task_title,
            entities=entities,
            concepts=concepts,
            spec_content=spec_content,
            page_type=page_type,
            output_path=str(output_path)
        )

        return {
            "skipped": False,
            "path": str(output_path),
            "action": "created",
            "entities": entities,
            "concepts": concepts,
            "wikilinks": wikilinks,
            "page_type": page_type,
            # 新增：Orchestrator 可执行的改进任务
            "improvements": improvements
        }

    def _generate_improvements(
        self,
        task_title: str,
        entities: List[str],
        concepts: List[str],
        spec_content: str,
        page_type: str,
        output_path: str
    ) -> Dict:
        """
        生成 Orchestrator 可执行的改进任务列表。
        """
        improvements = {
            "required": [],
            "optional": []
        }

        # 1. 检查 wikilinks 质量
        existing_pages = self._get_existing_wiki_titles()
        relevant_links = [e for e in entities if any(
            e.lower() in existing.lower() or existing.lower() in e.lower()
            for existing in existing_pages
        )]

        if len(relevant_links) < 2:
            improvements["required"].append({
                "action": "add_wikilinks",
                "description": "添加更多相关 wikilinks",
                "suggestion": "搜索现有 wiki 页面，找到与本文档相关的页面并添加链接",
                "command": f"# 搜索相关页面\ngrep -l '{entities[0] if entities else task_title}' ~/wiki/**/*.md"
            })

        # 2. 填充 Knowledge Gained
        improvements["required"].append({
            "action": "fill_knowledge_gained",
            "description": "填充知识收获内容",
            "suggestion": "分析 spec 内容，总结执行任务过程中获得的关键知识",
            "template": f"""## Knowledge Gained
- 核心概念: {concepts[0] if concepts else 'N/A'}
- 关键决策:
- 经验教训: """
        })

        # 3. 填充 Related Tasks (对于实施类文档)
        content_lower = spec_content.lower()
        is_implementation = any(keyword in content_lower for keyword in [
            "plan", "implementation", "实施", "计划", "任务", "task"
        ])
        if is_implementation:
            improvements["optional"].append({
                "action": "fill_related_tasks",
                "description": "填充相关任务引用",
                "suggestion": "如果本文档引用了其他任务或被其他任务引用，在此记录"
            })

        # 4. 验证 index.md
        improvements["optional"].append({
            "action": "verify_index",
            "description": "验证 index.md 条目格式",
            "suggestion": "检查 index.md 中的摘要是否清晰，是否需要精简"
        })

        # 5. 检查是否需要拆分为多个页面
        if len(spec_content) > 5000:
            improvements["optional"].append({
                "action": "consider_split",
                "description": "考虑拆分大型页面",
                "suggestion": f"内容超过 5000 字符({len(spec_content)}), 考虑拆分为子主题",
                "threshold": "200 lines recommended"
            })

        return improvements

    def _get_existing_wiki_titles(self) -> List[str]:
        """获取现有 wiki 页面的标题列表"""
        titles = []
        for subdir in ["entities", "concepts", "comparisons", "queries"]:
            dir_path = Path(self.wiki_path) / subdir
            if dir_path.exists():
                for md_file in dir_path.glob("*.md"):
                    titles.append(md_file.stem)
        return titles

    def apply_improvement(
        self,
        improvement: Dict,
        wiki_page_path: str
    ) -> Dict:
        """
        执行单个改进任务。
        由 Orchestrator 调用。
        """
        action = improvement.get("action")

        if action == "add_wikilinks":
            # 读取现有页面内容
            content = Path(wiki_page_path).read_text()
            # TODO: 实现自动添加 wikilinks 的逻辑
            return {"applied": False, "reason": "需要 LLM 判断相关页面"}

        elif action == "fill_knowledge_gained":
            content = Path(wiki_page_path).read_text()
            template = improvement.get("template", "")
            # 替换占位符
            new_content = content.replace(
                "## Knowledge Gained\n<!-- Fill in: What was learned from executing this task -->",
                "## Knowledge Gained\n" + template
            )
            Path(wiki_page_path).write_text(new_content)
            return {"applied": True, "action": "filled_knowledge_gained"}

        elif action == "fill_related_tasks":
            # TODO: 实现相关任务填充
            return {"applied": False, "reason": "需要人工或任务系统查询"}

        return {"applied": False, "reason": "unknown action"}

    def accumulate_task_result(
        self,
        task_title: str,
        task_result: str,
        priority: str = "medium",
        tags: List[str] = None,
        entities: List[str] = None,
        concepts: List[str] = None
    ) -> Dict:
        """
        Accumulate task result to Wiki (legacy interface).

        For full spec capture, use accumulate_task_spec() instead.
        """
        if not self.should_accumulate(priority, tags):
            return {"skipped": True, "reason": "low priority"}

        today = datetime.now().strftime("%Y-%m-%d")
        page_type = "query"

        # Generate wikilinks for entities
        wikilinks = self._find_wikilink_candidates(entities or [], concepts or [])
        wikilinks_text = '\n'.join([f"- {link}" for link in wikilinks]) if wikilinks else "- None"

        # Build content with wikilinks
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

## Cross-References
{wikilinks_text}

## Priority
{priority}
"""

        output_dir = Path(self.wiki_path) / "queries"
        output_dir.mkdir(exist_ok=True)

        filename = f"{task_title.lower().replace(' ', '-')[:50]}.md"
        output_path = output_dir / filename
        output_path.write_text(content)

        self.wiki.add_to_index(
            page_type=page_type,
            title=task_title,
            summary=task_result[:100]
        )

        self.wiki.append_log(
            action="ingest",
            subject=task_title,
            details=f"Priority: {priority}, Type: {page_type}"
        )

        return {
            "skipped": False,
            "path": str(output_path),
            "action": "created"
        }

    def detect_knowledge_gap(self, query_result: Dict) -> bool:
        """Detect if query result indicates a knowledge gap."""
        org_results = query_result.get("sources", {}).get("organization", [])
        wiki_results = query_result.get("sources", {}).get("wiki", [])

        if not org_results and not wiki_results:
            return True

        return False

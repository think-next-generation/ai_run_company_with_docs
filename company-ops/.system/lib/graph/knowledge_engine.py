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
        # Default paths - base is company-ops root (parent of .system)
        base_dir = Path(__file__).parent.parent.parent.parent
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
        """Query LLM Wiki for relevant pages."""
        return self.wiki.search_pages(query)
    
    def get_wiki_context(self, query: str) -> str:
        """Get context from wiki for a query."""
        pages = self.query_wiki(query)
        
        if not pages:
            return ""
        
        context_parts = []
        for page in pages[:3]:
            content = self.wiki.read_page(page["path"])
            if content:
                lines = content.split("\n")
                frontmatter_end = 0
                for i, line in enumerate(lines):
                    if line.strip() == "---":
                        frontmatter_end = i
                        if frontmatter_end > 0:
                            break
                
                body = "\n".join(lines[frontmatter_end+1:][:500])
                context_parts.append(f"## {page['title']}\n{body}")
        
        return "\n\n".join(context_parts)
    
    async def query(self, question: str) -> QueryResult:
        """Unified query - parallel query to both graphs."""
        org_results = self.query_org_graph(question)
        wiki_results = self.query_wiki(question)
        
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

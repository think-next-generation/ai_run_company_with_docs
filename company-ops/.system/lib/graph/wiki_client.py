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

    @property
    def comparisons_path(self) -> Path:
        return self.wiki_path / "comparisons"

    @property
    def queries_path(self) -> Path:
        return self.wiki_path / "queries"
    
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
        index_content = ""
        if self.index_path.exists():
            index_content = self.index_path.read_text()

        # Check if already exists
        if f"[[{title}]]" in index_content:
            return  # Skip if already in index

        new_entry = f"- [[{title}]] - {summary}\n"

        # Find the right section based on page_type
        section_map = {
            "entity": "## Entities",
            "concept": "## Concepts",
            "comparison": "## Comparisons",
            "query": "## Queries",
        }

        section_key = section_map.get(page_type, "## Queries")

        if section_key in index_content:
            index_content = index_content.replace(
                section_key + "\n",
                section_key + "\n" + new_entry
            )
        else:
            # Default to Queries section
            index_content = index_content.replace(
                "## Queries\n",
                "## Queries\n" + new_entry
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

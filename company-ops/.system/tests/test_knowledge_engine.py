import pytest
import json
import os
from pathlib import Path

# Import from the graph package - use lib/graph path
import sys
lib_path = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_path))
# Also add lib/graph for wiki_client import
graph_path = lib_path / "graph"
sys.path.insert(0, str(graph_path))

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

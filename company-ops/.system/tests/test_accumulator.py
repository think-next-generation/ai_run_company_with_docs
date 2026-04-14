import pytest
import os
from pathlib import Path

# Import from the graph package - use lib/graph path
import sys
lib_path = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_path))
# Also add lib/graph for wiki_client import
graph_path = lib_path / "graph"
sys.path.insert(0, str(graph_path))

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

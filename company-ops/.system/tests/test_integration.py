"""Integration tests for Knowledge Engine"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add lib/graph to path for imports
lib_graph_path = Path(__file__).parent.parent / "lib" / "graph"
sys.path.insert(0, str(lib_graph_path))

from knowledge_engine import KnowledgeEngine, QueryResult
from accumulator import KnowledgeAccumulator


@pytest.mark.asyncio
async def test_full_query_workflow():
    """Test complete query workflow"""
    engine = KnowledgeEngine()
    
    # Query for "财务"
    result = await engine.query("财务")
    
    # Should have some results
    assert result is not None
    assert isinstance(result, QueryResult)
    assert result.confidence >= 0
    # Sources should have organization and wiki keys
    assert "organization" in result.sources
    assert "wiki" in result.sources


def test_accumulation_workflow():
    """Test knowledge accumulation"""
    acc = KnowledgeAccumulator()
    
    # High priority task should accumulate
    result = acc.accumulate_task_result(
        task_title="Test Task",
        task_result="This is a test result",
        priority="high"
    )
    
    # Should not be skipped for high priority
    assert result.get("skipped") == False


def test_accumulation_low_priority_skipped():
    """Test low priority task is skipped"""
    acc = KnowledgeAccumulator()
    
    result = acc.accumulate_task_result(
        task_title="Low Priority Task",
        task_result="This should be skipped",
        priority="low"
    )
    
    assert result.get("skipped") == True


def test_knowledge_gap_detection():
    """Test knowledge gap detection"""
    acc = KnowledgeAccumulator()
    
    # Empty results should be a knowledge gap
    empty_result = {"sources": {"organization": [], "wiki": []}}
    assert acc.detect_knowledge_gap(empty_result) == True
    
    # Results should not be a gap
    has_results = {"sources": {"organization": [{"id": "test"}], "wiki": []}}
    assert acc.detect_knowledge_gap(has_results) == False


def test_should_accumulate_priority():
    """Test should_accumulate respects priority"""
    acc = KnowledgeAccumulator()
    
    # High priority should accumulate
    assert acc.should_accumulate(priority="high") == True
    assert acc.should_accumulate(priority="critical") == True
    
    # Low priority should not accumulate
    assert acc.should_accumulate(priority="low") == False
    assert acc.should_accumulate(priority="medium") == False


def test_should_accumulate_tags():
    """Test should_accumulate respects knowledge tags"""
    acc = KnowledgeAccumulator()
    
    # Low priority with knowledge tags should accumulate
    assert acc.should_accumulate(priority="low", tags=["knowledge"]) == True
    assert acc.should_accumulate(priority="low", tags=["document"]) == True
    assert acc.should_accumulate(priority="low", tags=["process"]) == True


def test_query_result_to_dict():
    """Test QueryResult serialization"""
    result = QueryResult(
        answer="Test answer",
        sources={"organization": [], "wiki": []},
        confidence=0.9
    )
    
    result_dict = result.to_dict()
    assert result_dict["answer"] == "Test answer"
    assert result_dict["confidence"] == 0.9
    assert result_dict["sources"]["organization"] == []

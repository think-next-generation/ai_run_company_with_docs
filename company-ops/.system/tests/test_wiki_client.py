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

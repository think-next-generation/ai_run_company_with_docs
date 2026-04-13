"""
Learning System for company-ops.

Enables continuous improvement through pattern extraction,
feedback processing, specification evolution, and cross-system sharing.
"""

from .extraction.extractor import PatternExtractor
from .feedback.processor import FeedbackProcessor
from .evolution.engine import SpecificationEvolver
from .sharing.synchronizer import KnowledgeSynchronizer
from .learning_engine import LearningEngine

__version__ = "1.0.0"
__all__ = [
    "PatternExtractor",
    "FeedbackProcessor",
    "SpecificationEvolver",
    "KnowledgeSynchronizer",
    "LearningEngine",
]

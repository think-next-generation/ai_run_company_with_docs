"""
Knowledge sharing module.

Shares knowledge across subsystems.
"""

from .synchronizer import KnowledgeSynchronizer, SharedKnowledge, SynchronizationResult

__all__ = ["KnowledgeSynchronizer", "SharedKnowledge", "SynchronizationResult"]

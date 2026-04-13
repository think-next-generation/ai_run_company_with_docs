"""
Learning Engine for company-ops.

Orchestrates all learning activities: pattern extraction,
feedback processing, specification evolution, and knowledge sharing.
"""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class LearningResult:
    """Result of a learning cycle."""
    timestamp: str
    patterns_extracted: int
    feedback_processed: int
    specifications_updated: int
    knowledge_shared: int
    insights: list[dict]
    recommendations: list[str]


class LearningEngine:
    """
    Main learning engine that coordinates all learning activities.

    Learning Cycle:
    1. Extract patterns from execution history
    2. Process human feedback
    3. Evolve specifications based on patterns and feedback
    4. Share learnings across subsystems
    """

    def __init__(self, knowledge_graph, config: dict = None):
        """
        Initialize the learning engine.

        Args:
            knowledge_graph: KnowledgeGraph instance
            config: Optional configuration
        """
        self.kg = knowledge_graph
        self.config = config or {}
        self.base_path = Path(self.config.get("base_path", "."))

        # Initialize components
        from .extraction.extractor import PatternExtractor
        from .feedback.processor import FeedbackProcessor
        from .evolution.engine import SpecificationEvolver
        from .sharing.synchronizer import KnowledgeSynchronizer

        self.extractor = PatternExtractor(knowledge_graph, self.config.get("extraction", {}))
        self.feedback_processor = FeedbackProcessor(knowledge_graph, self.config.get("feedback", {}))
        self.evolver = SpecificationEvolver(knowledge_graph, self.config.get("evolution", {}))
        self.synchronizer = KnowledgeSynchronizer(knowledge_graph, self.config.get("sharing", {}))

        # Learning state
        self.last_learning_cycle: Optional[str] = None
        self.learning_history: list[LearningResult] = []

    def run_learning_cycle(self, scope: str = "all") -> LearningResult:
        """
        Run a complete learning cycle.

        Args:
            scope: "all", "global", or specific subsystem_id

        Returns:
            LearningResult with summary of learnings
        """
        timestamp = datetime.now().isoformat()
        insights = []
        recommendations = []

        # Step 1: Extract patterns
        patterns = self.extractor.extract_patterns(scope)
        patterns_count = len(patterns.get("patterns", []))
        if patterns_count > 0:
            insights.append({
                "type": "patterns_extracted",
                "count": patterns_count,
                "top_patterns": patterns.get("patterns", [])[:5]
            })

        # Step 2: Process feedback
        feedback_result = self.feedback_processor.process_pending(scope)
        feedback_count = feedback_result.get("processed", 0)
        if feedback_count > 0:
            insights.append({
                "type": "feedback_processed",
                "count": feedback_count,
                "summary": feedback_result.get("summary")
            })

        # Step 3: Evolve specifications
        evolution_result = self.evolver.evolve(scope)
        specs_updated = evolution_result.get("updated", 0)
        if specs_updated > 0:
            insights.append({
                "type": "specifications_evolved",
                "count": specs_updated,
                "changes": evolution_result.get("changes", [])
            })
            recommendations.extend(evolution_result.get("recommendations", []))

        # Step 4: Share knowledge
        sharing_result = self.synchronizer.synchronize(scope)
        knowledge_shared = sharing_result.get("shared", 0)
        if knowledge_shared > 0:
            insights.append({
                "type": "knowledge_shared",
                "count": knowledge_shared,
                "targets": sharing_result.get("targets", [])
            })

        # Create result
        result = LearningResult(
            timestamp=timestamp,
            patterns_extracted=patterns_count,
            feedback_processed=feedback_count,
            specifications_updated=specs_updated,
            knowledge_shared=knowledge_shared,
            insights=insights,
            recommendations=recommendations
        )

        # Store in history
        self.learning_history.append(result)
        self.last_learning_cycle = timestamp

        # Persist learning state
        self._persist_learning_result(result)

        return result

    def learn_from_execution(self, execution_record: dict) -> dict:
        """
        Learn from a single execution record.

        Args:
            execution_record: Record of a task execution

        Returns:
            Learning insights from this execution
        """
        insights = {
            "patterns": [],
            "feedback_items": [],
            "suggestions": []
        }

        # Extract patterns from this execution
        patterns = self.extractor.extract_from_execution(execution_record)
        insights["patterns"] = patterns

        # Check for implicit feedback (success/failure patterns)
        if execution_record.get("status") == "failed":
            insights["suggestions"].append({
                "type": "failure_pattern",
                "context": execution_record.get("context"),
                "error": execution_record.get("error"),
                "recommendation": "Consider adding this failure pattern to risk assessment"
            })

        return insights

    def learn_from_feedback(self, feedback: dict) -> dict:
        """
        Learn from explicit human feedback.

        Args:
            feedback: Human feedback data

        Returns:
            Processing result
        """
        return self.feedback_processor.process_feedback(feedback)

    def get_learning_stats(self) -> dict:
        """Get learning statistics."""
        return {
            "total_cycles": len(self.learning_history),
            "last_cycle": self.last_learning_cycle,
            "total_patterns_extracted": sum(r.patterns_extracted for r in self.learning_history),
            "total_feedback_processed": sum(r.feedback_processed for r in self.learning_history),
            "total_specifications_updated": sum(r.specifications_updated for r in self.learning_history),
            "total_knowledge_shared": sum(r.knowledge_shared for r in self.learning_history),
        }

    def get_recent_insights(self, limit: int = 10) -> list[dict]:
        """Get recent learning insights."""
        all_insights = []
        for result in reversed(self.learning_history[-10:]):
            all_insights.extend(result.insights)
        return all_insights[:limit]

    def _persist_learning_result(self, result: LearningResult):
        """Persist learning result to disk."""
        learning_dir = self.base_path / ".system" / "learning"
        learning_dir.mkdir(parents=True, exist_ok=True)

        result_file = learning_dir / f"learning_{result.timestamp.replace(':', '-')}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": result.timestamp,
                "patterns_extracted": result.patterns_extracted,
                "feedback_processed": result.feedback_processed,
                "specifications_updated": result.specifications_updated,
                "knowledge_shared": result.knowledge_shared,
                "insights": result.insights,
                "recommendations": result.recommendations
            }, f, ensure_ascii=False, indent=2)

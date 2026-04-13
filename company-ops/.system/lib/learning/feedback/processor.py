"""
Feedback Processor for company-ops learning system.

Processes human feedback and converts it into actionable improvements.
"""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json


@dataclass
class FeedbackItem:
    """Represents a feedback item."""
    feedback_id: str
    feedback_type: str  # "correction", "approval", "rejection", "suggestion"
    subsystem_id: str
    context: dict
    content: str
    severity: str  # "low", "medium", "high"
    status: str  # "pending", "processed", "applied"
    created_at: str
    processed_at: Optional[str] = None


@dataclass
class ProcessedFeedback:
    """Result of processing feedback."""
    feedback_id: str
    actions: list[dict]
    specification_updates: list[dict]
    knowledge_updates: list[dict]
    notifications: list[str]


class FeedbackProcessor:
    """
    Processes human feedback from various sources.

    Feedback sources:
    - human/feedback/ directory (file-based)
    - Review decisions from human/reviews/
    - Direct corrections in documents
    - Explicit feedback messages
    """

    FEEDBACK_TYPES = {
        "correction": {
            "description": "Correction to agent output",
            "auto_apply": False,
            "requires_review": True,
        },
        "approval": {
            "description": "Approval of agent action",
            "auto_apply": True,
            "requires_review": False,
        },
        "rejection": {
            "description": "Rejection of agent action",
            "auto_apply": False,
            "requires_review": True,
        },
        "suggestion": {
            "description": "Improvement suggestion",
            "auto_apply": False,
            "requires_review": True,
        },
        "rating": {
            "description": "Quality rating",
            "auto_apply": True,
            "requires_review": False,
        }
    }

    def __init__(self, knowledge_graph, config: dict = None):
        self.kg = knowledge_graph
        self.config = config or {}
        self.base_path = Path(self.config.get("base_path", "."))

        # Feedback queue
        self.pending_feedback: list[FeedbackItem] = []
        self.processed_feedback: list[ProcessedFeedback] = []

    def process_pending(self, scope: str = "all") -> dict:
        """
        Process all pending feedback.

        Args:
            scope: "all", "global", or subsystem_id

        Returns:
            Processing summary
        """
        # Load pending feedback
        self._load_pending_feedback(scope)

        processed_count = 0
        results = []

        for feedback in self.pending_feedback:
            if feedback.status != "pending":
                continue

            if scope != "all" and feedback.subsystem_id != scope:
                continue

            result = self._process_feedback_item(feedback)
            if result:
                processed_count += 1
                results.append(result)
                feedback.status = "processed"
                feedback.processed_at = datetime.now().isoformat()

        return {
            "processed": processed_count,
            "results": [
                {
                    "feedback_id": r.feedback_id,
                    "actions": len(r.actions),
                    "updates": len(r.specification_updates)
                }
                for r in results
            ],
            "summary": self._summarize_results(results)
        }

    def process_feedback(self, feedback: dict) -> dict:
        """
        Process a single feedback item.

        Args:
            feedback: Feedback data

        Returns:
            Processing result
        """
        item = FeedbackItem(
            feedback_id=feedback.get("feedback_id", self._generate_id()),
            feedback_type=feedback.get("type", "suggestion"),
            subsystem_id=feedback.get("subsystem_id", "global"),
            context=feedback.get("context", {}),
            content=feedback.get("content", ""),
            severity=feedback.get("severity", "medium"),
            status="pending",
            created_at=datetime.now().isoformat()
        )

        result = self._process_feedback_item(item)

        if result:
            return {
                "status": "processed",
                "feedback_id": result.feedback_id,
                "actions": result.actions,
                "updates": result.specification_updates,
                "notifications": result.notifications
            }
        else:
            return {
                "status": "failed",
                "feedback_id": item.feedback_id,
                "error": "Could not process feedback"
            }

    def _process_feedback_item(self, feedback: FeedbackItem) -> Optional[ProcessedFeedback]:
        """Process a single feedback item."""
        feedback_type = feedback.feedback_type
        type_config = self.FEEDBACK_TYPES.get(feedback_type, {})

        actions = []
        spec_updates = []
        knowledge_updates = []
        notifications = []

        if feedback_type == "correction":
            # Extract what was corrected
            correction = self._parse_correction(feedback)
            if correction:
                actions.append({
                    "type": "apply_correction",
                    "target": correction.get("target"),
                    "original": correction.get("original"),
                    "corrected": correction.get("corrected")
                })
                spec_updates.append({
                    "type": "add_pattern",
                    "pattern": correction.get("pattern"),
                    "source": "human_correction"
                })

        elif feedback_type == "approval":
            actions.append({
                "type": "record_approval",
                "context": feedback.context
            })
            knowledge_updates.append({
                "type": "positive_example",
                "context": feedback.context
            })

        elif feedback_type == "rejection":
            actions.append({
                "type": "record_rejection",
                "context": feedback.context,
                "reason": feedback.content
            })
            spec_updates.append({
                "type": "add_constraint",
                "constraint": feedback.content,
                "source": "human_rejection"
            })

        elif feedback_type == "suggestion":
            suggestion = self._parse_suggestion(feedback)
            if suggestion:
                actions.append({
                    "type": "evaluate_suggestion",
                    "suggestion": suggestion
                })
                notifications.append(f"New suggestion for {feedback.subsystem_id}: {suggestion.get('summary', '')}")

        elif feedback_type == "rating":
            rating = self._parse_rating(feedback)
            if rating:
                knowledge_updates.append({
                    "type": "quality_metric",
                    "metric": rating.get("metric"),
                    "value": rating.get("value"),
                    "context": feedback.context
                })

        return ProcessedFeedback(
            feedback_id=feedback.feedback_id,
            actions=actions,
            specification_updates=spec_updates,
            knowledge_updates=knowledge_updates,
            notifications=notifications
        )

    def _load_pending_feedback(self, scope: str):
        """Load pending feedback from files."""
        feedback_dir = self.base_path / "human" / "feedback"

        if not feedback_dir.exists():
            return

        for feedback_file in feedback_dir.glob("*.json"):
            try:
                with open(feedback_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                item = FeedbackItem(
                    feedback_id=data.get("feedback_id", feedback_file.stem),
                    feedback_type=data.get("type", "suggestion"),
                    subsystem_id=data.get("subsystem_id", "global"),
                    context=data.get("context", {}),
                    content=data.get("content", ""),
                    severity=data.get("severity", "medium"),
                    status=data.get("status", "pending"),
                    created_at=data.get("created_at", datetime.now().isoformat())
                )

                # Avoid duplicates
                if not any(f.feedback_id == item.feedback_id for f in self.pending_feedback):
                    self.pending_feedback.append(item)

            except Exception as e:
                print(f"Error loading feedback {feedback_file}: {e}")

    def _parse_correction(self, feedback: FeedbackItem) -> Optional[dict]:
        """Parse correction feedback."""
        content = feedback.content

        # Try to extract original/corrected pairs
        # Format: "原: xxx -> 改: yyy" or "original: xxx -> corrected: yyy"
        patterns = [
            r"原[：:]\s*(.+?)\s*->\s*改[：:]\s*(.+)",
            r"original[：:]\s*(.+?)\s*->\s*corrected[：:]\s*(.+)",
        ]

        for pattern in patterns:
            match = content.match(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return {
                    "original": match.group(1).strip(),
                    "corrected": match.group(2).strip(),
                    "target": feedback.context.get("target"),
                    "pattern": f"Avoid: {match.group(1).strip()[:50]}"
                }

        return {"content": content, "target": feedback.context.get("target")}

    def _parse_suggestion(self, feedback: FeedbackItem) -> Optional[dict]:
        """Parse suggestion feedback."""
        return {
            "summary": feedback.content[:100],
            "details": feedback.content,
            "subsystem": feedback.subsystem_id,
            "priority": feedback.severity
        }

    def _parse_rating(self, feedback: FeedbackItem) -> Optional[dict]:
        """Parse rating feedback."""
        content = feedback.content

        # Try to extract numeric rating
        import re
        match = re.search(r"(\d+(?:\.\d+)?)[/\s]*(?:out\s+of\s+)?(\d+)?", content)
        if match:
            value = float(match.group(1))
            max_value = float(match.group(2)) if match.group(2) else 5.0
            normalized = value / max_value

            return {
                "value": normalized,
                "raw_value": value,
                "max_value": max_value,
                "metric": "quality"
            }

        # Check for sentiment-based rating
        positive_words = ["好", "优秀", "满意", "good", "excellent", "satisfied"]
        negative_words = ["差", "糟糕", "不满意", "bad", "poor", "unsatisfied"]

        content_lower = content.lower()
        if any(w in content_lower for w in positive_words):
            return {"value": 0.8, "metric": "quality"}
        elif any(w in content_lower for w in negative_words):
            return {"value": 0.3, "metric": "quality"}

        return None

    def _summarize_results(self, results: list[ProcessedFeedback]) -> dict:
        """Summarize processing results."""
        if not results:
            return {"message": "No feedback processed"}

        total_actions = sum(len(r.actions) for r in results)
        total_updates = sum(len(r.specification_updates) for r in results)

        return {
            "total_feedback": len(results),
            "total_actions": total_actions,
            "total_spec_updates": total_updates,
            "message": f"Processed {len(results)} feedback items, generated {total_actions} actions"
        }

    def _generate_id(self) -> str:
        """Generate a unique feedback ID."""
        import uuid
        return f"fb-{uuid.uuid4().hex[:8]}"


import re  # Add import at module level

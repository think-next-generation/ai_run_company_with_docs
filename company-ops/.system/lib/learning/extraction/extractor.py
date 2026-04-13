"""
Pattern Extractor for company-ops learning system.

Extracts reusable patterns from execution history and task records.
"""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
import re


@dataclass
class Pattern:
    """Represents an extracted pattern."""
    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    confidence: float
    examples: list[str]
    metadata: dict = field(default_factory=dict)


class PatternExtractor:
    """
    Extracts patterns from execution history.

    Pattern types:
    - workflow: Common task sequences
    - decision: Decision-making patterns
    - error: Error and recovery patterns
    - optimization: Efficiency improvement patterns
    - collaboration: Cross-subsystem interaction patterns
    """

    # Pattern detection rules
    PATTERN_RULES = {
        "workflow": {
            "sequential_tasks": {
                "description": "Tasks commonly executed in sequence",
                "min_frequency": 3,
                "window_days": 30,
            },
            "time_based": {
                "description": "Tasks executed at regular intervals",
                "min_frequency": 5,
                "interval_tolerance": 0.2,
            }
        },
        "decision": {
            "conditional": {
                "description": "If-then decision patterns",
                "indicators": ["如果", "当", "if", "when", "条件"],
            },
            "threshold": {
                "description": "Threshold-based decisions",
                "indicators": ["超过", "大于", "exceed", ">", ">="],
            }
        },
        "error": {
            "recovery": {
                "description": "Error recovery patterns",
                "indicators": ["重试", "回滚", "retry", "rollback", "恢复"],
            },
            "prevention": {
                "description": "Error prevention patterns",
                "indicators": ["检查", "验证", "check", "validate", "verify"],
            }
        },
        "optimization": {
            "batching": {
                "description": "Task batching patterns",
                "indicators": ["批量", "合并", "batch", "merge"],
            },
            "caching": {
                "description": "Caching patterns",
                "indicators": ["缓存", "暂存", "cache", "store"],
            }
        },
        "collaboration": {
            "handoff": {
                "description": "Task handoff patterns between subsystems",
                "min_frequency": 2,
            },
            "synchronization": {
                "description": "Synchronization patterns",
                "indicators": ["同步", "协调", "sync", "coordinate"],
            }
        }
    }

    def __init__(self, knowledge_graph, config: dict = None):
        self.kg = knowledge_graph
        self.config = config or {}
        self.patterns: list[Pattern] = []

    def extract_patterns(self, scope: str = "all") -> dict:
        """
        Extract patterns from execution history.

        Args:
            scope: "all", "global", or subsystem_id

        Returns:
            Dict with extracted patterns
        """
        # Get execution history
        history = self._get_execution_history(scope)

        patterns = []

        # Extract each pattern type
        for pattern_type, rules in self.PATTERN_RULES.items():
            type_patterns = self._extract_type_patterns(pattern_type, rules, history)
            patterns.extend(type_patterns)

        # Sort by frequency and confidence
        patterns.sort(key=lambda p: (p.frequency * p.confidence), reverse=True)

        self.patterns = patterns

        return {
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "type": p.pattern_type,
                    "description": p.description,
                    "frequency": p.frequency,
                    "confidence": p.confidence,
                    "examples": p.examples[:3]
                }
                for p in patterns
            ],
            "total_patterns": len(patterns),
            "by_type": self._group_by_type(patterns)
        }

    def extract_from_execution(self, execution: dict) -> list[dict]:
        """
        Extract patterns from a single execution.

        Args:
            execution: Single execution record

        Returns:
            List of detected patterns
        """
        patterns = []

        # Check for workflow patterns
        task_sequence = execution.get("task_sequence", [])
        if len(task_sequence) >= 2:
            patterns.append({
                "type": "workflow",
                "subtype": "sequential",
                "sequence": task_sequence,
                "context": execution.get("context")
            })

        # Check for decision patterns
        decisions = execution.get("decisions", [])
        for decision in decisions:
            if decision.get("condition"):
                patterns.append({
                    "type": "decision",
                    "subtype": "conditional",
                    "condition": decision.get("condition"),
                    "outcome": decision.get("outcome")
                })

        # Check for error patterns
        if execution.get("status") == "failed":
            patterns.append({
                "type": "error",
                "subtype": "failure",
                "error": execution.get("error"),
                "context": execution.get("context"),
                "recovery_attempted": execution.get("recovery_attempted", False)
            })
        elif execution.get("recovery_used"):
            patterns.append({
                "type": "error",
                "subtype": "recovery",
                "recovery_method": execution.get("recovery_used")
            })

        # Check for collaboration patterns
        subsystems_involved = execution.get("subsystems_involved", [])
        if len(subsystems_involved) > 1:
            patterns.append({
                "type": "collaboration",
                "subtype": "multi_subsystem",
                "subsystems": subsystems_involved,
                "interaction_type": execution.get("interaction_type")
            })

        return patterns

    def _extract_type_patterns(
        self,
        pattern_type: str,
        rules: dict,
        history: list[dict]
    ) -> list[Pattern]:
        """Extract patterns of a specific type."""
        patterns = []

        if pattern_type == "workflow":
            patterns.extend(self._extract_workflow_patterns(rules, history))
        elif pattern_type == "decision":
            patterns.extend(self._extract_decision_patterns(rules, history))
        elif pattern_type == "error":
            patterns.extend(self._extract_error_patterns(rules, history))
        elif pattern_type == "optimization":
            patterns.extend(self._extract_optimization_patterns(rules, history))
        elif pattern_type == "collaboration":
            patterns.extend(self._extract_collaboration_patterns(rules, history))

        return patterns

    def _extract_workflow_patterns(self, rules: dict, history: list) -> list[Pattern]:
        """Extract workflow patterns."""
        patterns = []

        # Sequential task patterns
        task_sequences = []
        for record in history:
            tasks = record.get("tasks", [])
            if len(tasks) >= 2:
                for i in range(len(tasks) - 1):
                    seq = (tasks[i].get("type"), tasks[i+1].get("type"))
                    task_sequences.append(seq)

        # Count frequencies
        seq_counter = Counter(task_sequences)

        for seq, count in seq_counter.items():
            if count >= rules.get("sequential_tasks", {}).get("min_frequency", 3):
                patterns.append(Pattern(
                    pattern_id=f"workflow_seq_{len(patterns)}",
                    pattern_type="workflow",
                    description=f"Common sequence: {seq[0]} → {seq[1]}",
                    frequency=count,
                    confidence=min(0.95, count / 10),
                    examples=[f"{seq[0]} followed by {seq[1]}"]
                ))

        return patterns

    def _extract_decision_patterns(self, rules: dict, history: list) -> list[Pattern]:
        """Extract decision patterns."""
        patterns = []
        indicators = rules.get("conditional", {}).get("indicators", [])

        decision_records = []
        for record in history:
            decisions = record.get("decisions", [])
            for decision in decisions:
                decision_text = str(decision.get("condition", ""))
                if any(ind in decision_text.lower() for ind in indicators):
                    decision_records.append(decision)

        # Group similar decisions
        decision_groups = {}
        for decision in decision_records:
            key = decision.get("type", "unknown")
            if key not in decision_groups:
                decision_groups[key] = []
            decision_groups[key].append(decision)

        for decision_type, decisions in decision_groups.items():
            if len(decisions) >= 2:
                patterns.append(Pattern(
                    pattern_id=f"decision_{decision_type}",
                    pattern_type="decision",
                    description=f"Common decision: {decision_type}",
                    frequency=len(decisions),
                    confidence=0.8,
                    examples=[d.get("condition", "")[:50] for d in decisions[:3]]
                ))

        return patterns

    def _extract_error_patterns(self, rules: dict, history: list) -> list[Pattern]:
        """Extract error and recovery patterns."""
        patterns = []

        # Error patterns
        errors = []
        for record in history:
            if record.get("status") == "failed":
                error_type = record.get("error_type", "unknown")
                errors.append(error_type)

        error_counter = Counter(errors)
        for error_type, count in error_counter.items():
            if count >= 2:
                patterns.append(Pattern(
                    pattern_id=f"error_{error_type}",
                    pattern_type="error",
                    description=f"Recurring error: {error_type}",
                    frequency=count,
                    confidence=0.9,
                    examples=[f"Error occurred {count} times"],
                    metadata={"severity": "high" if count >= 5 else "medium"}
                ))

        # Recovery patterns
        recoveries = []
        for record in history:
            if record.get("recovery_used"):
                recoveries.append(record.get("recovery_used"))

        recovery_counter = Counter(recoveries)
        for recovery_method, count in recovery_counter.items():
            if count >= 2:
                patterns.append(Pattern(
                    pattern_id=f"recovery_{recovery_method}",
                    pattern_type="error",
                    description=f"Effective recovery: {recovery_method}",
                    frequency=count,
                    confidence=0.85,
                    examples=[f"Recovery succeeded {count} times"],
                    metadata={"subtype": "recovery"}
                ))

        return patterns

    def _extract_optimization_patterns(self, rules: dict, history: list) -> list[Pattern]:
        """Extract optimization patterns."""
        patterns = []

        # Look for time improvements
        time_improvements = []
        for record in history:
            if record.get("optimization_applied"):
                time_improvements.append(record.get("optimization_applied"))

        if time_improvements:
            opt_counter = Counter(time_improvements)
            for opt, count in opt_counter.items():
                if count >= 2:
                    patterns.append(Pattern(
                        pattern_id=f"optimization_{opt}",
                        pattern_type="optimization",
                        description=f"Effective optimization: {opt}",
                        frequency=count,
                        confidence=0.8,
                        examples=[f"Applied {count} times"]
                    ))

        return patterns

    def _extract_collaboration_patterns(self, rules: dict, history: list) -> list[Pattern]:
        """Extract collaboration patterns."""
        patterns = []

        # Cross-subsystem interactions
        interactions = []
        for record in history:
            subsystems = record.get("subsystems_involved", [])
            if len(subsystems) >= 2:
                interactions.append(tuple(sorted(subsystems)))

        interaction_counter = Counter(interactions)
        for subsystems, count in interaction_counter.items():
            if count >= rules.get("handoff", {}).get("min_frequency", 2):
                patterns.append(Pattern(
                    pattern_id=f"collaboration_{'_'.join(subsystems)}",
                    pattern_type="collaboration",
                    description=f"Frequent collaboration: {' ↔ '.join(subsystems)}",
                    frequency=count,
                    confidence=0.85,
                    examples=[f"Collaborated {count} times"]
                ))

        return patterns

    def _get_execution_history(self, scope: str) -> list[dict]:
        """Get execution history from knowledge graph."""
        # This would query the actual execution logs
        # For now, return mock data
        return []

    def _group_by_type(self, patterns: list[Pattern]) -> dict:
        """Group patterns by type."""
        grouped = {}
        for p in patterns:
            if p.pattern_type not in grouped:
                grouped[p.pattern_type] = 0
            grouped[p.pattern_type] += 1
        return grouped

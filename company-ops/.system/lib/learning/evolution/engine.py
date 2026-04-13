"""
Specification Evolution Engine for company-ops learning system.

Evolves specifications based on patterns and feedback.
"""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import yaml
import json
import copy


@dataclass
class EvolutionProposal:
    """Represents a proposed specification evolution."""
    proposal_id: str
    target_spec: str  # Path to specification file
    change_type: str  # "add", "modify", "remove", "restructure"
    changes: list[dict]
    rationale: str
    impact: str  # "low", "medium", "high"
    status: str  # "proposed", "approved", "applied", "rejected"
    created_at: str
    confidence: float


@dataclass
class EvolutionResult:
    """Result of specification evolution."""
    proposals_generated: int
    proposals_applied: int
    changes: list[dict]
    recommendations: list[str]


class SpecificationEvolver:
    """
    Evolves specifications based on learned patterns and feedback.

    Evolution types:
    - Add: Add new rules, constraints, or patterns
    - Modify: Update existing rules based on new data
    - Remove: Remove obsolete or problematic rules
    - Restructure: Reorganize for clarity or efficiency
    """

    # Evolution rules
    EVOLUTION_TRIGGERS = {
        "pattern_frequency": {
            "threshold": 5,
            "action": "add_pattern",
            "description": "Add pattern when observed N+ times"
        },
        "error_frequency": {
            "threshold": 3,
            "action": "add_constraint",
            "description": "Add constraint after N+ errors"
        },
        "rejection_rate": {
            "threshold": 0.3,
            "action": "review_specification",
            "description": "Review spec when rejection rate > 30%"
        },
        "optimization_gain": {
            "threshold": 0.2,
            "action": "update_default",
            "description": "Update default when optimization shows 20%+ improvement"
        }
    }

    def __init__(self, knowledge_graph, config: dict = None):
        self.kg = knowledge_graph
        self.config = config or {}
        self.base_path = Path(self.config.get("base_path", "."))

        self.proposals: list[EvolutionProposal] = []
        self.applied_changes: list[dict] = []

    def evolve(self, scope: str = "all") -> dict:
        """
        Run specification evolution.

        Args:
            scope: "all", "global", or subsystem_id

        Returns:
            Evolution result
        """
        changes = []
        recommendations = []
        proposals_applied = 0

        # Generate proposals from patterns
        pattern_proposals = self._generate_pattern_proposals(scope)
        self.proposals.extend(pattern_proposals)

        # Generate proposals from feedback
        feedback_proposals = self._generate_feedback_proposals(scope)
        self.proposals.extend(feedback_proposals)

        # Apply safe proposals automatically
        for proposal in self.proposals:
            if proposal.status != "proposed":
                continue

            if self._can_auto_apply(proposal):
                applied = self._apply_proposal(proposal)
                if applied:
                    changes.append({
                        "proposal_id": proposal.proposal_id,
                        "target": proposal.target_spec,
                        "type": proposal.change_type,
                        "summary": proposal.rationale
                    })
                    proposals_applied += 1
                    proposal.status = "applied"
            else:
                recommendations.append(
                    f"Review proposal {proposal.proposal_id}: {proposal.rationale}"
                )

        return {
            "updated": proposals_applied,
            "changes": changes,
            "recommendations": recommendations,
            "pending_proposals": len([p for p in self.proposals if p.status == "proposed"])
        }

    def propose_change(
        self,
        target_spec: str,
        change_type: str,
        changes: list[dict],
        rationale: str,
        impact: str = "medium"
    ) -> EvolutionProposal:
        """
        Create a new evolution proposal.

        Args:
            target_spec: Path to specification file
            change_type: Type of change
            changes: List of changes to make
            rationale: Why this change is needed
            impact: Impact level

        Returns:
            EvolutionProposal
        """
        proposal = EvolutionProposal(
            proposal_id=self._generate_id(),
            target_spec=target_spec,
            change_type=change_type,
            changes=changes,
            rationale=rationale,
            impact=impact,
            status="proposed",
            created_at=datetime.now().isoformat(),
            confidence=0.7
        )

        self.proposals.append(proposal)
        return proposal

    def approve_proposal(self, proposal_id: str) -> bool:
        """Approve a proposal for application."""
        proposal = self._get_proposal(proposal_id)
        if not proposal:
            return False

        proposal.status = "approved"
        return self._apply_proposal(proposal)

    def reject_proposal(self, proposal_id: str, reason: str = "") -> bool:
        """Reject a proposal."""
        proposal = self._get_proposal(proposal_id)
        if not proposal:
            return False

        proposal.status = "rejected"
        return True

    def _generate_pattern_proposals(self, scope: str) -> list[EvolutionProposal]:
        """Generate proposals from extracted patterns."""
        proposals = []

        # Get patterns from knowledge graph
        # This would query the PatternExtractor results
        patterns = self._get_patterns(scope)

        for pattern in patterns:
            if pattern.get("frequency", 0) >= self.EVOLUTION_TRIGGERS["pattern_frequency"]["threshold"]:
                proposal = EvolutionProposal(
                    proposal_id=self._generate_id(),
                    target_spec=self._get_spec_for_pattern(pattern),
                    change_type="add",
                    changes=[{
                        "type": "add_pattern",
                        "pattern": pattern
                    }],
                    rationale=f"Pattern observed {pattern.get('frequency')} times: {pattern.get('description')}",
                    impact="low",
                    status="proposed",
                    created_at=datetime.now().isoformat(),
                    confidence=min(0.9, pattern.get("frequency", 0) / 10)
                )
                proposals.append(proposal)

        return proposals

    def _generate_feedback_proposals(self, scope: str) -> list[EvolutionProposal]:
        """Generate proposals from processed feedback."""
        proposals = []

        # Get feedback summaries
        feedback_items = self._get_feedback_summaries(scope)

        for feedback in feedback_items:
            if feedback.get("type") == "rejection":
                # Propose constraint addition
                proposal = EvolutionProposal(
                    proposal_id=self._generate_id(),
                    target_spec=feedback.get("target_spec", "CONSTITUTION.yaml"),
                    change_type="add",
                    changes=[{
                        "type": "add_constraint",
                        "constraint": feedback.get("content", ""),
                        "context": feedback.get("context", {})
                    }],
                    rationale=f"Constraint suggested by rejection feedback",
                    impact="medium",
                    status="proposed",
                    created_at=datetime.now().isoformat(),
                    confidence=0.6
                )
                proposals.append(proposal)

        return proposals

    def _can_auto_apply(self, proposal: EvolutionProposal) -> bool:
        """Check if a proposal can be auto-applied."""
        # Only low-impact proposals can be auto-applied
        if proposal.impact != "low":
            return False

        # High confidence required
        if proposal.confidence < 0.8:
            return False

        # Add operations are safer than modify/remove
        if proposal.change_type not in ("add",):
            return False

        return True

    def _apply_proposal(self, proposal: EvolutionProposal) -> bool:
        """Apply a proposal to the specification."""
        target_path = self.base_path / proposal.target_spec

        if not target_path.exists():
            return False

        try:
            # Read current spec
            if target_path.suffix in (".yaml", ".yml"):
                with open(target_path, "r", encoding="utf-8") as f:
                    spec = yaml.safe_load(f)
            else:
                with open(target_path, "r", encoding="utf-8") as f:
                    spec = json.load(f)

            # Apply changes
            original_spec = copy.deepcopy(spec)
            for change in proposal.changes:
                spec = self._apply_change(spec, change)

            # Validate change didn't break structure
            if not self._validate_spec(spec):
                return False

            # Write updated spec
            if target_path.suffix in (".yaml", ".yml"):
                with open(target_path, "w", encoding="utf-8") as f:
                    yaml.dump(spec, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            else:
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(spec, f, indent=2, ensure_ascii=False)

            # Record change
            self.applied_changes.append({
                "proposal_id": proposal.proposal_id,
                "target": proposal.target_spec,
                "timestamp": datetime.now().isoformat(),
                "original": original_spec,
                "updated": spec
            })

            return True

        except Exception as e:
            print(f"Error applying proposal: {e}")
            return False

    def _apply_change(self, spec: dict, change: dict) -> dict:
        """Apply a single change to a specification."""
        change_type = change.get("type")

        if change_type == "add_pattern":
            patterns = spec.setdefault("learned_patterns", [])
            patterns.append(change.get("pattern"))

        elif change_type == "add_constraint":
            constraints = spec.setdefault("learned_constraints", [])
            constraints.append({
                "constraint": change.get("constraint"),
                "source": "evolution",
                "added_at": datetime.now().isoformat()
            })

        elif change_type == "update_value":
            path = change.get("path", "").split(".")
            value = change.get("value")
            self._set_nested_value(spec, path, value)

        return spec

    def _set_nested_value(self, obj: dict, path: list, value):
        """Set a nested value in a dict."""
        for key in path[:-1]:
            obj = obj.setdefault(key, {})
        if path:
            obj[path[-1]] = value

    def _validate_spec(self, spec: dict) -> bool:
        """Validate that spec structure is valid."""
        # Basic validation - can be extended
        return isinstance(spec, dict)

    def _get_proposal(self, proposal_id: str) -> Optional[EvolutionProposal]:
        """Get a proposal by ID."""
        for p in self.proposals:
            if p.proposal_id == proposal_id:
                return p
        return None

    def _get_patterns(self, scope: str) -> list[dict]:
        """Get patterns from knowledge graph."""
        # Would query PatternExtractor results
        return []

    def _get_feedback_summaries(self, scope: str) -> list[dict]:
        """Get feedback summaries."""
        # Would query FeedbackProcessor results
        return []

    def _get_spec_for_pattern(self, pattern: dict) -> str:
        """Determine which spec file to update for a pattern."""
        pattern_type = pattern.get("type", "")
        subsystem = pattern.get("subsystem_id", "")

        if subsystem and subsystem != "global":
            return f"subsystems/{subsystem}/SPEC.md"

        return "CONSTITUTION.yaml"

    def _generate_id(self) -> str:
        """Generate a unique proposal ID."""
        import uuid
        return f"evo-{uuid.uuid4().hex[:8]}"

"""
Knowledge Synchronizer for company-ops learning system.

Shares learnings across subsystems and maintains knowledge consistency.
"""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json


@dataclass
class SharedKnowledge:
    """Represents shared knowledge item."""
    knowledge_id: str
    knowledge_type: str  # "pattern", "constraint", "optimization", "best_practice"
    source_subsystem: str
    target_subsystems: list[str]
    content: dict
    relevance_score: float
    created_at: str
    applied_at: Optional[str] = None


@dataclass
class SynchronizationResult:
    """Result of knowledge synchronization."""
    shared: int
    applied: int
    conflicts: list[dict]
    recommendations: list[str]


class KnowledgeSynchronizer:
    """
    Synchronizes knowledge across subsystems.

    Sharing types:
    - Pattern sharing: Reusable patterns between similar subsystems
    - Constraint propagation: Safety constraints to all subsystems
    - Best practice diffusion: Successful practices to others
    - Warning propagation: Error patterns to avoid
    """

    # Knowledge sharing rules
    SHARING_RULES = {
        "pattern": {
            "share_scope": "similar",  # "all", "similar", "related"
            "min_confidence": 0.7,
            "requires_consent": False,
        },
        "constraint": {
            "share_scope": "all",
            "min_confidence": 0.5,
            "requires_consent": False,
        },
        "best_practice": {
            "share_scope": "similar",
            "min_confidence": 0.8,
            "requires_consent": True,
        },
        "warning": {
            "share_scope": "all",
            "min_confidence": 0.6,
            "requires_consent": False,
        }
    }

    def __init__(self, knowledge_graph, config: dict = None):
        self.kg = knowledge_graph
        self.config = config or {}
        self.base_path = Path(self.config.get("base_path", "."))

        self.shared_knowledge: list[SharedKnowledge] = []
        self.sync_history: list[dict] = []

    def synchronize(self, scope: str = "all") -> dict:
        """
        Run knowledge synchronization.

        Args:
            scope: "all", "global", or subsystem_id

        Returns:
            Synchronization result
        """
        shared_count = 0
        applied_count = 0
        conflicts = []
        recommendations = []

        # Get subsystems to sync
        subsystems = self._get_subsystems(scope)

        # Collect knowledge to share
        knowledge_items = self._collect_shareable_knowledge(subsystems)

        # Share to appropriate targets
        for item in knowledge_items:
            targets = self._determine_targets(item, subsystems)

            for target in targets:
                share_result = self._share_to_subsystem(item, target)

                if share_result.get("shared"):
                    shared_count += 1

                if share_result.get("applied"):
                    applied_count += 1

                if share_result.get("conflict"):
                    conflicts.append({
                        "knowledge_id": item.knowledge_id,
                        "target": target,
                        "conflict": share_result.get("conflict")
                    })

        # Record sync
        self.sync_history.append({
            "timestamp": datetime.now().isoformat(),
            "scope": scope,
            "shared": shared_count,
            "applied": applied_count,
            "conflicts": len(conflicts)
        })

        return {
            "shared": shared_count,
            "applied": applied_count,
            "conflicts": conflicts,
            "recommendations": recommendations
        }

    def share_knowledge(
        self,
        knowledge_type: str,
        source: str,
        content: dict,
        targets: list[str] = None
    ) -> SharedKnowledge:
        """
        Explicitly share knowledge.

        Args:
            knowledge_type: Type of knowledge
            source: Source subsystem
            content: Knowledge content
            targets: Optional specific targets

        Returns:
            SharedKnowledge item
        """
        item = SharedKnowledge(
            knowledge_id=self._generate_id(),
            knowledge_type=knowledge_type,
            source_subsystem=source,
            target_subsystems=targets or [],
            content=content,
            relevance_score=self._calculate_relevance(content),
            created_at=datetime.now().isoformat()
        )

        self.shared_knowledge.append(item)

        # Persist
        self._persist_shared_knowledge(item)

        return item

    def get_knowledge_for_subsystem(self, subsystem_id: str) -> list[dict]:
        """Get all shared knowledge relevant to a subsystem."""
        relevant = []

        for item in self.shared_knowledge:
            if self._is_relevant_to(item, subsystem_id):
                relevant.append({
                    "knowledge_id": item.knowledge_id,
                    "type": item.knowledge_type,
                    "source": item.source_subsystem,
                    "content": item.content,
                    "relevance": item.relevance_score
                })

        # Sort by relevance
        relevant.sort(key=lambda x: x["relevance"], reverse=True)

        return relevant

    def apply_knowledge(
        self,
        knowledge_id: str,
        target_subsystem: str
    ) -> dict:
        """
        Apply shared knowledge to a subsystem.

        Args:
            knowledge_id: ID of knowledge to apply
            target_subsystem: Target subsystem

        Returns:
            Application result
        """
        item = self._get_knowledge(knowledge_id)
        if not item:
            return {"success": False, "error": "Knowledge not found"}

        # Check if already applied
        if item.applied_at:
            return {"success": False, "error": "Already applied"}

        # Apply to subsystem
        result = self._apply_to_subsystem(item, target_subsystem)

        if result.get("success"):
            item.applied_at = datetime.now().isoformat()
            if target_subsystem not in item.target_subsystems:
                item.target_subsystems.append(target_subsystem)

        return result

    def _collect_shareable_knowledge(self, subsystems: list[str]) -> list[SharedKnowledge]:
        """Collect knowledge that can be shared."""
        items = []

        for subsystem_id in subsystems:
            # Get patterns from subsystem
            patterns = self._get_subsystem_patterns(subsystem_id)
            for pattern in patterns:
                if self._is_shareable("pattern", pattern):
                    items.append(SharedKnowledge(
                        knowledge_id=self._generate_id(),
                        knowledge_type="pattern",
                        source_subsystem=subsystem_id,
                        target_subsystems=[],
                        content=pattern,
                        relevance_score=pattern.get("confidence", 0.5),
                        created_at=datetime.now().isoformat()
                    ))

            # Get constraints from subsystem
            constraints = self._get_subsystem_constraints(subsystem_id)
            for constraint in constraints:
                if self._is_shareable("constraint", constraint):
                    items.append(SharedKnowledge(
                        knowledge_id=self._generate_id(),
                        knowledge_type="constraint",
                        source_subsystem=subsystem_id,
                        target_subsystems=[],
                        content=constraint,
                        relevance_score=0.9,
                        created_at=datetime.now().isoformat()
                    ))

        return items

    def _determine_targets(
        self,
        item: SharedKnowledge,
        subsystems: list[str]
    ) -> list[str]:
        """Determine which subsystems should receive knowledge."""
        rules = self.SHARING_RULES.get(item.knowledge_type, {})
        scope = rules.get("share_scope", "similar")

        targets = []

        for sub_id in subsystems:
            if sub_id == item.source_subsystem:
                continue

            if scope == "all":
                targets.append(sub_id)
            elif scope == "similar":
                if self._are_similar(item.source_subsystem, sub_id):
                    targets.append(sub_id)
            elif scope == "related":
                if self._are_related(item.source_subsystem, sub_id):
                    targets.append(sub_id)

        return targets

    def _share_to_subsystem(
        self,
        item: SharedKnowledge,
        target: str
    ) -> dict:
        """Share knowledge to a specific subsystem."""
        result = {
            "shared": False,
            "applied": False,
            "conflict": None
        }

        # Check for conflicts
        conflict = self._check_conflict(item, target)
        if conflict:
            result["conflict"] = conflict
            return result

        # Add to subsystem's knowledge inbox
        inbox_path = self.base_path / "subsystems" / target / "inbox" / f"knowledge_{item.knowledge_id}.json"

        try:
            inbox_path.parent.mkdir(parents=True, exist_ok=True)

            with open(inbox_path, "w", encoding="utf-8") as f:
                json.dump({
                    "knowledge_id": item.knowledge_id,
                    "type": item.knowledge_type,
                    "source": item.source_subsystem,
                    "content": item.content,
                    "relevance": item.relevance_score,
                    "received_at": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            result["shared"] = True

            # Auto-apply if rules allow
            rules = self.SHARING_RULES.get(item.knowledge_type, {})
            if not rules.get("requires_consent") and item.relevance_score >= rules.get("min_confidence", 0.5):
                apply_result = self._apply_to_subsystem(item, target)
                result["applied"] = apply_result.get("success", False)

        except Exception as e:
            result["conflict"] = str(e)

        return result

    def _apply_to_subsystem(
        self,
        item: SharedKnowledge,
        target: str
    ) -> dict:
        """Apply knowledge to subsystem's local graph."""
        try:
            # Update local graph
            graph_path = self.base_path / "subsystems" / target / "local-graph.json"

            if graph_path.exists():
                with open(graph_path, "r", encoding="utf-8") as f:
                    graph = json.load(f)

                # Add learned entity
                entity = {
                    "id": f"learned.{item.knowledge_id}",
                    "type": "learning",
                    "name": f"Learned {item.knowledge_type}",
                    "description": f"Learned from {item.source_subsystem}",
                    "properties": {
                        "knowledge_type": item.knowledge_type,
                        "source": item.source_subsystem,
                        "content": item.content,
                        "applied_at": datetime.now().isoformat()
                    },
                    "tags": ["learned", item.knowledge_type]
                }

                graph.setdefault("entities", []).append(entity)

                with open(graph_path, "w", encoding="utf-8") as f:
                    json.dump(graph, f, ensure_ascii=False, indent=2)

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _is_shareable(self, knowledge_type: str, content: dict) -> bool:
        """Check if knowledge is shareable."""
        rules = self.SHARING_RULES.get(knowledge_type, {})
        confidence = content.get("confidence", 0)
        return confidence >= rules.get("min_confidence", 0.5)

    def _is_relevant_to(self, item: SharedKnowledge, subsystem_id: str) -> bool:
        """Check if knowledge is relevant to a subsystem."""
        # Similar subsystems get similar knowledge
        if self._are_similar(item.source_subsystem, subsystem_id):
            return True

        # Global knowledge is relevant to all
        if item.source_subsystem == "global":
            return True

        return item.relevance_score > 0.7

    def _are_similar(self, sub1: str, sub2: str) -> bool:
        """Check if two subsystems are similar."""
        # Same type subsystems are similar
        # This could be enhanced with semantic similarity
        sub1_type = sub1.split("/")[0] if "/" in sub1 else sub1
        sub2_type = sub2.split("/")[0] if "/" in sub2 else sub2

        return sub1_type == sub2_type

    def _are_related(self, sub1: str, sub2: str) -> bool:
        """Check if two subsystems are related (have dependencies)."""
        # Check knowledge graph for relations
        relations = self.kg.get_relations(f"subsystem.{sub1}")
        for rel in relations:
            if sub2 in rel.get("target", ""):
                return True
        return False

    def _check_conflict(self, item: SharedKnowledge, target: str) -> Optional[str]:
        """Check for conflicts when sharing."""
        # Check if conflicting knowledge exists
        target_knowledge = self.get_knowledge_for_subsystem(target)

        for existing in target_knowledge:
            if existing["type"] == item.knowledge_type:
                # Simple conflict detection
                if self._content_conflicts(existing["content"], item.content):
                    return f"Conflicts with existing {item.knowledge_type}"

        return None

    def _content_conflicts(self, content1: dict, content2: dict) -> bool:
        """Check if two contents conflict."""
        # Simplified conflict detection
        # Would need more sophisticated comparison
        return False

    def _calculate_relevance(self, content: dict) -> float:
        """Calculate relevance score for content."""
        return content.get("confidence", 0.5)

    def _get_subsystems(self, scope: str) -> list[str]:
        """Get list of subsystems."""
        if scope == "all":
            # Get from registry
            registry_path = self.base_path / "subsystems" / "_registry.json"
            if registry_path.exists():
                with open(registry_path, "r", encoding="utf-8") as f:
                    registry = json.load(f)
                return [s.get("id") for s in registry.get("subsystems", [])]
        return [scope] if scope != "all" else []

    def _get_subsystem_patterns(self, subsystem_id: str) -> list[dict]:
        """Get patterns from a subsystem."""
        return []

    def _get_subsystem_constraints(self, subsystem_id: str) -> list[dict]:
        """Get constraints from a subsystem."""
        return []

    def _get_knowledge(self, knowledge_id: str) -> Optional[SharedKnowledge]:
        """Get knowledge by ID."""
        for item in self.shared_knowledge:
            if item.knowledge_id == knowledge_id:
                return item
        return None

    def _persist_shared_knowledge(self, item: SharedKnowledge):
        """Persist shared knowledge to disk."""
        sharing_dir = self.base_path / ".system" / "learning" / "shared"
        sharing_dir.mkdir(parents=True, exist_ok=True)

        file_path = sharing_dir / f"{item.knowledge_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({
                "knowledge_id": item.knowledge_id,
                "type": item.knowledge_type,
                "source": item.source_subsystem,
                "targets": item.target_subsystems,
                "content": item.content,
                "relevance": item.relevance_score,
                "created_at": item.created_at,
                "applied_at": item.applied_at
            }, f, ensure_ascii=False, indent=2)

    def _generate_id(self) -> str:
        """Generate a unique knowledge ID."""
        import uuid
        return f"know-{uuid.uuid4().hex[:8]}"

"""
Graph Updater for company-ops knowledge graphs.

Handles updates to knowledge graph files.
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from .index import GraphIndex


class GraphUpdater:
    """Handles updates to knowledge graph files."""

    def __init__(self, base_path: str, index: GraphIndex):
        self.base_path = Path(base_path)
        self.index = index

    def add_entity(self, entity: dict, scope: str = "global") -> bool:
        """
        Add a new entity to a graph.

        Args:
            entity: Entity data (must have id, type, name)
            scope: "global" or subsystem_id

        Returns:
            Success status
        """
        # Validate required fields
        required = ["id", "type", "name"]
        if not all(field in entity for field in required):
            return False

        # Check if entity already exists
        if self.index.get_entity(entity["id"]):
            return False

        # Add timestamps
        now = datetime.now().isoformat()
        if "created_at" not in entity:
            entity["created_at"] = now
        entity["updated_at"] = now

        # Load graph
        graph = self._load_graph(scope)
        if not graph:
            return False

        # Add entity
        graph["entities"].append(entity)

        # Update metadata
        graph["metadata"]["updated_at"] = now

        # Save graph
        if not self._save_graph(graph, scope):
            return False

        # Update index
        self.index.build_index({**graph, "entities": [entity], "relations": []}, scope)

        return True

    def update_entity(self, entity_id: str, updates: dict, scope: str = "global") -> bool:
        """
        Update an existing entity.

        Args:
            entity_id: Entity ID to update
            updates: Fields to update
            scope: "global" or subsystem_id

        Returns:
            Success status
        """
        # Load graph
        graph = self._load_graph(scope)
        if not graph:
            return False

        # Find entity
        entity = None
        for e in graph["entities"]:
            if e.get("id") == entity_id:
                entity = e
                break

        if not entity:
            return False

        # Apply updates (immutable pattern - create new dict)
        updated_entity = {**entity, **updates}
        updated_entity["updated_at"] = datetime.now().isoformat()

        # Replace in graph
        graph["entities"] = [
            updated_entity if e.get("id") == entity_id else e
            for e in graph["entities"]
        ]

        # Update metadata
        graph["metadata"]["updated_at"] = datetime.now().isoformat()

        # Save graph
        if not self._save_graph(graph, scope):
            return False

        # Update index
        self.index.clear()
        self.index.build_index(graph, scope)

        return True

    def delete_entity(self, entity_id: str, scope: str = "global") -> bool:
        """
        Delete an entity.

        Args:
            entity_id: Entity ID to delete
            scope: "global" or subsystem_id

        Returns:
            Success status
        """
        # Load graph
        graph = self._load_graph(scope)
        if not graph:
            return False

        # Remove entity
        original_count = len(graph["entities"])
        graph["entities"] = [e for e in graph["entities"] if e.get("id") != entity_id]

        if len(graph["entities"]) == original_count:
            return False  # Entity not found

        # Remove related relations
        graph["relations"] = [
            r for r in graph["relations"]
            if r.get("source") != entity_id and r.get("target") != entity_id
        ]

        # Update metadata
        graph["metadata"]["updated_at"] = datetime.now().isoformat()

        # Save graph
        if not self._save_graph(graph, scope):
            return False

        # Update index
        self.index.clear()
        self.index.build_index(graph, scope)

        return True

    def add_relation(self, relation: dict, scope: str = "global") -> bool:
        """
        Add a new relation to a graph.

        Args:
            relation: Relation data (must have type, source, target)
            scope: "global" or subsystem_id

        Returns:
            Success status
        """
        # Validate required fields
        required = ["type", "source", "target"]
        if not all(field in relation for field in required):
            return False

        # Verify source and target exist
        if not self.index.get_entity(relation["source"]):
            return False
        if not self.index.get_entity(relation["target"]):
            return False

        # Add timestamps
        now = datetime.now().isoformat()
        if "created_at" not in relation:
            relation["created_at"] = now

        # Load graph
        graph = self._load_graph(scope)
        if not graph:
            return False

        # Check for duplicate
        for r in graph["relations"]:
            if (r.get("type") == relation["type"] and
                r.get("source") == relation["source"] and
                r.get("target") == relation["target"]):
                return False  # Duplicate

        # Add relation
        graph["relations"].append(relation)

        # Update metadata
        graph["metadata"]["updated_at"] = now

        # Save graph
        if not self._save_graph(graph, scope):
            return False

        # Update index
        self.index._index_relation(relation, scope)

        return True

    def delete_relation(
        self,
        source: str,
        target: str,
        relation_type: str,
        scope: str = "global"
    ) -> bool:
        """
        Delete a relation.

        Args:
            source: Source entity ID
            target: Target entity ID
            relation_type: Relation type
            scope: "global" or subsystem_id

        Returns:
            Success status
        """
        # Load graph
        graph = self._load_graph(scope)
        if not graph:
            return False

        # Remove relation
        original_count = len(graph["relations"])
        graph["relations"] = [
            r for r in graph["relations"]
            if not (r.get("source") == source and
                    r.get("target") == target and
                    r.get("type") == relation_type)
        ]

        if len(graph["relations"]) == original_count:
            return False  # Relation not found

        # Update metadata
        graph["metadata"]["updated_at"] = datetime.now().isoformat()

        # Save graph
        if not self._save_graph(graph, scope):
            return False

        # Update index
        self.index.clear()
        self.index.build_index(graph, scope)

        return True

    def _load_graph(self, scope: str) -> Optional[dict]:
        """Load a graph file."""
        if scope == "global":
            path = self.base_path / "global-graph.json"
        else:
            path = self.base_path / "subsystems" / scope / "local-graph.json"

        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_graph(self, graph: dict, scope: str) -> bool:
        """Save a graph file."""
        if scope == "global":
            path = self.base_path / "global-graph.json"
        else:
            path = self.base_path / "subsystems" / scope / "local-graph.json"

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(graph, f, indent=2, ensure_ascii=False)
                f.write("\n")
            return True
        except Exception:
            return False

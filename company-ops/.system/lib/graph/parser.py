"""
Graph Parser for company-ops knowledge graphs.

Parses global-graph.json, local-graph.json, and _registry.json files.
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class GraphParser:
    """Parses knowledge graph JSON files."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.global_graph_path = self.base_path / "global-graph.json"
        self.subsystems_path = self.base_path / "subsystems"

    def parse_global_graph(self) -> dict:
        """
        Parse the global knowledge graph.

        Returns:
            Parsed graph with metadata, entities, relations, and views
        """
        if not self.global_graph_path.exists():
            return self._empty_graph("global")

        with open(self.global_graph_path, "r", encoding="utf-8") as f:
            graph = json.load(f)

        # Validate structure
        graph = self._validate_graph(graph, "global")

        # Parse timestamps
        graph = self._parse_timestamps(graph)

        return graph

    def parse_local_graph(self, subsystem_id: str) -> dict:
        """
        Parse a subsystem's local knowledge graph.

        Args:
            subsystem_id: Subsystem identifier

        Returns:
            Parsed local graph
        """
        graph_path = self.subsystems_path / subsystem_id / "local-graph.json"

        if not graph_path.exists():
            return self._empty_graph(subsystem_id, is_local=True)

        with open(graph_path, "r", encoding="utf-8") as f:
            graph = json.load(f)

        # Validate structure
        graph = self._validate_graph(graph, subsystem_id, is_local=True)

        # Ensure subsystem_id is set
        if "metadata" in graph:
            graph["metadata"]["subsystem_id"] = subsystem_id

        return graph

    def parse_registry(self) -> dict:
        """
        Parse the subsystem registry.

        Returns:
            Registry data with subsystems list
        """
        registry_path = self.subsystems_path / "_registry.json"

        if not registry_path.exists():
            return {
                "version": "0.0.0",
                "updated_at": datetime.now().isoformat(),
                "subsystems": []
            }

        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)

        return registry

    def parse_all_graphs(self) -> dict:
        """
        Parse all graphs: global + all local graphs.

        Returns:
            Dict with 'global' and 'subsystems' keys
        """
        result = {
            "global": self.parse_global_graph(),
            "subsystems": {}
        }

        registry = self.parse_registry()
        for subsystem in registry.get("subsystems", []):
            subsystem_id = subsystem.get("id")
            if subsystem_id:
                result["subsystems"][subsystem_id] = self.parse_local_graph(subsystem_id)

        return result

    def _empty_graph(self, scope: str, is_local: bool = False) -> dict:
        """Create an empty graph structure."""
        graph = {
            "metadata": {
                "version": "0.0.0",
                "updated_at": datetime.now().isoformat(),
            },
            "entities": [],
            "relations": [],
            "views": {}
        }

        if is_local:
            graph["metadata"]["subsystem_id"] = scope
        else:
            graph["metadata"]["root_namespace"] = scope

        return graph

    def _validate_graph(self, graph: dict, scope: str, is_local: bool = False) -> dict:
        """Validate and normalize graph structure."""
        # Ensure required fields
        if "metadata" not in graph:
            graph["metadata"] = {}

        if "entities" not in graph:
            graph["entities"] = []

        if "relations" not in graph:
            graph["relations"] = []

        if "views" not in graph:
            graph["views"] = {}

        # Validate metadata
        required_meta = ["version", "updated_at"]
        for field in required_meta:
            if field not in graph["metadata"]:
                if field == "version":
                    graph["metadata"][field] = "0.0.0"
                elif field == "updated_at":
                    graph["metadata"][field] = datetime.now().isoformat()

        # Validate entities
        validated_entities = []
        for entity in graph.get("entities", []):
            if self._validate_entity(entity):
                validated_entities.append(entity)

        graph["entities"] = validated_entities

        # Validate relations
        validated_relations = []
        for relation in graph.get("relations", []):
            if self._validate_relation(relation):
                validated_relations.append(relation)

        graph["relations"] = validated_relations

        return graph

    def _validate_entity(self, entity: dict) -> bool:
        """Validate an entity has required fields."""
        if not isinstance(entity, dict):
            return False

        required = ["id", "type", "name"]
        return all(field in entity for field in required)

    def _validate_relation(self, relation: dict) -> bool:
        """Validate a relation has required fields."""
        if not isinstance(relation, dict):
            return False

        required = ["type", "source", "target"]
        return all(field in relation for field in required)

    def _parse_timestamps(self, graph: dict) -> dict:
        """Parse ISO timestamps to datetime objects (stored as strings for JSON)."""
        # Keep timestamps as ISO strings for JSON compatibility
        # This method can be extended for additional parsing if needed
        return graph

    def get_entity_types(self, scope: str = "global") -> list[str]:
        """Get all unique entity types in a graph."""
        if scope == "global":
            graph = self.parse_global_graph()
        else:
            graph = self.parse_local_graph(scope)

        types = set()
        for entity in graph.get("entities", []):
            if "type" in entity:
                types.add(entity["type"])

        return sorted(list(types))

    def get_relation_types(self, scope: str = "global") -> list[str]:
        """Get all unique relation types in a graph."""
        if scope == "global":
            graph = self.parse_global_graph()
        else:
            graph = self.parse_local_graph(scope)

        types = set()
        for relation in graph.get("relations", []):
            if "type" in relation:
                types.add(relation["type"])

        return sorted(list(types))

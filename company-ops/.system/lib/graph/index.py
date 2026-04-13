"""
Graph Index for company-ops knowledge graphs.

Builds and maintains indices for efficient querying.
"""

from typing import Optional
from collections import defaultdict


class GraphIndex:
    """Maintains indices for efficient graph queries."""

    def __init__(self):
        # Entity indices
        self.entities_by_id: dict[str, dict] = {}
        self.entities_by_type: dict[str, list[dict]] = defaultdict(list)
        self.entities_by_tag: dict[str, list[dict]] = defaultdict(list)
        self.entities_by_scope: dict[str, list[dict]] = defaultdict(list)

        # Relation indices
        self.relations_by_source: dict[str, list[dict]] = defaultdict(list)
        self.relations_by_target: dict[str, list[dict]] = defaultdict(list)
        self.relations_by_type: dict[str, list[dict]] = defaultdict(list)

        # View indices
        self.views_by_scope: dict[str, dict[str, list[str]]] = defaultdict(dict)

        # Scope tracking
        self.entity_scope: dict[str, str] = {}  # entity_id -> scope

    def build_index(self, graph: dict, scope: str = "global"):
        """
        Build indices from a graph.

        Args:
            graph: Parsed graph data
            scope: Scope identifier (global or subsystem_id)
        """
        # Index entities
        for entity in graph.get("entities", []):
            self._index_entity(entity, scope)

        # Index relations
        for relation in graph.get("relations", []):
            self._index_relation(relation, scope)

        # Index views
        for view_name, view_items in graph.get("views", {}).items():
            self.views_by_scope[scope][view_name] = view_items

    def build_subsystem_index(self, subsystem_id: str, graph: dict):
        """Build indices for a subsystem graph."""
        self.build_index(graph, scope=subsystem_id)

    def _index_entity(self, entity: dict, scope: str):
        """Index a single entity."""
        entity_id = entity.get("id")
        if not entity_id:
            return

        # Store by ID
        self.entities_by_id[entity_id] = entity
        self.entity_scope[entity_id] = scope
        self.entities_by_scope[scope].append(entity)

        # Index by type
        entity_type = entity.get("type")
        if entity_type:
            self.entities_by_type[entity_type].append(entity)

        # Index by tags
        for tag in entity.get("tags", []):
            self.entities_by_tag[tag].append(entity)

    def _index_relation(self, relation: dict, scope: str):
        """Index a single relation."""
        relation_id = relation.get("id")
        source = relation.get("source")
        target = relation.get("target")
        rel_type = relation.get("type")

        # Store scope on relation
        relation["_scope"] = scope

        # Index by source
        if source:
            self.relations_by_source[source].append(relation)

        # Index by target
        if target:
            self.relations_by_target[target].append(relation)

        # Index by type
        if rel_type:
            self.relations_by_type[rel_type].append(relation)

    def get_entity(self, entity_id: str) -> Optional[dict]:
        """Get entity by ID."""
        return self.entities_by_id.get(entity_id)

    def get_entities_by_type(self, entity_type: str) -> list[dict]:
        """Get all entities of a type."""
        return self.entities_by_type.get(entity_type, [])

    def get_entities_by_tag(self, tag: str) -> list[dict]:
        """Get all entities with a tag."""
        return self.entities_by_tag.get(tag, [])

    def get_entities_by_scope(self, scope: str) -> list[dict]:
        """Get all entities in a scope."""
        return self.entities_by_scope.get(scope, [])

    def get_outgoing_relations(self, entity_id: str) -> list[dict]:
        """Get relations where entity is source."""
        return self.relations_by_source.get(entity_id, [])

    def get_incoming_relations(self, entity_id: str) -> list[dict]:
        """Get relations where entity is target."""
        return self.relations_by_target.get(entity_id, [])

    def get_relations_by_type(self, relation_type: str) -> list[dict]:
        """Get all relations of a type."""
        return self.relations_by_type.get(relation_type, [])

    def get_view(self, view_name: str, scope: str = "global") -> list[str]:
        """Get a view by name and scope."""
        return self.views_by_scope.get(scope, {}).get(view_name, [])

    def search_entities(self, query: str, fields: list[str] = None) -> list[dict]:
        """
        Search entities by query string.

        Args:
            query: Search query (case-insensitive substring match)
            fields: Fields to search in (default: id, name, description)

        Returns:
            List of matching entities
        """
        if fields is None:
            fields = ["id", "name", "description"]

        query_lower = query.lower()
        results = []

        for entity in self.entities_by_id.values():
            for field in fields:
                value = entity.get(field, "")
                if isinstance(value, str) and query_lower in value.lower():
                    results.append(entity)
                    break

        return results

    def get_entity_scope(self, entity_id: str) -> Optional[str]:
        """Get the scope of an entity."""
        return self.entity_scope.get(entity_id)

    def get_all_scopes(self) -> list[str]:
        """Get all known scopes."""
        return list(self.entities_by_scope.keys())

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            "total_entities": len(self.entities_by_id),
            "total_relations": sum(len(r) for r in self.relations_by_source.values()) // 1,
            "entity_types": len(self.entities_by_type),
            "relation_types": len(self.relations_by_type),
            "scopes": list(self.entities_by_scope.keys()),
            "views": {
                scope: list(views.keys())
                for scope, views in self.views_by_scope.items()
            }
        }

    def clear(self):
        """Clear all indices."""
        self.entities_by_id.clear()
        self.entities_by_type.clear()
        self.entities_by_tag.clear()
        self.entities_by_scope.clear()
        self.relations_by_source.clear()
        self.relations_by_target.clear()
        self.relations_by_type.clear()
        self.views_by_scope.clear()
        self.entity_scope.clear()

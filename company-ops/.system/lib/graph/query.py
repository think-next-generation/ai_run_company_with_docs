"""
Graph Query for company-ops knowledge graphs.

Provides query capabilities for the knowledge graph.
"""

from typing import Optional
from .index import GraphIndex


class GraphQuery:
    """Query interface for the knowledge graph."""

    def __init__(self, index: GraphIndex):
        self.index = index

    def search(self, query: str, scope: str = "all") -> list[dict]:
        """
        Search entities by query string.

        Args:
            query: Search query
            scope: "all", "global", or specific subsystem_id

        Returns:
            List of matching entities
        """
        results = self.index.search_entities(query)

        if scope != "all":
            results = [e for e in results if self.index.get_entity_scope(e.get("id")) == scope]

        return results

    def get_entity(self, entity_id: str) -> Optional[dict]:
        """
        Get an entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity data or None if not found
        """
        return self.index.get_entity(entity_id)

    def get_entities_by_type(self, entity_type: str, scope: str = "all") -> list[dict]:
        """
        Get all entities of a specific type.

        Args:
            entity_type: Entity type (e.g., "subsystem", "capability")
            scope: "all", "global", or subsystem_id

        Returns:
            List of entities
        """
        entities = self.index.get_entities_by_type(entity_type)

        if scope != "all":
            entities = [e for e in entities if self.index.get_entity_scope(e.get("id")) == scope]

        return entities

    def get_entities_by_tag(self, tag: str, scope: str = "all") -> list[dict]:
        """
        Get all entities with a specific tag.

        Args:
            tag: Tag name
            scope: "all", "global", or subsystem_id

        Returns:
            List of entities
        """
        entities = self.index.get_entities_by_tag(tag)

        if scope != "all":
            entities = [e for e in entities if self.index.get_entity_scope(e.get("id")) == scope]

        return entities

    def get_relations(
        self,
        entity_id: str,
        direction: str = "both",
        relation_type: str = None
    ) -> list[dict]:
        """
        Get relations for an entity.

        Args:
            entity_id: Entity ID
            direction: "incoming", "outgoing", or "both"
            relation_type: Filter by relation type (optional)

        Returns:
            List of relations
        """
        relations = []

        if direction in ["outgoing", "both"]:
            outgoing = self.index.get_outgoing_relations(entity_id)
            relations.extend(outgoing)

        if direction in ["incoming", "both"]:
            incoming = self.index.get_incoming_relations(entity_id)
            relations.extend(incoming)

        if relation_type:
            relations = [r for r in relations if r.get("type") == relation_type]

        # Remove duplicates
        seen = set()
        unique_relations = []
        for r in relations:
            rid = r.get("id") or (r.get("source"), r.get("target"), r.get("type"))
            if rid not in seen:
                seen.add(rid)
                unique_relations.append(r)

        return unique_relations

    def get_related_entities(
        self,
        entity_id: str,
        direction: str = "both",
        relation_type: str = None
    ) -> list[dict]:
        """
        Get entities related to an entity.

        Args:
            entity_id: Entity ID
            direction: "incoming", "outgoing", or "both"
            relation_type: Filter by relation type (optional)

        Returns:
            List of related entities
        """
        relations = self.get_relations(entity_id, direction, relation_type)
        related = []

        for relation in relations:
            if relation.get("source") != entity_id:
                target_id = relation.get("source")
            else:
                target_id = relation.get("target")

            if target_id:
                entity = self.index.get_entity(target_id)
                if entity:
                    related.append({
                        "entity": entity,
                        "relation": relation
                    })

        return related

    def get_view(self, view_name: str, scope: str = "global") -> list[dict]:
        """
        Get a predefined view.

        Args:
            view_name: View name (e.g., "capability", "goal")
            scope: "global" or subsystem_id

        Returns:
            List of entities in the view
        """
        view_ids = self.index.get_view(view_name, scope)
        entities = []

        for entity_id in view_ids:
            entity = self.index.get_entity(entity_id)
            if entity:
                entities.append(entity)

        return entities

    def get_path(
        self,
        from_entity: str,
        to_entity: str,
        max_depth: int = 5
    ) -> Optional[list[dict]]:
        """
        Find a path between two entities.

        Args:
            from_entity: Starting entity ID
            to_entity: Target entity ID
            max_depth: Maximum search depth

        Returns:
            List of relations forming the path, or None if no path found
        """
        # BFS to find shortest path
        visited = {from_entity}
        queue = [(from_entity, [])]

        while queue:
            current, path = queue.pop(0)

            if len(path) >= max_depth:
                continue

            relations = self.get_relations(current, direction="outgoing")

            for relation in relations:
                target = relation.get("target")
                if not target:
                    continue

                new_path = path + [relation]

                if target == to_entity:
                    return new_path

                if target not in visited:
                    visited.add(target)
                    queue.append((target, new_path))

        return None

    def get_subtree(
        self,
        root_entity: str,
        relation_type: str = "breaks_down_to",
        max_depth: int = 10
    ) -> dict:
        """
        Get a tree of entities under a root.

        Args:
            root_entity: Root entity ID
            relation_type: Relation type that forms the tree
            max_depth: Maximum depth

        Returns:
            Tree structure with entities
        """
        def build_tree(entity_id: str, depth: int) -> dict:
            entity = self.index.get_entity(entity_id)
            if not entity:
                return None

            node = {
                "entity": entity,
                "children": []
            }

            if depth >= max_depth:
                return node

            relations = self.get_relations(
                entity_id,
                direction="outgoing",
                relation_type=relation_type
            )

            for relation in relations:
                target_id = relation.get("target")
                if target_id:
                    child = build_tree(target_id, depth + 1)
                    if child:
                        child["relation"] = relation
                        node["children"].append(child)

            return node

        return build_tree(root_entity, 0)

    def get_dependency_graph(self, entity_id: str) -> dict:
        """
        Get all dependencies of an entity.

        Args:
            entity_id: Entity ID

        Returns:
            Dict with 'depends_on' and 'depended_by' lists
        """
        depends_on = self.get_related_entities(
            entity_id,
            direction="outgoing",
            relation_type="depends_on"
        )

        depended_by = self.get_related_entities(
            entity_id,
            direction="incoming",
            relation_type="depends_on"
        )

        return {
            "entity_id": entity_id,
            "depends_on": depends_on,
            "depended_by": depended_by
        }

    def get_stats(self) -> dict:
        """Get graph statistics."""
        return self.index.get_stats()

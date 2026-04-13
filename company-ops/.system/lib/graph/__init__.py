"""
Knowledge Graph Library for company-ops.

Provides parsing, indexing, querying, updating, and caching
for the document-driven knowledge graph system.
"""

from .parser import GraphParser
from .index import GraphIndex
from .query import GraphQuery
from .update import GraphUpdater
from .cache import GraphCache

__version__ = "1.0.0"
__all__ = [
    "GraphParser",
    "GraphIndex",
    "GraphQuery",
    "GraphUpdater",
    "GraphCache",
]


class KnowledgeGraph:
    """
    Main interface for the knowledge graph system.

    Combines all components into a unified API.
    """

    def __init__(self, base_path: str, use_cache: bool = True):
        """
        Initialize the knowledge graph system.

        Args:
            base_path: Base path of the company-ops directory
            use_cache: Whether to enable caching
        """
        self.base_path = base_path
        self.parser = GraphParser(base_path)
        self.index = GraphIndex()
        self.query = GraphQuery(self.index)
        self.updater = GraphUpdater(base_path, self.index)
        self.cache = GraphCache(base_path) if use_cache else None

    def load_global_graph(self) -> dict:
        """Load and parse the global knowledge graph."""
        if self.cache:
            cached = self.cache.get("global-graph")
            if cached:
                return cached

        graph = self.parser.parse_global_graph()
        self.index.build_index(graph)

        if self.cache:
            self.cache.set("global-graph", graph)

        return graph

    def load_subsystem_graph(self, subsystem_id: str) -> dict:
        """Load and parse a subsystem's local knowledge graph."""
        cache_key = f"local-graph:{subsystem_id}"

        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        graph = self.parser.parse_local_graph(subsystem_id)
        self.index.build_subsystem_index(subsystem_id, graph)

        if self.cache:
            self.cache.set(cache_key, graph)

        return graph

    def load_all_graphs(self) -> dict:
        """Load all graphs (global + all subsystems)."""
        result = {
            "global": self.load_global_graph(),
            "subsystems": {}
        }

        # Get all subsystems from registry
        registry = self.parser.parse_registry()
        for subsystem in registry.get("subsystems", []):
            subsystem_id = subsystem.get("id")
            if subsystem_id:
                result["subsystems"][subsystem_id] = self.load_subsystem_graph(subsystem_id)

        return result

    def search(self, query_str: str, scope: str = "all") -> list:
        """
        Search across the knowledge graph.

        Args:
            query_str: Search query
            scope: "all", "global", or specific subsystem_id

        Returns:
            List of matching entities
        """
        return self.query.search(query_str, scope)

    def get_entity(self, entity_id: str) -> dict | None:
        """Get an entity by ID."""
        return self.query.get_entity(entity_id)

    def get_relations(self, entity_id: str, direction: str = "both") -> list:
        """
        Get relations for an entity.

        Args:
            entity_id: Entity ID
            direction: "incoming", "outgoing", or "both"

        Returns:
            List of relations
        """
        return self.query.get_relations(entity_id, direction)

    def add_entity(self, entity: dict, scope: str = "global") -> bool:
        """
        Add a new entity.

        Args:
            entity: Entity data
            scope: "global" or subsystem_id

        Returns:
            Success status
        """
        return self.updater.add_entity(entity, scope)

    def update_entity(self, entity_id: str, updates: dict, scope: str = "global") -> bool:
        """Update an existing entity."""
        return self.updater.update_entity(entity_id, updates, scope)

    def add_relation(self, relation: dict, scope: str = "global") -> bool:
        """Add a new relation."""
        return self.updater.add_relation(relation, scope)

    def get_view(self, view_name: str, scope: str = "global") -> list:
        """Get a predefined view."""
        return self.query.get_view(view_name, scope)

    def invalidate_cache(self, scope: str = "all"):
        """Invalidate cache."""
        if self.cache:
            self.cache.invalidate(scope)

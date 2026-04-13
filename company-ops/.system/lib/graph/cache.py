"""
Graph Cache for company-ops knowledge graphs.

Provides caching for parsed graphs to improve performance.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta


class GraphCache:
    """Cache for knowledge graph data."""

    def __init__(self, base_path: str, ttl_seconds: int = 300):
        """
        Initialize the cache.

        Args:
            base_path: Base path of company-ops
            ttl_seconds: Time-to-live for cache entries (default: 5 minutes)
        """
        self.base_path = Path(base_path)
        self.cache_dir = self.base_path / ".system" / "graph-cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

        # In-memory cache
        self._memory_cache: dict[str, dict] = {}
        self._cache_times: dict[str, datetime] = {}

    def get(self, key: str) -> Optional[dict]:
        """
        Get a cached value.

        Args:
            key: Cache key (e.g., "global-graph", "local-graph:财务")

        Returns:
            Cached data or None if not found/expired
        """
        # Check memory cache first
        if key in self._memory_cache:
            if self._is_valid(key):
                return self._memory_cache[key]
            else:
                del self._memory_cache[key]
                del self._cache_times[key]

        # Check disk cache
        cache_file = self._get_cache_path(key)
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Check TTL
                cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
                if datetime.now() - cached_at < timedelta(seconds=self.ttl_seconds):
                    # Promote to memory cache
                    self._memory_cache[key] = data.get("value")
                    self._cache_times[key] = cached_at
                    return data.get("value")
            except Exception:
                pass

        return None

    def set(self, key: str, value: dict):
        """
        Set a cached value.

        Args:
            key: Cache key
            value: Data to cache
        """
        now = datetime.now()

        # Set in memory cache
        self._memory_cache[key] = value
        self._cache_times[key] = now

        # Set in disk cache
        cache_file = self._get_cache_path(key)
        cache_data = {
            "key": key,
            "value": value,
            "_cached_at": now.isoformat()
        }

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False)
        except Exception:
            pass  # Disk cache failure is non-critical

    def invalidate(self, key: str = None, scope: str = "all"):
        """
        Invalidate cache entries.

        Args:
            key: Specific key to invalidate (None for all matching scope)
            scope: "all", "global", or subsystem_id
        """
        if key:
            # Invalidate specific key
            self._invalidate_key(key)
        elif scope == "all":
            # Invalidate all
            self._memory_cache.clear()
            self._cache_times.clear()
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        else:
            # Invalidate by scope
            keys_to_remove = [
                k for k in self._memory_cache.keys()
                if k == "global-graph" and scope == "global"
                or k.startswith(f"local-graph:{scope}")
            ]
            for k in keys_to_remove:
                self._invalidate_key(k)

    def _invalidate_key(self, key: str):
        """Invalidate a specific cache key."""
        if key in self._memory_cache:
            del self._memory_cache[key]
        if key in self._cache_times:
            del self._cache_times[key]

        cache_file = self._get_cache_path(key)
        if cache_file.exists():
            cache_file.unlink()

    def _is_valid(self, key: str) -> bool:
        """Check if a memory cache entry is still valid."""
        if key not in self._cache_times:
            return False

        elapsed = datetime.now() - self._cache_times[key]
        return elapsed < timedelta(seconds=self.ttl_seconds)

    def _get_cache_path(self, key: str) -> Path:
        """Get the cache file path for a key."""
        # Use hash to handle special characters in keys
        key_hash = hashlib.md5(key.encode()).hexdigest()[:12]
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}_{key_hash}.json"

    def get_stats(self) -> dict:
        """Get cache statistics."""
        memory_count = len(self._memory_cache)
        disk_count = len(list(self.cache_dir.glob("*.json")))

        return {
            "memory_cache_count": memory_count,
            "disk_cache_count": disk_count,
            "ttl_seconds": self.ttl_seconds,
            "cache_dir": str(self.cache_dir)
        }

    def warmup(self, parser):
        """
        Warm up the cache by preloading graphs.

        Args:
            parser: GraphParser instance
        """
        # Cache global graph
        global_graph = parser.parse_global_graph()
        self.set("global-graph", global_graph)

        # Cache all subsystem graphs
        registry = parser.parse_registry()
        for subsystem in registry.get("subsystems", []):
            subsystem_id = subsystem.get("id")
            if subsystem_id:
                local_graph = parser.parse_local_graph(subsystem_id)
                self.set(f"local-graph:{subsystem_id}", local_graph)

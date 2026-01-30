"""
DS-Search Cache Layer
=====================
Multi-layer caching for search results.

Layers:
1. In-memory cache (fastest, limited size)
2. File cache (persistent, larger)
3. MongoDB cache (optional, distributed)

Features:
- TTL-based expiration (6-24 hours)
- Query hash-based keys
- Cache hit/miss tracking
- Automatic cleanup
"""

import hashlib
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cache entry with metadata"""
    query_hash: str
    query: str
    results: List[Dict]
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    source: str = "search"  # search, crawl, api
    
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
    
    def to_dict(self) -> Dict:
        return {
            "query_hash": self.query_hash,
            "query": self.query,
            "results": self.results,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "hit_count": self.hit_count,
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        return cls(
            query_hash=data['query_hash'],
            query=data['query'],
            results=data['results'],
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']),
            hit_count=data.get('hit_count', 0),
            source=data.get('source', 'search')
        )


@dataclass
class CacheStats:
    """Cache statistics"""
    total_entries: int = 0
    memory_entries: int = 0
    file_entries: int = 0
    db_entries: int = 0
    hits: int = 0
    misses: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class SearchCache:
    """
    Multi-layer cache for DS-Search results.
    """
    
    # Default TTLs
    DEFAULT_TTL_HOURS = 6
    HIGH_PRIORITY_TTL_HOURS = 24
    LOW_PRIORITY_TTL_HOURS = 3
    
    # Memory cache limits
    MAX_MEMORY_ENTRIES = 500
    
    def __init__(self, db=None, cache_dir: str = None):
        self.db = db
        
        # In-memory cache (LRU-like)
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # For LRU eviction
        
        # File cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent.parent / "cache" / "search"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = CacheStats()
        
        logger.info(f"Search cache initialized. Dir: {self.cache_dir}")
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for query"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _get_file_path(self, query_hash: str) -> Path:
        """Get file path for cache entry"""
        # Use first 2 chars as subdirectory for better distribution
        subdir = self.cache_dir / query_hash[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{query_hash}.json"
    
    async def get(self, query: str) -> Optional[List[Dict]]:
        """
        Get cached results for a query.
        Checks layers in order: memory -> file -> db
        
        Args:
            query: Search query
            
        Returns:
            Cached results or None if not found/expired
        """
        query_hash = self._hash_query(query)
        
        # Layer 1: Memory cache
        entry = self._get_from_memory(query_hash)
        if entry and not entry.is_expired():
            self.stats.hits += 1
            entry.hit_count += 1
            logger.debug(f"Cache HIT (memory): {query[:50]}...")
            return entry.results
        
        # Layer 2: File cache
        entry = self._get_from_file(query_hash)
        if entry and not entry.is_expired():
            # Promote to memory cache
            self._put_to_memory(entry)
            self.stats.hits += 1
            entry.hit_count += 1
            logger.debug(f"Cache HIT (file): {query[:50]}...")
            return entry.results
        
        # Layer 3: Database cache
        if self.db is not None:
            entry = await self._get_from_db(query_hash)
            if entry and not entry.is_expired():
                # Promote to memory and file cache
                self._put_to_memory(entry)
                self._put_to_file(entry)
                self.stats.hits += 1
                entry.hit_count += 1
                logger.debug(f"Cache HIT (db): {query[:50]}...")
                return entry.results
        
        self.stats.misses += 1
        logger.debug(f"Cache MISS: {query[:50]}...")
        return None
    
    async def put(self, query: str, results: List[Dict], 
                  ttl_hours: float = None, source: str = "search"):
        """
        Store results in cache.
        
        Args:
            query: Search query
            results: Results to cache
            ttl_hours: Time to live in hours
            source: Source of results (search, crawl, api)
        """
        if not results:
            return
        
        query_hash = self._hash_query(query)
        ttl = ttl_hours or self.DEFAULT_TTL_HOURS
        
        now = datetime.now(timezone.utc)
        entry = CacheEntry(
            query_hash=query_hash,
            query=query,
            results=results,
            created_at=now,
            expires_at=now + timedelta(hours=ttl),
            source=source
        )
        
        # Store in all layers
        self._put_to_memory(entry)
        self._put_to_file(entry)
        
        if self.db is not None:
            await self._put_to_db(entry)
        
        self.stats.total_entries += 1
        logger.debug(f"Cached {len(results)} results for: {query[:50]}...")
    
    def _get_from_memory(self, query_hash: str) -> Optional[CacheEntry]:
        """Get from memory cache"""
        entry = self.memory_cache.get(query_hash)
        if entry:
            # Move to end of access order (LRU)
            if query_hash in self.access_order:
                self.access_order.remove(query_hash)
            self.access_order.append(query_hash)
        return entry
    
    def _put_to_memory(self, entry: CacheEntry):
        """Put to memory cache with LRU eviction"""
        # Evict if at capacity
        while len(self.memory_cache) >= self.MAX_MEMORY_ENTRIES:
            if self.access_order:
                oldest = self.access_order.pop(0)
                self.memory_cache.pop(oldest, None)
        
        self.memory_cache[entry.query_hash] = entry
        self.access_order.append(entry.query_hash)
        self.stats.memory_entries = len(self.memory_cache)
    
    def _get_from_file(self, query_hash: str) -> Optional[CacheEntry]:
        """Get from file cache"""
        file_path = self._get_file_path(query_hash)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return CacheEntry.from_dict(data)
        except Exception as e:
            logger.warning(f"File cache read error: {e}")
            return None
    
    def _put_to_file(self, entry: CacheEntry):
        """Put to file cache"""
        file_path = self._get_file_path(entry.query_hash)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"File cache write error: {e}")
    
    async def _get_from_db(self, query_hash: str) -> Optional[CacheEntry]:
        """Get from database cache"""
        try:
            doc = await self.db.search_cache.find_one({"query_hash": query_hash})
            if doc:
                return CacheEntry.from_dict(doc)
        except Exception as e:
            logger.warning(f"DB cache read error: {e}")
        return None
    
    async def _put_to_db(self, entry: CacheEntry):
        """Put to database cache"""
        try:
            await self.db.search_cache.update_one(
                {"query_hash": entry.query_hash},
                {"$set": entry.to_dict()},
                upsert=True
            )
            self.stats.db_entries += 1
        except Exception as e:
            logger.warning(f"DB cache write error: {e}")
    
    async def invalidate(self, query: str):
        """Invalidate cache for a specific query"""
        query_hash = self._hash_query(query)
        
        # Remove from memory
        self.memory_cache.pop(query_hash, None)
        if query_hash in self.access_order:
            self.access_order.remove(query_hash)
        
        # Remove from file
        file_path = self._get_file_path(query_hash)
        if file_path.exists():
            file_path.unlink()
        
        # Remove from database
        if self.db is not None:
            try:
                await self.db.search_cache.delete_one({"query_hash": query_hash})
            except Exception as e:
                logger.warning(f"DB cache invalidation error: {e}")
        
        logger.debug(f"Invalidated cache for: {query[:50]}...")
    
    async def cleanup_expired(self):
        """Remove expired entries from all cache layers"""
        now = datetime.now(timezone.utc)
        removed_count = 0
        
        # Memory cache
        expired_hashes = [
            h for h, e in self.memory_cache.items() 
            if e.is_expired()
        ]
        for h in expired_hashes:
            self.memory_cache.pop(h, None)
            if h in self.access_order:
                self.access_order.remove(h)
            removed_count += 1
        
        # File cache
        for subdir in self.cache_dir.iterdir():
            if subdir.is_dir():
                for file_path in subdir.glob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        expires_at = datetime.fromisoformat(data['expires_at'])
                        if now > expires_at.replace(tzinfo=timezone.utc):
                            file_path.unlink()
                            removed_count += 1
                    except Exception:
                        pass
        
        # Database cache
        if self.db is not None:
            try:
                result = await self.db.search_cache.delete_many({
                    "expires_at": {"$lt": now.isoformat()}
                })
                removed_count += result.deleted_count
            except Exception as e:
                logger.warning(f"DB cache cleanup error: {e}")
        
        logger.info(f"Cache cleanup: removed {removed_count} expired entries")
        return removed_count
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        self.stats.memory_entries = len(self.memory_cache)
        
        return {
            "memory_entries": self.stats.memory_entries,
            "max_memory_entries": self.MAX_MEMORY_ENTRIES,
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate": f"{self.stats.hit_rate:.2%}",
            "cache_dir": str(self.cache_dir)
        }
    
    def clear_memory(self):
        """Clear memory cache"""
        self.memory_cache.clear()
        self.access_order.clear()
        self.stats.memory_entries = 0
        logger.info("Memory cache cleared")
    
    async def clear_all(self):
        """Clear all cache layers"""
        # Memory
        self.clear_memory()
        
        # File cache
        import shutil
        for subdir in self.cache_dir.iterdir():
            if subdir.is_dir():
                shutil.rmtree(subdir)
        
        # Database
        if self.db is not None:
            try:
                await self.db.search_cache.delete_many({})
            except Exception as e:
                logger.warning(f"DB cache clear error: {e}")
        
        self.stats = CacheStats()
        logger.info("All caches cleared")


# Singleton instance
_cache_instance: Optional[SearchCache] = None

async def get_cache_instance(db=None, cache_dir: str = None) -> SearchCache:
    """Get or create cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SearchCache(db, cache_dir)
    return _cache_instance

"""Query result caching with LRU eviction and TTL."""
import hashlib
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Set
from pathlib import Path
from dataclasses import dataclass, field

from irouter.core.types import QueryResult


@dataclass
class CacheEntry:
    """A single cache entry."""
    key: str
    query_hash: str
    result: QueryResult
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    source_files: Set[str] = field(default_factory=set)
    source_file_mtimes: Dict[str, float] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.now() > self.expires_at
    
    def is_invalidated(self) -> bool:
        """Check if source files have been modified."""
        for file_path, cached_mtime in self.source_file_mtimes.items():
            try:
                current_mtime = Path(file_path).stat().st_mtime
                if current_mtime > cached_mtime:
                    return True
            except FileNotFoundError:
                # File deleted, invalidate cache
                return True
        return False


class QueryCache:
    """
    LRU cache for query results with TTL and file-based invalidation.
    
    Features:
    - LRU eviction when cache is full
    - Time-based expiration (TTL)
    - File modification-based invalidation
    - Cache statistics tracking
    
    Example:
        >>> cache = QueryCache(max_size=100, ttl_seconds=3600)
        >>> result = cache.get(sql)
        >>> if result is None:
        ...     result = execute_query(sql)
        ...     cache.put(sql, result)
    """
    
    def __init__(
        self,
        max_size: int = 100,
        ttl_seconds: int = 3600,
        enable_file_invalidation: bool = True
    ):
        """
        Initialize query cache.
        
        Args:
            max_size: Maximum number of entries to cache
            ttl_seconds: Time-to-live for cache entries in seconds
            enable_file_invalidation: Invalidate cache when source files change
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.enable_file_invalidation = enable_file_invalidation
        
        # OrderedDict for LRU behavior
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0
        self.invalidations = 0
    
    def get(self, sql: str) -> Optional[QueryResult]:
        """
        Get cached result for SQL query.
        
        Args:
            sql: SQL query string (normalized)
            
        Returns:
            QueryResult if cached and valid, None otherwise
        """
        key = self._hash_query(sql)
        
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if entry.is_expired():
            del self.cache[key]
            self.expirations += 1
            self.misses += 1
            return None
        
        # Check if invalidated by file changes
        if self.enable_file_invalidation and entry.is_invalidated():
            del self.cache[key]
            self.invalidations += 1
            self.misses += 1
            return None
        
        # Cache hit - move to end (most recently used)
        self.cache.move_to_end(key)
        entry.hit_count += 1
        entry.last_accessed = datetime.now()
        self.hits += 1
        
        # Mark as from cache
        cached_result = entry.result
        cached_result.from_cache = True
        
        return cached_result
    
    def put(
        self,
        sql: str,
        result: QueryResult,
        source_files: Optional[Set[str]] = None
    ):
        """
        Cache query result.
        
        Args:
            sql: SQL query string
            result: Query result to cache
            source_files: Optional set of source file paths for invalidation
        """
        key = self._hash_query(sql)
        
        # Evict oldest entry if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_oldest()
        
        # Get file modification times for invalidation
        source_file_mtimes = {}
        if self.enable_file_invalidation and source_files:
            for file_path in source_files:
                try:
                    source_file_mtimes[file_path] = Path(file_path).stat().st_mtime
                except FileNotFoundError:
                    pass
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            query_hash=key,
            result=result,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=self.ttl_seconds),
            source_files=source_files or set(),
            source_file_mtimes=source_file_mtimes
        )
        
        # Add to cache (or update existing)
        self.cache[key] = entry
        self.cache.move_to_end(key)
    
    def invalidate(self, sql: str):
        """
        Manually invalidate cache entry.
        
        Args:
            sql: SQL query string
        """
        key = self._hash_query(sql)
        if key in self.cache:
            del self.cache[key]
            self.invalidations += 1
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0
        self.invalidations = 0
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'evictions': self.evictions,
            'expirations': self.expirations,
            'invalidations': self.invalidations,
            'total_requests': total_requests
        }
    
    def _hash_query(self, sql: str) -> str:
        """
        Generate cache key from SQL query.
        
        Args:
            sql: SQL query string
            
        Returns:
            Hash string
        """
        # Normalize: strip whitespace, lowercase
        normalized = ' '.join(sql.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def _evict_oldest(self):
        """Evict the least recently used entry."""
        if self.cache:
            self.cache.popitem(last=False)  # Remove oldest (first) item
            self.evictions += 1
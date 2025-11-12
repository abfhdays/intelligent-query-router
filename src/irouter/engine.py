"""Main query execution engine."""
import time
from typing import Optional, Dict, Set
from pathlib import Path

from irouter.sqlglot.parser import SQLParser
from irouter.sqlglot.feature_extractor import FeatureExtractor
from irouter.optimizer.partition_pruning import PartitionPruner
from irouter.selector.backend_selector import BackendSelector
from irouter.backends.duckdb_backend import DuckDBBackend
from irouter.backends.polars_backend import PolarsBackend
from irouter.backends.spark_backend import SparkBackend
from irouter.cache.query_cache import QueryCache
from irouter.core.types import (
    Backend,
    QueryResult,
    PruningResult,
)


class QueryEngine:
    """
    Main query execution engine with caching.
    
    Orchestrates the full pipeline:
    Cache Check → Parse → Prune → Extract Features → Select Backend → Execute → Cache
    """
    
    def __init__(
        self, 
        data_path: str,
        dialect: str = "spark",
        enable_cache: bool = True,
        cache_size: int = 100,
        cache_ttl_seconds: int = 3600
    ):
        """
        Initialize query engine.
        
        Args:
            data_path: Root path where data is stored
            dialect: SQL dialect for parsing
            enable_cache: Enable query result caching
            cache_size: Maximum number of cached queries
            cache_ttl_seconds: Cache entry TTL in seconds
        """
        self.data_path = Path(data_path)
        self.dialect = dialect
        self.enable_cache = enable_cache
        
        # Initialize components
        self.parser = SQLParser(dialect=dialect)
        self.pruner = PartitionPruner(data_path=data_path)
        self.feature_extractor = FeatureExtractor()
        self.selector = BackendSelector()
        
        # Initialize cache
        self.cache = QueryCache(
            max_size=cache_size,
            ttl_seconds=cache_ttl_seconds,
            enable_file_invalidation=True
        ) if enable_cache else None
        
        # Initialize backends
        self.backends = {
            Backend.DUCKDB: DuckDBBackend(),
            Backend.POLARS: PolarsBackend(),
            Backend.SPARK: SparkBackend(),
        }
        
        # Cache for table schemas
        self.schemas: Dict[str, Dict[str, str]] = {}
    
    def execute(
        self,
        sql: str,
        schema: Optional[Dict[str, Dict[str, str]]] = None,
        force_backend: Optional[Backend] = None,
        bypass_cache: bool = False
    ) -> QueryResult:
        """
        Execute SQL query with automatic optimization and caching.
        
        Args:
            sql: SQL query string
            schema: Optional table schemas
            force_backend: Optional backend to force
            bypass_cache: Skip cache lookup and storage
            
        Returns:
            QueryResult with execution details
        """
        # Check cache first (unless bypassed)
        if self.enable_cache and not bypass_cache:
            cached_result = self.cache.get(sql)
            if cached_result is not None:
                return cached_result
        
        # Execute query
        total_start_time = time.time()
        
        try:
            # Parse SQL
            ast = self.parser.parse(sql)
            
            # Extract table name
            tables = self.parser.extract_tables(ast)
            if not tables:
                raise ValueError("No tables found in query")
            table_name = tables[0]
            
            # Optimize SQL
            optimized_ast = self.parser.optimize(ast, schema=schema)
            optimized_sql = self.parser.to_sql(optimized_ast)
            
            # Prune partitions
            pruning_result = self.pruner.prune(
                table_name=table_name,
                sql=sql,
                schema=schema
            )
            
            # Extract query features
            query_features = self.feature_extractor.extract_features(
                optimized_ast,
                pruning_result
            )
            
            # Select backend
            backend_choice = self.selector.select_backend(
                pruning_result,
                query_features,
                force_backend=force_backend
            )
            
            selected_backend = backend_choice.backend
            
            # Execute on selected backend
            backend = self.backends.get(selected_backend)
            if not backend:
                raise RuntimeError(f"Backend {selected_backend} not available")
            
            execution_start = time.time()
            result_data = backend.execute(
                optimized_sql,
                pruning_result,
                table_name
            )
            execution_time = time.time() - execution_start
            
            # Build result
            result = QueryResult(
                data=result_data,
                backend_used=selected_backend,
                execution_time_sec=execution_time,
                rows_processed=len(result_data),
                partitions_scanned=pruning_result.partitions_scanned,
                total_partitions=pruning_result.total_partitions,
                from_cache=False,
                sql_optimized=optimized_sql,
                pruning_result=pruning_result,
                actual_data_size_gb=pruning_result.size_gb
            )
            
            # Cache result (unless bypassed)
            if self.enable_cache and not bypass_cache:
                source_files = self._get_source_files(pruning_result)
                self.cache.put(sql, result, source_files=source_files)
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}") from e
    
    def _get_source_files(self, pruning_result: PruningResult) -> Set[str]:
        """
        Get set of source file paths from pruning result.
        
        Args:
            pruning_result: Partition pruning result
            
        Returns:
            Set of file paths
        """
        source_files = set()
        for partition in pruning_result.partitions_to_scan:
            partition_dir = Path(partition.path)
            for parquet_file in partition_dir.glob("*.parquet"):
                source_files.add(str(parquet_file))
        return source_files
    
    def explain(
        self,
        sql: str,
        schema: Optional[Dict[str, Dict[str, str]]] = None
    ) -> str:
        """Explain query execution plan without running."""
        # ... (keep existing implementation)
        try:
            ast = self.parser.parse(sql)
            tables = self.parser.extract_tables(ast)
            if not tables:
                return "Error: No tables found in query"
            
            table_name = tables[0]
            optimized_ast = self.parser.optimize(ast, schema=schema)
            
            pruning_result = self.pruner.prune(
                table_name=table_name,
                sql=sql,
                schema=schema
            )
            
            query_features = self.feature_extractor.extract_features(
                optimized_ast,
                pruning_result
            )
            
            backend_choice = self.selector.select_backend(
                pruning_result,
                query_features
            )
            
            lines = []
            lines.append("=" * 60)
            lines.append("QUERY EXECUTION PLAN")
            lines.append("=" * 60)
            
            lines.append("\n📊 QUERY ANALYSIS:")
            lines.append(f"  Tables: {', '.join(tables)}")
            lines.append(f"  Joins: {query_features.num_joins}")
            lines.append(f"  Aggregations: {query_features.num_aggregations}")
            lines.append(f"  Window Functions: {query_features.num_window_functions}")
            lines.append(f"  Has DISTINCT: {query_features.has_distinct}")
            lines.append(f"  Has ORDER BY: {query_features.has_order_by}")
            lines.append(f"  Complexity Score: {query_features.complexity_score:.1f}")
            
            lines.append("\n🎯 PARTITION PRUNING:")
            lines.append(f"  Total Partitions: {pruning_result.total_partitions}")
            lines.append(f"  Partitions to Scan: {pruning_result.partitions_scanned}")
            lines.append(f"  Data Skipped: {pruning_result.pruning_ratio*100:.1f}%")
            lines.append(f"  Estimated Speedup: {pruning_result.speedup_estimate:.1f}x")
            lines.append(f"  Data to Scan: {pruning_result.size_gb:.2f} GB")
            
            if pruning_result.predicates_applied:
                lines.append(f"\n  Predicates Applied:")
                for pred in pruning_result.predicates_applied:
                    lines.append(f"    - {pred.column} {pred.operator.value} {pred.value}")
            
            lines.append("\n⚡ BACKEND SELECTION:")
            lines.append(f"  Selected Backend: {backend_choice.backend.value.upper()}")
            lines.append(f"  Reasoning: {backend_choice.reasoning}")
            
            lines.append("\n💰 COST ESTIMATES:")
            for backend, estimate in backend_choice.all_estimates.items():
                if estimate.estimated_time_sec == float('inf'):
                    lines.append(f"  {backend.value}: INFEASIBLE")
                else:
                    marker = "⭐" if backend == backend_choice.backend else "  "
                    lines.append(f"  {marker} {backend.value}:")
                    lines.append(f"      Total Time: {estimate.estimated_time_sec:.2f}s")
                    lines.append(f"      Scan: {estimate.scan_cost:.2f}s")
                    lines.append(f"      Compute: {estimate.compute_cost:.2f}s")
                    lines.append(f"      Overhead: {estimate.overhead_cost:.2f}s")
                    lines.append(f"      Memory: {estimate.estimated_memory_gb:.2f} GB")
            
            lines.append("\n" + "=" * 60)
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error explaining query: {e}"
    
    def cache_stats(self) -> Dict:
        """Get cache statistics."""
        if not self.cache:
            return {'enabled': False}
        
        stats = self.cache.stats()
        stats['enabled'] = True
        return stats
    
    def clear_cache(self):
        """Clear query cache."""
        if self.cache:
            self.cache.clear()
    
    def register_schema(self, table_name: str, schema: Dict[str, str]):
        """Register table schema."""
        self.schemas[table_name] = schema
    
    def close(self):
        """Clean up resources."""
        for backend in self.backends.values():
            backend.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
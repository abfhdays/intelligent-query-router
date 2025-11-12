"""Cost estimation for query execution on different backends."""
from typing import Dict, List
from dataclasses import dataclass

from irouter.core.types import (
    Backend,
    CostEstimate,
    PruningResult,
)


@dataclass
class QueryFeatures:
    """Features extracted from query for cost estimation."""
    estimated_scan_size_gb: float
    num_joins: int
    num_aggregations: int
    num_window_functions: int
    has_distinct: bool
    has_order_by: bool
    selectivity: float = 1.0  # Estimated % of rows returned (0.0 to 1.0)
    
    @property
    def complexity_score(self) -> float:
        """
        Calculate query complexity score.
        
        Higher score = more complex query.
        """
        score = 0.0
        score += self.num_joins * 2.0
        score += self.num_aggregations * 1.0
        score += self.num_window_functions * 3.0
        score += 1.0 if self.has_distinct else 0.0
        score += 0.5 if self.has_order_by else 0.0
        return score


class CostEstimator:
    """
    Estimates execution cost for different backends.
    
    Uses simple rule-based heuristics that can be replaced
    with ML models later.
    """
    
    # Backend characteristics (tunable parameters)
    DUCKDB_SCAN_RATE_GB_SEC = 2.0      # 2 GB/sec scan rate
    DUCKDB_OVERHEAD_SEC = 0.1          # Fast startup
    DUCKDB_MAX_MEMORY_GB = 32.0        # Memory limit
    
    POLARS_SCAN_RATE_GB_SEC = 1.8      # Slightly slower than DuckDB
    POLARS_OVERHEAD_SEC = 0.2          # Fast startup
    POLARS_MAX_MEMORY_GB = 64.0        # Can handle more memory
    
    SPARK_SCAN_RATE_GB_SEC = 1.5       # Slower but distributed
    SPARK_OVERHEAD_SEC = 15.0          # Cold start overhead
    SPARK_MIN_EFFICIENT_SIZE_GB = 10.0  # Not efficient for small data
    
    def __init__(self):
        """Initialize cost estimator."""
        pass
    
    def estimate_all_backends(
        self, 
        pruning_result: PruningResult,
        query_features: QueryFeatures
    ) -> Dict[Backend, CostEstimate]:
        """
        Estimate cost for all available backends.
        
        Args:
            pruning_result: Result from partition pruning
            query_features: Extracted query features
            
        Returns:
            Dict mapping Backend to CostEstimate
        """
        estimates = {}
        
        # Estimate for DuckDB
        estimates[Backend.DUCKDB] = self._estimate_duckdb(
            pruning_result, query_features
        )
        
        # Estimate for Polars
        estimates[Backend.POLARS] = self._estimate_polars(
            pruning_result, query_features
        )
        
        # Estimate for Spark
        estimates[Backend.SPARK] = self._estimate_spark(
            pruning_result, query_features
        )
        
        return estimates
    
    def _estimate_duckdb(
        self,
        pruning_result: PruningResult,
        query_features: QueryFeatures
    ) -> CostEstimate:
        """Estimate cost for DuckDB backend."""
        data_size_gb = pruning_result.size_gb
        
        # Scan cost
        scan_time = data_size_gb / self.DUCKDB_SCAN_RATE_GB_SEC
        
        # Compute cost (based on query complexity)
        compute_time = self._compute_cost(query_features, backend_type="olap")
        
        # Overhead
        overhead_time = self.DUCKDB_OVERHEAD_SEC
        
        # Memory estimate (3x data size for processing)
        memory_needed = data_size_gb * 3.0
        
        # Check if exceeds memory limit
        if memory_needed > self.DUCKDB_MAX_MEMORY_GB:
            # Penalize heavily if OOM likely
            total_time = float('inf')
            reasoning = f"Insufficient memory (need {memory_needed:.1f}GB, have {self.DUCKDB_MAX_MEMORY_GB}GB)"
        else:
            total_time = scan_time + compute_time + overhead_time
            reasoning = "Vectorized OLAP execution optimal for small-medium datasets"
        
        return CostEstimate(
            backend=Backend.DUCKDB,
            estimated_time_sec=total_time,
            estimated_memory_gb=memory_needed,
            scan_cost=scan_time,
            compute_cost=compute_time,
            overhead_cost=overhead_time,
            reasoning=reasoning
        )
    
    def _estimate_polars(
        self,
        pruning_result: PruningResult,
        query_features: QueryFeatures
    ) -> CostEstimate:
        """Estimate cost for Polars backend."""
        data_size_gb = pruning_result.size_gb
        
        # Scan cost
        scan_time = data_size_gb / self.POLARS_SCAN_RATE_GB_SEC
        
        # Compute cost (Polars is good at parallel operations)
        compute_time = self._compute_cost(query_features, backend_type="parallel")
        
        # Overhead
        overhead_time = self.POLARS_OVERHEAD_SEC
        
        # Memory estimate (2.5x data size - more efficient than DuckDB)
        memory_needed = data_size_gb * 2.5
        
        # Check memory limit
        if memory_needed > self.POLARS_MAX_MEMORY_GB:
            total_time = float('inf')
            reasoning = f"Insufficient memory (need {memory_needed:.1f}GB, have {self.POLARS_MAX_MEMORY_GB}GB)"
        else:
            total_time = scan_time + compute_time + overhead_time
            reasoning = "Parallel execution good for medium datasets"
        
        return CostEstimate(
            backend=Backend.POLARS,
            estimated_time_sec=total_time,
            estimated_memory_gb=memory_needed,
            scan_cost=scan_time,
            compute_cost=compute_time,
            overhead_cost=overhead_time,
            reasoning=reasoning
        )
    
    def _estimate_spark(
        self,
        pruning_result: PruningResult,
        query_features: QueryFeatures
    ) -> CostEstimate:
        """Estimate cost for Spark backend."""
        data_size_gb = pruning_result.size_gb
        
        # Scan cost (distributed, slightly slower per-node)
        scan_time = data_size_gb / self.SPARK_SCAN_RATE_GB_SEC
        
        # Compute cost (distributed computation)
        compute_time = self._compute_cost(query_features, backend_type="distributed")
        
        # Overhead (high cold start cost)
        overhead_time = self.SPARK_OVERHEAD_SEC
        
        # Memory estimate (distributed across nodes)
        # Assume 4 executors with 16GB each = 64GB total
        memory_needed = data_size_gb / 4.0  # Distributed
        
        total_time = scan_time + compute_time + overhead_time
        
        # Penalize Spark for small datasets (overhead not worth it)
        if data_size_gb < self.SPARK_MIN_EFFICIENT_SIZE_GB:
            efficiency_penalty = self.SPARK_MIN_EFFICIENT_SIZE_GB / max(data_size_gb, 0.1)
            total_time *= efficiency_penalty
            reasoning = f"Inefficient for small data ({data_size_gb:.1f}GB < {self.SPARK_MIN_EFFICIENT_SIZE_GB}GB threshold)"
        else:
            reasoning = "Distributed execution optimal for large datasets"
        
        return CostEstimate(
            backend=Backend.SPARK,
            estimated_time_sec=total_time,
            estimated_memory_gb=memory_needed,
            scan_cost=scan_time,
            compute_cost=compute_time,
            overhead_cost=overhead_time,
            reasoning=reasoning
        )
    
    def _compute_cost(
        self, 
        query_features: QueryFeatures,
        backend_type: str
    ) -> float:
        """
        Estimate computation time based on query features.
        
        Args:
            query_features: Query features
            backend_type: "olap", "parallel", or "distributed"
            
        Returns:
            Estimated computation time in seconds
        """
        # Base computation time per operation
        if backend_type == "olap":
            # DuckDB - fast vectorized operations
            join_cost = 1.0
            agg_cost = 0.5
            window_cost = 2.0
        elif backend_type == "parallel":
            # Polars - parallel but single-machine
            join_cost = 0.8
            agg_cost = 0.4
            window_cost = 1.5
        else:  # distributed
            # Spark - distributed overhead but scales
            join_cost = 0.6
            agg_cost = 0.3
            window_cost = 1.0
        
        cost = 0.0
        cost += query_features.num_joins * join_cost
        cost += query_features.num_aggregations * agg_cost
        cost += query_features.num_window_functions * window_cost
        
        # Add cost for distinct/sort operations
        if query_features.has_distinct:
            cost += 1.0
        if query_features.has_order_by:
            cost += 0.5
        
        return cost
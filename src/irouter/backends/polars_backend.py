"""Polars backend for query execution."""
import time
from typing import List, Dict
import pandas as pd
import polars as pl
from pathlib import Path

from irouter.backends.base import BaseBackend
from irouter.core.types import Backend, PruningResult


class PolarsBackend(BaseBackend):
    """
    Polars backend for parallel query execution.
    
    Best for: 10-100 GB data, multi-core parallelism
    Features: Lazy evaluation, parallel execution, efficient memory usage
    """
    
    def __init__(self):
        """Initialize Polars backend."""
        super().__init__()
    
    def execute(
        self,
        sql: str,
        pruning_result: PruningResult,
        table_name: str
    ) -> pd.DataFrame:
        """
        Execute SQL query using Polars.
        
        Args:
            sql: SQL query to execute
            pruning_result: Pruned partitions to read
            table_name: Table name in the query
            
        Returns:
            Query results as pandas DataFrame
        """
        # Get partition information
        partitions_data = self._get_partitions_with_metadata(pruning_result)
        
        if not partitions_data:
            # No files to read, return empty DataFrame
            return pd.DataFrame()
        
        try:
            # Read all partitions and add partition columns
            dfs = []
            
            for partition_info in partitions_data:
                # Read Parquet files in this partition
                df = pl.scan_parquet(partition_info['files'])
                
                # Add partition columns (e.g., date=2024-11-01)
                for key, value in partition_info['partition_cols'].items():
                    df = df.with_columns(pl.lit(value).alias(key))
                
                dfs.append(df)
            
            # Concatenate all partitions
            if len(dfs) == 1:
                combined_df = dfs[0]
            else:
                combined_df = pl.concat(dfs)
            
            # Register as table for SQL execution
            ctx = pl.SQLContext()
            ctx.register(table_name, combined_df)
            
            # Execute SQL query
            result = ctx.execute(sql)
            
            # Collect and convert to pandas
            result_df = result.collect().to_pandas()
            
            return result_df
            
        except Exception as e:
            raise RuntimeError(f"Polars query execution failed: {e}")
    
    def _get_partitions_with_metadata(self, pruning_result: PruningResult) -> List[Dict]:
        """
        Get partition information including files and partition column values.
        
        Args:
            pruning_result: Pruning result with partition info
            
        Returns:
            List of dicts with 'files' and 'partition_cols'
            
        Example:
            [
                {
                    'files': ['data/sales/date=2024-11-01/data.parquet'],
                    'partition_cols': {'date': '2024-11-01'}
                },
                ...
            ]
        """
        partitions_data = []
        
        for partition in pruning_result.partitions_to_scan:
            partition_dir = Path(partition.path)
            
            # Get all Parquet files in this partition
            parquet_files = list(partition_dir.glob("*.parquet"))
            
            if not parquet_files:
                continue
            
            # Extract partition column from directory name (e.g., "date=2024-11-01")
            partition_cols = {}
            if '=' in partition_dir.name:
                key, value = partition_dir.name.split('=', 1)
                partition_cols[key] = value
            
            partitions_data.append({
                'files': [str(f) for f in parquet_files],
                'partition_cols': partition_cols
            })
        
        return partitions_data
    
    def get_backend_type(self) -> Backend:
        """Get backend type."""
        return Backend.POLARS
    
    def supports_feature(self, feature: str) -> bool:
        """
        Check if Polars supports a feature.
        
        Args:
            feature: Feature name
            
        Returns:
            True if supported
        """
        supported_features = {
            "window_functions": True,
            "cte": True,
            "lateral_join": False,  # Limited support
            "pivot": True,
            "unpivot": True,
        }
        
        return supported_features.get(feature, True)
    
    def close(self):
        """Close Polars resources (no persistent connection)."""
        pass
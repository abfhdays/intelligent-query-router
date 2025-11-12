"""Spark backend for distributed query execution."""
import time
from typing import List, Optional
import pandas as pd
from pathlib import Path

from irouter.backends.base import BaseBackend
from irouter.core.types import Backend, PruningResult


class SparkBackend(BaseBackend):
    """
    Spark backend for distributed query execution.
    
    Best for: > 100 GB data, distributed processing
    Features: Horizontal scaling, fault tolerance, distributed execution
    
    Note: This uses local Spark session for testing.
    In production, connect to existing Spark cluster.
    """
    
    def __init__(self, app_name: str = "IntelligentQueryRouter"):
        """
        Initialize Spark backend.
        
        Args:
            app_name: Spark application name
        """
        super().__init__()
        self.spark = self._create_spark_session(app_name)
    
    def _create_spark_session(self, app_name: str):
        """
        Create local Spark session.
        
        Args:
            app_name: Application name
            
        Returns:
            SparkSession
        """
        try:
            from pyspark.sql import SparkSession
            
            spark = (SparkSession.builder
                     .appName(app_name)
                     .master("local[*]")  # Use all local cores
                     .config("spark.driver.memory", "4g")
                     .config("spark.executor.memory", "4g")
                     .config("spark.sql.shuffle.partitions", "8")
                     .getOrCreate())
            
            # Set log level to WARN to reduce noise
            spark.sparkContext.setLogLevel("WARN")
            
            return spark
            
        except ImportError:
            raise RuntimeError(
                "PySpark not installed. Install with: pip install pyspark"
            )
    
    def execute(
        self,
        sql: str,
        pruning_result: PruningResult,
        table_name: str
    ) -> pd.DataFrame:
        """
        Execute SQL query using Spark.
        
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
            from pyspark.sql import functions as F
            
            # Read all partitions
            dfs = []
            
            for partition_info in partitions_data:
                # Read Parquet files
                df = self.spark.read.parquet(*partition_info['files'])
                
                # Add partition columns
                for key, value in partition_info['partition_cols'].items():
                    df = df.withColumn(key, F.lit(value))
                
                dfs.append(df)
            
            # Union all partitions
            if len(dfs) == 1:
                combined_df = dfs[0]
            else:
                combined_df = dfs[0]
                for df in dfs[1:]:
                    combined_df = combined_df.union(df)
            
            # Register as temporary view
            combined_df.createOrReplaceTempView(table_name)
            
            # Execute SQL query
            result_df_spark = self.spark.sql(sql)
            
            # Convert to pandas (collect to driver)
            result_df = result_df_spark.toPandas()
            
            return result_df
            
        except Exception as e:
            raise RuntimeError(f"Spark query execution failed: {e}")
    
    def _get_partitions_with_metadata(self, pruning_result: PruningResult) -> List[dict]:
        """
        Get partition information including files and partition column values.
        
        Args:
            pruning_result: Pruning result with partition info
            
        Returns:
            List of dicts with 'files' and 'partition_cols'
        """
        partitions_data = []
        
        for partition in pruning_result.partitions_to_scan:
            partition_dir = Path(partition.path)
            
            # Get all Parquet files in this partition
            parquet_files = list(partition_dir.glob("*.parquet"))
            
            if not parquet_files:
                continue
            
            # Extract partition column from directory name
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
        return Backend.SPARK
    
    def supports_feature(self, feature: str) -> bool:
        """
        Check if Spark supports a feature.
        
        Args:
            feature: Feature name
            
        Returns:
            True if supported
        """
        # Spark supports almost everything
        supported_features = {
            "window_functions": True,
            "cte": True,
            "recursive_cte": False,  # Not supported
            "lateral_join": True,
            "pivot": True,
            "unpivot": True,
        }
        
        return supported_features.get(feature, True)
    
    def close(self):
        """Stop Spark session."""
        if self.spark:
            self.spark.stop()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()
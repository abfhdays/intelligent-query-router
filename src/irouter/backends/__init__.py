"""Backend execution engines."""
from irouter.backends.base import BaseBackend
from irouter.backends.duckdb_backend import DuckDBBackend
from irouter.backends.polars_backend import PolarsBackend
from irouter.backends.spark_backend import SparkBackend

__all__ = ["BaseBackend", "DuckDBBackend", "PolarsBackend", "SparkBackend"]
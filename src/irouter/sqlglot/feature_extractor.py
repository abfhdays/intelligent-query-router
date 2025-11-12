"""Extract query complexity features from SQL AST for cost estimation."""
from typing import Optional
from sqlglot import exp

from irouter.core.types import PruningResult
from irouter.selector.cost_estimator import QueryFeatures


class FeatureExtractor:
    """Extracts query complexity features from SQL AST."""
    
    def __init__(self):
        """Initialize feature extractor."""
        pass
    
    def extract_features(
        self, 
        ast: exp.Expression,
        pruning_result: PruningResult
    ) -> QueryFeatures:
        """
        Extract query complexity features from SQL AST.
        
        Args:
            ast: Parsed and optimized SQL expression
            pruning_result: Result from partition pruning (for data size)
            
        Returns:
            QueryFeatures with extracted metrics
            
        Example:
            >>> extractor = FeatureExtractor()
            >>> ast = parser.parse("SELECT * FROM sales WHERE date > '2024-01-01'")
            >>> features = extractor.extract_features(ast, pruning_result)
            >>> print(features.num_joins)  # 0
        """
        # Extract all features
        num_joins = self._count_joins(ast)
        num_aggregations = self._count_aggregations(ast)
        num_window_functions = self._count_window_functions(ast)
        has_distinct = self._has_distinct(ast)
        has_order_by = self._has_order_by(ast)
        selectivity = self._estimate_selectivity(ast)
        
        return QueryFeatures(
            estimated_scan_size_gb=pruning_result.size_gb,
            num_joins=num_joins,
            num_aggregations=num_aggregations,
            num_window_functions=num_window_functions,
            has_distinct=has_distinct,
            has_order_by=has_order_by,
            selectivity=selectivity
        )
    
    def _count_joins(self, ast: exp.Expression) -> int:
        """
        Count number of JOIN operations in query.
        
        Args:
            ast: SQL expression
            
        Returns:
            Number of JOINs (INNER, LEFT, RIGHT, FULL, CROSS)
        """
        return sum(1 for _ in ast.find_all(exp.Join))
    
    def _count_aggregations(self, ast: exp.Expression) -> int:
        """
        Count number of aggregation operations.
        
        Counts both aggregation functions (SUM, COUNT, AVG, etc.)
        and GROUP BY clauses.
        
        Args:
            ast: SQL expression
            
        Returns:
            Number of aggregation operations
        """
        # Count aggregation functions
        agg_function_types = (
            exp.Count,
            exp.Sum,
            exp.Avg,
            exp.Min,
            exp.Max,
            exp.GroupConcat,
            exp.ArrayAgg,
            exp.Stddev,
            exp.Variance,
        )
        
        num_agg_functions = sum(1 for _ in ast.find_all(*agg_function_types))
        
        # Check if GROUP BY exists (indicates aggregation even without AGG functions)
        has_group_by = ast.find(exp.Group) is not None
        
        # Return max of function count and 1 if GROUP BY exists
        if has_group_by:
            return max(num_agg_functions, 1)
        
        return num_agg_functions
    
    def _count_window_functions(self, ast: exp.Expression) -> int:
        """
        Count number of window functions (OVER clause).
        
        Args:
            ast: SQL expression
            
        Returns:
            Number of window functions
            
        Examples:
            ROW_NUMBER() OVER (...), RANK() OVER (...), etc.
        """
        return sum(1 for _ in ast.find_all(exp.Window))
    
    def _has_distinct(self, ast: exp.Expression) -> bool:
        """
        Check if query uses DISTINCT.
        
        Args:
            ast: SQL expression
            
        Returns:
            True if DISTINCT is used
        """
        # Check for SELECT DISTINCT
        select = ast.find(exp.Select)
        if select and select.distinct:
            return True
        
        # Check for COUNT(DISTINCT col)
        for count_expr in ast.find_all(exp.Count):
            if count_expr.this and hasattr(count_expr.this, 'distinct'):
                if count_expr.this.distinct:
                    return True
        
        return False
    
    def _has_order_by(self, ast: exp.Expression) -> bool:
        """
        Check if query has ORDER BY clause.
        
        Args:
            ast: SQL expression
            
        Returns:
            True if ORDER BY is present
        """
        return ast.find(exp.Order) is not None
    
    def _estimate_selectivity(self, ast: exp.Expression) -> float:
        """
        Estimate query selectivity (fraction of rows returned).
        
        This is a simple heuristic-based estimate. More sophisticated
        approaches would use column statistics and predicate analysis.
        
        Args:
            ast: SQL expression
            
        Returns:
            Estimated selectivity between 0.0 and 1.0
            
        Heuristics:
            - No WHERE: 1.0 (all rows)
            - Has WHERE: 0.5 (assume 50% filtered)
            - Has equality predicates: 0.1 per predicate
        """
        where = ast.find(exp.Where)
        
        if not where:
            # No filtering, return all rows
            return 1.0
        
        # Count predicates
        num_eq_predicates = sum(1 for _ in where.find_all(exp.EQ))
        num_predicates = (
            sum(1 for _ in where.find_all(exp.EQ)) +
            sum(1 for _ in where.find_all(exp.GT)) +
            sum(1 for _ in where.find_all(exp.GTE)) +
            sum(1 for _ in where.find_all(exp.LT)) +
            sum(1 for _ in where.find_all(exp.LTE))
        )
        
        # Simple heuristic:
        # - Equality predicates are very selective (10% each)
        # - Range predicates are less selective (50% each)
        if num_eq_predicates > 0:
            # Each equality cuts down by ~90%
            selectivity = 0.1 ** num_eq_predicates
        elif num_predicates > 0:
            # Range predicates are less selective
            selectivity = 0.5
        else:
            # Has WHERE but we can't estimate, assume moderate filtering
            selectivity = 0.5
        
        # Clamp between 0.01 and 1.0
        return max(0.01, min(1.0, selectivity))
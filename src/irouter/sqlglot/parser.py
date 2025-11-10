"""SQL parsing and optimization using SQLGlot."""
from typing import List, Optional
import sqlglot
from sqlglot import exp
from sqlglot.optimizer import optimize


class SQLParser:
    """Parses and optimizes SQL queries using SQLGlot."""
    
    def __init__(self, dialect: str = "spark"):
        """
        Initialize parser.
        
        Args:
            dialect: SQL dialect (spark, postgres, snowflake, etc.)
        """
        self.dialect = dialect
    
    def parse(self, sql: str) -> exp.Expression:
        """
        Parse SQL string into AST.
        
        Args:
            sql: SQL query string
            
        Returns:
            SQLGlot expression (AST)
        """
        try:
            return sqlglot.parse_one(sql, dialect=self.dialect)
        except Exception as e:
            raise ValueError(f"Failed to parse SQL: {e}")
    
    def optimize(self, ast: exp.Expression, schema: Optional[dict] = None) -> exp.Expression:
        """
        Apply optimization rules to AST.
        
        Args:
            ast: Parsed SQL expression
            schema: Optional schema information
            
        Returns:
            Optimized AST
        """
        return optimize(ast, schema=schema, dialect=self.dialect)
    
    def extract_tables(self, ast: exp.Expression) -> List[str]:
        """
        Extract all table names from query.
        
        Args:
            ast: Parsed SQL expression
            
        Returns:
            List of table names
        """
        return [table.name for table in ast.find_all(exp.Table)]
    
    def extract_where_clause(self, ast: exp.Expression) -> Optional[exp.Where]:
        """
        Extract WHERE clause from query.
        
        Args:
            ast: Parsed SQL expression
            
        Returns:
            WHERE clause or None
        """
        return ast.find(exp.Where)
    
    def to_sql(self, ast: exp.Expression) -> str:
        """
        Convert AST back to SQL string.
        
        Args:
            ast: SQLGlot expression
            
        Returns:
            SQL string
        """
        return ast.sql(dialect=self.dialect, pretty=True)
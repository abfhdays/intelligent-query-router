"""Quick verification that SQLGlot integration works."""
from irouter.sqlglot.parser import SQLParser
from rich.console import Console
from rich.syntax import Syntax

console = Console()

def main():
    """Test basic SQL parsing and optimization."""
    
    # Initialize parser
    parser = SQLParser(dialect="spark")
    
    # Define schema
    schema = {
        "bar": {
            "a": "INT",
            "b": "INT",
        },
        "baz": {
            "a": "INT",
            "c": "VARCHAR",
        }
    }
    
    # Test query (can use unqualified columns now)
    sql = """
    SELECT 
        a,
        b + 1 AS b_plus_one
    FROM sales
    WHERE a > 1
    """
    
    console.print("\n[bold cyan]Original SQL:[/bold cyan]")
    console.print(Syntax(sql, "sql", theme="monokai"))
    
    # Parse
    console.print("\n[bold cyan]Step 1: Parsing...[/bold cyan]")
    ast = parser.parse(sql)
    console.print(f"✓ Parsed successfully. AST type: {type(ast).__name__}")
    
    # Extract tables
    console.print("\n[bold cyan]Step 2: Extracting tables...[/bold cyan]")
    tables = parser.extract_tables(ast)
    console.print(f"✓ Found tables: {tables}")
    
    # Extract WHERE clause
    console.print("\n[bold cyan]Step 3: Extracting WHERE clause...[/bold cyan]")
    where = parser.extract_where_clause(ast)
    if where:
        console.print(f"✓ Found WHERE clause: {where.this}")
    
    # Optimize
    console.print("\n[bold cyan]Step 4: Optimizing...[/bold cyan]")
    optimized = parser.optimize(ast)
    optimized_sql = parser.to_sql(optimized)
    console.print(Syntax(optimized_sql, "sql", theme="monokai"))
    
    console.print("\n[bold green]✓ All tests passed! Setup is working.[/bold green]")

if __name__ == "__main__":
    main()

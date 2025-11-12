"""Test query feature extraction."""
from irouter.sqlglot.parser import SQLParser
from irouter.sqlglot.feature_extractor import FeatureExtractor
from irouter.optimizer.partition_pruning import PartitionPruner
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def test_query_features(sql: str, description: str):
    """Test feature extraction for a single query."""
    console.print(f"\n[bold cyan]{description}[/bold cyan]")
    console.print(f"SQL: {sql}\n")
    
    # Parse
    parser = SQLParser()
    ast = parser.parse(sql)
    
    # Create dummy pruning result
    from irouter.core.types import PruningResult
    pruning_result = PruningResult(
        partitions_to_scan=[],
        total_partitions=30,
        total_size_bytes=int(5 * 1024**3),  # 5 GB
        total_files=30,
    )
    
    # Extract features
    extractor = FeatureExtractor()
    features = extractor.extract_features(ast, pruning_result)
    
    # Display
    table = Table(show_header=False)
    table.add_column("Feature", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Data Size (GB)", f"{features.estimated_scan_size_gb:.2f}")
    table.add_row("Joins", str(features.num_joins))
    table.add_row("Aggregations", str(features.num_aggregations))
    table.add_row("Window Functions", str(features.num_window_functions))
    table.add_row("Has DISTINCT", str(features.has_distinct))
    table.add_row("Has ORDER BY", str(features.has_order_by))
    table.add_row("Selectivity", f"{features.selectivity:.2%}")
    table.add_row("Complexity Score", f"{features.complexity_score:.1f}")
    
    console.print(table)


def main():
    """Run feature extraction tests."""
    console.print(Panel.fit(
        "[bold cyan]Query Feature Extraction Tests[/bold cyan]",
        border_style="cyan"
    ))
    
    # Test 1: Simple scan
    test_query_features(
        "SELECT * FROM sales",
        "Test 1: Simple Full Scan"
    )
    
    # Test 2: With filter
    test_query_features(
        "SELECT * FROM sales WHERE date >= '2024-11-01'",
        "Test 2: Filtered Scan"
    )
    
    # Test 3: With aggregation
    test_query_features(
        "SELECT region, SUM(amount) FROM sales GROUP BY region",
        "Test 3: Aggregation Query"
    )
    
    # Test 4: With join
    test_query_features(
        """
        SELECT s.customer_id, SUM(s.amount)
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        WHERE s.date >= '2024-11-01'
        GROUP BY s.customer_id
        """,
        "Test 4: Join + Aggregation"
    )
    
    # Test 5: Complex query
    test_query_features(
        """
        SELECT DISTINCT customer_id,
               SUM(amount) OVER (PARTITION BY region) as regional_total
        FROM sales
        WHERE date >= '2024-11-01'
        ORDER BY customer_id
        """,
        "Test 5: Complex Query (DISTINCT + Window + ORDER BY)"
    )
    
    # Test 6: Multiple joins
    test_query_features(
        """
        SELECT s.customer_id, c.name, p.product_name, SUM(s.amount)
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        JOIN products p ON s.product_id = p.id
        WHERE s.date >= '2024-11-01'
        GROUP BY s.customer_id, c.name, p.product_name
        ORDER BY SUM(s.amount) DESC
        """,
        "Test 6: Multiple Joins + Aggregation + Order"
    )
    
    console.print("\n[bold green]✓ All feature extraction tests complete![/bold green]")


if __name__ == "__main__":
    main()
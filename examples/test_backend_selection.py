"""Test backend selection logic."""
from irouter.optimizer.partition_pruning import PartitionPruner
from irouter.selector.backend_selector import BackendSelector
from irouter.selector.cost_estimator import QueryFeatures
from irouter.core.types import Backend
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def test_small_query():
    """Test with small dataset (< 1 GB)."""
    console.print("\n[bold cyan]Test 1: Small Query (< 1 GB)[/bold cyan]")
    
    pruner = PartitionPruner(data_path="./data")
    selector = BackendSelector()
    
    # Query with good filtering
    sql = """
        SELECT customer_id, SUM(amount) as total
        FROM sales
        WHERE date = '2024-11-01'
        GROUP BY customer_id
    """
    
    # Prune partitions
    pruning_result = pruner.prune(
        table_name="sales",
        sql=sql,
        schema={"sales": {"date": "DATE", "customer_id": "VARCHAR", "amount": "DECIMAL"}}
    )
    
    console.print(f"Data size: {pruning_result.size_gb:.2f} GB")
    console.print(f"Partitions: {pruning_result.partitions_scanned}/{pruning_result.total_partitions}")
    
    # Extract query features (simple for now)
    query_features = QueryFeatures(
        estimated_scan_size_gb=pruning_result.size_gb,
        num_joins=0,
        num_aggregations=1,
        num_window_functions=0,
        has_distinct=False,
        has_order_by=False,
    )
    
    # Select backend
    choice = selector.select_backend(pruning_result, query_features)
    
    console.print(f"\n[bold green]Selected: {choice.backend.value}[/bold green]")
    console.print(f"Reasoning: {choice.reasoning}")
    
    # Show cost table
    cost_table = Table(title="Cost Estimates", show_header=True, header_style="bold cyan")
    cost_table.add_column("Backend")
    cost_table.add_column("Total Time (s)")
    cost_table.add_column("Scan (s)")
    cost_table.add_column("Compute (s)")
    cost_table.add_column("Overhead (s)")
    cost_table.add_column("Memory (GB)")
    
    for backend, estimate in choice.all_estimates.items():
        if estimate.estimated_time_sec == float('inf'):
            cost_table.add_row(
                backend.value,
                "INFEASIBLE",
                "-", "-", "-", "-"
            )
        else:
            marker = "⭐" if backend == choice.backend else ""
            cost_table.add_row(
                f"{backend.value} {marker}",
                f"{estimate.estimated_time_sec:.2f}",
                f"{estimate.scan_cost:.2f}",
                f"{estimate.compute_cost:.2f}",
                f"{estimate.overhead_cost:.2f}",
                f"{estimate.estimated_memory_gb:.2f}"
            )
    
    console.print(cost_table)


def test_medium_query():
    """Test with medium dataset (10-50 GB simulated)."""
    console.print("\n[bold cyan]Test 2: Medium Query (simulated 15 GB)[/bold cyan]")
    
    pruner = PartitionPruner(data_path="./data")
    selector = BackendSelector()
    
    # Query all data
    sql = "SELECT * FROM sales"
    
    pruning_result = pruner.prune(
        table_name="sales",
        sql=sql,
    )
    
    # Simulate larger dataset by scaling up
    simulated_size_gb = 15.0
    console.print(f"Simulated data size: {simulated_size_gb} GB")
    
    query_features = QueryFeatures(
        estimated_scan_size_gb=simulated_size_gb,
        num_joins=2,
        num_aggregations=1,
        num_window_functions=0,
        has_distinct=False,
        has_order_by=True,
    )
    
    # Create fake pruning result with larger size
    from irouter.core.types import PruningResult
    large_pruning_result = PruningResult(
        partitions_to_scan=pruning_result.partitions_to_scan,
        total_partitions=pruning_result.total_partitions,
        total_size_bytes=int(simulated_size_gb * 1024**3),
        total_files=pruning_result.total_files,
        predicates_applied=[],
    )
    
    choice = selector.select_backend(large_pruning_result, query_features)
    
    console.print(f"\n[bold green]Selected: {choice.backend.value}[/bold green]")
    console.print(f"Reasoning: {choice.reasoning}")
    
    # Show comparison
    console.print("\n[bold]Time Comparison:[/bold]")
    for backend, estimate in choice.all_estimates.items():
        if estimate.estimated_time_sec != float('inf'):
            console.print(f"  {backend.value}: {estimate.estimated_time_sec:.1f}s")


def test_large_query():
    """Test with large dataset (> 100 GB simulated)."""
    console.print("\n[bold cyan]Test 3: Large Query (simulated 150 GB)[/bold cyan]")
    
    selector = BackendSelector()
    
    simulated_size_gb = 150.0
    console.print(f"Simulated data size: {simulated_size_gb} GB")
    
    query_features = QueryFeatures(
        estimated_scan_size_gb=simulated_size_gb,
        num_joins=3,
        num_aggregations=2,
        num_window_functions=1,
        has_distinct=True,
        has_order_by=True,
    )
    
    from irouter.core.types import PruningResult
    large_pruning_result = PruningResult(
        partitions_to_scan=[],
        total_partitions=365,
        total_size_bytes=int(simulated_size_gb * 1024**3),
        total_files=365,
        predicates_applied=[],
    )
    
    choice = selector.select_backend(large_pruning_result, query_features)
    
    console.print(f"\n[bold green]Selected: {choice.backend.value}[/bold green]")
    console.print(f"Reasoning: {choice.reasoning}")


def main():
    """Run all backend selection tests."""
    console.print(Panel.fit(
        "[bold cyan]Backend Selection Tests[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        test_small_query()
        test_medium_query()
        test_large_query()
        
        console.print("\n[bold green]✓ All tests completed![/bold green]")
        
    except FileNotFoundError as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        console.print("[yellow]Run: python scripts/generate_test_data.py[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
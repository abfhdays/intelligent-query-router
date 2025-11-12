"""Test all three backends."""
from irouter.engine import QueryEngine
from irouter.core.types import Backend
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def test_backend(backend: Backend, data_size_desc: str):
    """Test a specific backend."""
    console.print(f"\n[bold cyan]Testing {backend.value.upper()} Backend[/bold cyan]")
    console.print(f"Scenario: {data_size_desc}")
    
    engine = QueryEngine(data_path="./data")
    
    sql = """
        SELECT 
            region,
            COUNT(*) as transactions,
            SUM(amount) as total
        FROM sales
        WHERE date >= '2024-11-01' AND date <= '2024-11-07'
        GROUP BY region
        ORDER BY total DESC
    """
    
    try:
        # Force specific backend
        result = engine.execute(
            sql,
            schema={"sales": {
                "date": "DATE",
                "region": "VARCHAR",
                "amount": "DECIMAL"
            }},
            force_backend=backend
        )
        
        console.print(f"[bold green]✓ {backend.value} executed successfully![/bold green]")
        console.print(f"  Time: {result.execution_time_sec:.3f}s")
        console.print(f"  Rows: {len(result.data)}")
        console.print(f"  Partitions: {result.partitions_scanned}/{result.total_partitions}")
        
        # Show sample results
        if len(result.data) > 0:
            console.print(f"\n  Results:")
            for _, row in result.data.iterrows():
                console.print(f"    {row['region']}: {row['transactions']} txns, ${row['total']:,.2f}")
        
        return True
        
    except Exception as e:
        console.print(f"[bold red]✗ {backend.value} failed: {e}[/bold red]")
        return False


def compare_backends():
    """Compare performance across backends."""
    console.print("\n[bold cyan]Backend Performance Comparison[/bold cyan]")
    
    engine = QueryEngine(data_path="./data")
    
    sql = """
        SELECT COUNT(*), SUM(amount)
        FROM sales
        WHERE date >= '2024-11-01' AND date <= '2024-11-10'
    """
    
    schema = {"sales": {"date": "DATE", "amount": "DECIMAL"}}
    
    results = {}
    
    for backend in [Backend.DUCKDB, Backend.POLARS, Backend.SPARK]:
        try:
            result = engine.execute(sql, schema=schema, force_backend=backend)
            # Round to avoid floating point precision issues
            results[backend] = round(result.execution_time_sec, 6)
        except Exception as e:
            console.print(f"[yellow]Warning: {backend.value} failed: {e}[/yellow]")
            results[backend] = None
    
    # Display comparison
    comparison_table = Table(show_header=True, header_style="bold cyan")
    comparison_table.add_column("Backend")
    comparison_table.add_column("Execution Time", justify="right")
    comparison_table.add_column("Relative Speed")
    
    # Find fastest (minimum non-zero time)
    valid_results = {k: v for k, v in results.items() if v is not None and v > 0}
    
    if not valid_results:
        console.print("[yellow]All backends executed too fast to measure accurately (< 1ms)[/yellow]")
        return
    
    fastest_time = min(valid_results.values())
    
    # If fastest time is essentially 0, all are too fast
    if fastest_time < 0.001:
        console.print("[yellow]Query executed too fast for accurate comparison (< 1ms)[/yellow]")
        for backend in [Backend.DUCKDB, Backend.POLARS, Backend.SPARK]:
            time = results.get(backend)
            if time is not None:
                comparison_table.add_row(
                    backend.value,
                    f"{time:.6f}s" if time > 0 else "< 0.001s",
                    "~1.00x"
                )
        console.print(comparison_table)
        return
    
    # Normal comparison
    for backend in [Backend.DUCKDB, Backend.POLARS, Backend.SPARK]:
        time = results.get(backend)
        if time is not None and time > 0:
            relative = f"{time/fastest_time:.2f}x"
            marker = "⭐" if abs(time - fastest_time) < 0.001 else ""
            comparison_table.add_row(
                f"{backend.value} {marker}",
                f"{time:.3f}s",
                relative
            )
        elif time == 0:
            comparison_table.add_row(
                backend.value,
                "< 0.001s",
                "~1.00x"
            )
        else:
            comparison_table.add_row(
                backend.value,
                "FAILED",
                "-"
            )
    
    console.print(comparison_table)

def main():
    """Run all backend tests."""
    console.print(Panel.fit(
        "[bold cyan]Multi-Backend Tests[/bold cyan]",
        border_style="cyan"
    ))
    
    # Test each backend
    results = {
        "DuckDB": test_backend(Backend.DUCKDB, "Small data (< 1 GB)"),
        "Polars": test_backend(Backend.POLARS, "Medium data (simulated)"),
        "Spark": test_backend(Backend.SPARK, "Large data (simulated)"),
    }
    
    # Compare backends
    compare_backends()
    
    # Summary
    console.print("\n[bold cyan]Summary:[/bold cyan]")
    for name, success in results.items():
        status = "[green]✓[/green]" if success else "[red]✗[/red]"
        console.print(f"  {status} {name}")
    
    if all(results.values()):
        console.print("\n[bold green]✓ All backends working![/bold green]")
    else:
        console.print("\n[yellow]⚠ Some backends failed (check dependencies)[/yellow]")


if __name__ == "__main__":
    main()
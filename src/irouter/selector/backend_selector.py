"""Backend selection logic."""
from typing import Optional, Dict
from dataclasses import dataclass

from irouter.core.types import Backend, CostEstimate, PruningResult
from irouter.selector.cost_estimator import CostEstimator, QueryFeatures


@dataclass
class BackendChoice:
    """Result of backend selection."""
    backend: Backend
    cost_estimate: CostEstimate
    all_estimates: Dict[Backend, CostEstimate]
    reasoning: str


class BackendSelector:
    """
    Selects optimal backend based on cost estimates.
    
    Uses cost-based optimization to pick the backend with
    minimum estimated execution time.
    """
    
    def __init__(self):
        """Initialize backend selector."""
        self.cost_estimator = CostEstimator()
    
    def select_backend(
        self,
        pruning_result: PruningResult,
        query_features: QueryFeatures,
        force_backend: Optional[Backend] = None
    ) -> BackendChoice:
        """
        Select optimal backend for query execution.
        
        Args:
            pruning_result: Result from partition pruning
            query_features: Extracted query features
            force_backend: Optional backend to force (for testing)
            
        Returns:
            BackendChoice with selected backend and reasoning
        """
        # Get cost estimates for all backends
        estimates = self.cost_estimator.estimate_all_backends(
            pruning_result, query_features
        )
        
        # If backend is forced, use that
        if force_backend:
            return BackendChoice(
                backend=force_backend,
                cost_estimate=estimates[force_backend],
                all_estimates=estimates,
                reasoning=f"Forced to use {force_backend.value}"
            )
        
        # Select backend with minimum cost
        best_backend = min(
            estimates.keys(),
            key=lambda b: estimates[b].estimated_time_sec
        )
        
        best_estimate = estimates[best_backend]
        
        # Build reasoning
        reasoning = self._build_reasoning(best_backend, estimates)
        
        return BackendChoice(
            backend=best_backend,
            cost_estimate=best_estimate,
            all_estimates=estimates,
            reasoning=reasoning
        )
    
    def _build_reasoning(
        self,
        selected_backend: Backend,
        all_estimates: Dict[Backend, CostEstimate]
    ) -> str:
        """
        Build human-readable reasoning for backend selection.
        
        Args:
            selected_backend: The selected backend
            all_estimates: All cost estimates
            
        Returns:
            Reasoning string
        """
        selected = all_estimates[selected_backend]
        
        # Compare to other backends
        comparisons = []
        for backend, estimate in all_estimates.items():
            if backend != selected_backend:
                if estimate.estimated_time_sec == float('inf'):
                    comparisons.append(
                        f"{backend.value} infeasible ({estimate.reasoning})"
                    )
                else:
                    speedup = estimate.estimated_time_sec / selected.estimated_time_sec
                    comparisons.append(
                        f"{speedup:.1f}x faster than {backend.value}"
                    )
        
        reasoning = (
            f"Selected {selected_backend.value}: {selected.reasoning}. "
            f"{', '.join(comparisons)}."
        )
        
        return reasoning
    
    def explain_selection(self, choice: BackendChoice) -> str:
        """
        Generate detailed explanation of backend selection.
        
        Args:
            choice: BackendChoice result
            
        Returns:
            Multi-line explanation string
        """
        lines = []
        lines.append(f"Selected Backend: {choice.backend.value}")
        lines.append(f"\nReasoning: {choice.reasoning}")
        lines.append(f"\nCost Breakdown:")
        lines.append(f"  Estimated time: {choice.cost_estimate.estimated_time_sec:.2f}s")
        lines.append(f"  - Scan: {choice.cost_estimate.scan_cost:.2f}s")
        lines.append(f"  - Compute: {choice.cost_estimate.compute_cost:.2f}s")
        lines.append(f"  - Overhead: {choice.cost_estimate.overhead_cost:.2f}s")
        lines.append(f"  Memory needed: {choice.cost_estimate.estimated_memory_gb:.2f} GB")
        
        lines.append(f"\nAll Backend Estimates:")
        for backend, estimate in choice.all_estimates.items():
            if estimate.estimated_time_sec == float('inf'):
                lines.append(f"  {backend.value}: INFEASIBLE")
            else:
                lines.append(f"  {backend.value}: {estimate.estimated_time_sec:.2f}s")
        
        return '\n'.join(lines)
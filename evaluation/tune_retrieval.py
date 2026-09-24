"""Retrieval tuning experiment script."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from evaluation.tuning import run_retrieval_tuning_experiment


def main():
    """Main entry point for retrieval tuning experiment."""
    print("=" * 80)
    print("HealthCompass Retrieval Tuning Experiment")
    print("=" * 80)
    print()

    # Define paths
    queries_path = Path("evaluation/retrieval_queries.json")
    output_dir = Path("evaluation/results")

    # Check if queries file exists
    if not queries_path.exists():
        print(f"ERROR: Test queries file not found at {queries_path}")
        sys.exit(1)

    print(f"Loading test queries from: {queries_path}")
    print(f"Output directory: {output_dir}")
    print()

    # Run the experiment
    print("Running retrieval tuning experiment...")
    print()

    # Use mock mode for testing without API key
    use_mock = True
    evaluations, best_config = run_retrieval_tuning_experiment(
        queries_path=queries_path,
        output_dir=output_dir,
        use_mock=use_mock,
    )

    # Print summary
    print("=" * 80)
    print("EXPERIMENT RESULTS")
    print("=" * 80)
    print()

    print("Configuration Comparison:")
    print()
    print(f"{'Configuration':<20} {'k':<10} {'Top-1 Hit Rate':<20} {'Top-k Hit Rate':<20}")
    print("-" * 80)
    for eval_result in evaluations:
        print(
            f"{eval_result.config_name:<20} {eval_result.k:<10} {eval_result.top_1_hit_rate:>6.1%}{'':<14} {eval_result.top_k_hit_rate:>6.1%}"
        )

    print()
    print("=" * 80)
    print("BEST CONFIGURATION")
    print("=" * 80)
    print()
    print(f"Chosen: {best_config.config_name}")
    print(f"k = {best_config.k}")
    print(f"Top-1 hit rate: {best_config.top_1_hit_rate:.1%}")
    print(f"Top-k hit rate: {best_config.top_k_hit_rate:.1%}")
    print()
    print(f"Reason: Selected based on highest top-k hit rate ({best_config.top_k_hit_rate:.1%}) and top-1 hit rate ({best_config.top_1_hit_rate:.1%}).")
    print()

    print("=" * 80)
    print("RESULTS SAVED")
    print("=" * 80)
    print()
    print(f"Detailed JSON: {output_dir / 'retrieval_tuning_results.json'}")
    print(f"Summary JSON: {output_dir / 'retrieval_tuning_summary.json'}")
    print(f"Report: {output_dir / 'retrieval_tuning_report.md'}")
    print()


if __name__ == "__main__":
    main()

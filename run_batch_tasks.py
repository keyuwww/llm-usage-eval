import os
import json
import sys
import time
from pathlib import Path
from datetime import datetime

from run_gdpval_task import run_task


def run_batch(task_ids=None, max_tasks=None, base_dir="gdpval_tasks"):
    """Run multiple GDPval tasks in batch.

    Args:
        task_ids: List of specific task IDs to run. If None, runs all tasks.
        max_tasks: Maximum number of tasks to run. If None, runs all.
        base_dir: Base directory containing downloaded tasks.
    """

    base_path = Path(base_dir)
    if not base_path.exists():
        print("❌ Tasks directory not found. Run download_gdpval_dataset.py first.")
        return

    # Get all task directories
    all_tasks = []
    for task_dir in sorted(base_path.iterdir()):
        if task_dir.is_dir():
            metadata_file = task_dir / "metadata.json"
            if metadata_file.exists():
                all_tasks.append(task_dir.name)

    # Filter to specific task IDs if provided
    if task_ids:
        tasks_to_run = [t for t in all_tasks if t in task_ids]
    else:
        tasks_to_run = all_tasks

    # Limit number of tasks if specified
    if max_tasks:
        tasks_to_run = tasks_to_run[:max_tasks]

    print(f"Running {len(tasks_to_run)} tasks...\n")

    # Track results
    results = {
        "completed": [],
        "failed": [],
        "start_time": datetime.now().isoformat(),
    }

    for i, task_id in enumerate(tasks_to_run, 1):
        print(f"\n{'='*80}")
        print(f"Task {i}/{len(tasks_to_run)}: {task_id}")
        print(f"{'='*80}\n")

        try:
            start = time.time()
            run_task(task_id, base_dir)
            duration = time.time() - start

            results["completed"].append({
                "task_id": task_id,
                "duration_seconds": round(duration, 2)
            })
            print(f"\n✅ Task completed in {duration:.2f}s")

        except KeyboardInterrupt:
            print("\n\n⚠️  Batch run interrupted by user")
            break

        except Exception as e:
            print(f"\n❌ Task failed: {e}")
            results["failed"].append({
                "task_id": task_id,
                "error": str(e)
            })

    # Save results
    results["end_time"] = datetime.now().isoformat()
    results_file = f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"\n\n{'='*80}")
    print("BATCH RUN SUMMARY")
    print(f"{'='*80}")
    print(f"Total tasks attempted: {len(tasks_to_run)}")
    print(f"Completed: {len(results['completed'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run GDPval tasks in batch")
    parser.add_argument(
        "--tasks",
        nargs="+",
        help="Specific task IDs to run (space-separated)"
    )
    parser.add_argument(
        "--max",
        type=int,
        help="Maximum number of tasks to run"
    )
    parser.add_argument(
        "--base-dir",
        default="gdpval_tasks",
        help="Base directory containing tasks (default: gdpval_tasks)"
    )

    args = parser.parse_args()

    run_batch(task_ids=args.tasks, max_tasks=args.max, base_dir=args.base_dir)

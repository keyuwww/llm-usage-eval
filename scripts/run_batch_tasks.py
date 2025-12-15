import os
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Set environment variable to use BasicTerminal instead of TmuxTerminal
# This avoids tmux version compatibility issues on older systems
os.environ.setdefault("OPENHANDS_TERMINAL_TYPE", "basic")

# Add scripts directory to path for imports
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from run_one_task import run_task


def run_batch(task_ids=None, max_tasks=None, base_dir="gdpval_tasks", output_dir="output", model="openai/gpt-4o", delay=0):
    """Run multiple GDPval tasks in batch.

    Args:
        task_ids: List of specific task IDs to run. If None, runs all tasks.
        max_tasks: Maximum number of tasks to run. If None, runs all.
        base_dir: Base directory containing downloaded tasks.
        output_dir: Directory to save outputs (default: output).
        model: Model to use (default: openai/gpt-4o).
        delay: Delay in seconds between tasks (default: 0). Use 60-120 for rate limit issues.
    """

    base_path = Path(base_dir)
    if not base_path.exists():
        print("❌ Tasks directory not found. Run download_gdpval_dataset.py first.")
        return

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Extract model name for directory organization (remove provider prefix)
    model_name = model.split("/")[-1] if "/" in model else model

    # Create model-specific output directory
    model_output_path = output_path / model_name
    model_output_path.mkdir(exist_ok=True)

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

    print(f"Running {len(tasks_to_run)} tasks...")
    print(f"Model: {model}")
    print(f"Output directory: {model_output_path.resolve()}\n")

    # Track results
    results = {
        "completed": [],
        "failed": [],
        "start_time": datetime.now().isoformat(),
        "output_directory": str(model_output_path.resolve()),
        "model": model,
        "model_name": model_name,
    }

    for i, task_id in enumerate(tasks_to_run, 1):
        print(f"\n{'='*80}")
        print(f"Task {i}/{len(tasks_to_run)}: {task_id}")
        print(f"{'='*80}\n")

        try:
            start = time.time()
            run_task(task_id, base_dir, output_dir, model)
            duration = time.time() - start

            results["completed"].append({
                "task_id": task_id,
                "duration_seconds": round(duration, 2),
                "output_dir": str(model_output_path / task_id)
            })
            print(f"\n✅ Task {i}/{len(tasks_to_run)} completed in {duration:.2f}s")

            # Add delay between tasks if specified (for rate limiting)
            if delay > 0 and i < len(tasks_to_run):
                print(f"⏳ Waiting {delay}s before next task (rate limit protection)...")
                time.sleep(delay)

        except KeyboardInterrupt:
            print("\n\n⚠️  Batch run interrupted by user")
            break

        except Exception as e:
            print(f"\n❌ Task {i}/{len(tasks_to_run)} failed: {e}")
            results["failed"].append({
                "task_id": task_id,
                "error": str(e),
                "output_dir": str(model_output_path / task_id)
            })

    # Save results
    results["end_time"] = datetime.now().isoformat()
    results_file = model_output_path / f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"\n\n{'='*80}")
    print("BATCH RUN SUMMARY")
    print(f"{'='*80}")
    print(f"Total tasks attempted: {len(tasks_to_run)}")
    print(f"Completed: {len(results['completed'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"\nModel: {model}")
    print(f"Output directory: {model_output_path.resolve()}")
    print(f"Batch results saved to: {results_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run GDPval tasks in batch")
    parser.add_argument(
        "--tasks",
        nargs="+",
        help="Specific task IDs to run (space-separated)"
    )
    parser.add_argument(
        "--tasks-file",
        help="File containing task IDs (one per line)"
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
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to save outputs (default: output)"
    )
    parser.add_argument(
        "--model",
        default="openai/gpt-4o",
        help="Model to use (default: openai/gpt-4o). Examples: openai/gpt-4o-mini, anthropic/claude-3-5-sonnet-20241022"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=0,
        help="Delay in seconds between tasks (default: 0). Use 60-120 for rate limit issues."
    )

    args = parser.parse_args()

    # Load task IDs from file if provided
    task_ids = args.tasks
    if args.tasks_file:
        print(f"Loading task IDs from {args.tasks_file}...")
        with open(args.tasks_file, "r") as f:
            file_tasks = [line.strip() for line in f if line.strip()]
        if task_ids:
            # Combine with command-line tasks
            task_ids.extend(file_tasks)
        else:
            task_ids = file_tasks
        print(f"Loaded {len(file_tasks)} task IDs from file")

    run_batch(task_ids=task_ids, max_tasks=args.max, base_dir=args.base_dir, output_dir=args.output_dir, model=args.model, delay=args.delay)

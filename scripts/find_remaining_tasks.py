#!/usr/bin/env python3
"""Find tasks that haven't been completed yet."""

import json
from pathlib import Path


def find_remaining_tasks(base_dir="gdpval_tasks", output_dir="output"):
    """Find tasks that haven't been run yet."""

    base_path = Path(base_dir)
    output_path = Path(output_dir)

    if not base_path.exists():
        print(f"❌ Base directory not found: {base_dir}")
        return []

    # Get all available tasks
    all_tasks = []
    for task_dir in sorted(base_path.iterdir()):
        if task_dir.is_dir():
            metadata_file = task_dir / "metadata.json"
            if metadata_file.exists():
                all_tasks.append(task_dir.name)

    # Get completed tasks
    completed_tasks = set()
    if output_path.exists():
        for task_dir in output_path.iterdir():
            if not task_dir.is_dir():
                continue

            exec_metadata_file = task_dir / "execution_metadata.json"
            if exec_metadata_file.exists():
                try:
                    with open(exec_metadata_file) as f:
                        metadata = json.load(f)
                    if metadata.get("status") == "completed":
                        completed_tasks.add(task_dir.name)
                except:
                    pass

    # Find remaining tasks
    remaining_tasks = [t for t in all_tasks if t not in completed_tasks]

    print(f"📊 Task Summary")
    print(f"{'='*80}")
    print(f"Total tasks: {len(all_tasks)}")
    print(f"Completed: {len(completed_tasks)}")
    print(f"Remaining: {len(remaining_tasks)}")
    print(f"{'='*80}\n")

    if remaining_tasks:
        print(f"Remaining tasks ({len(remaining_tasks)}):")
        for i, task_id in enumerate(remaining_tasks[:10], 1):
            print(f"  {i}. {task_id}")

        if len(remaining_tasks) > 10:
            print(f"  ... and {len(remaining_tasks) - 10} more")

    return remaining_tasks


def save_remaining_tasks(remaining_tasks, output_file="remaining_tasks.txt"):
    """Save remaining task IDs to a file."""
    with open(output_file, "w") as f:
        for task_id in remaining_tasks:
            f.write(f"{task_id}\n")
    print(f"\n✅ Saved {len(remaining_tasks)} task IDs to: {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Find remaining tasks to run")
    parser.add_argument(
        "--base-dir",
        default="gdpval_tasks",
        help="Base directory containing tasks (default: gdpval_tasks)"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory (default: output)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save remaining task IDs to remaining_tasks.txt"
    )

    args = parser.parse_args()

    remaining = find_remaining_tasks(args.base_dir, args.output_dir)

    if args.save and remaining:
        save_remaining_tasks(remaining)

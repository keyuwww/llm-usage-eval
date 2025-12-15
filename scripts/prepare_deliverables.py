#!/usr/bin/env python3
"""Prepare deliverable files for GDPval submission."""

import json
import shutil
from pathlib import Path


def prepare_deliverables(output_dir="output/claude-opus-4-5-20251101", deliverable_dir="deliverable_files"):
    """
    Copy output files from evaluation to deliverable_files directory.

    Creates structure: deliverable_files/{task_id}/output_file.ext
    """

    output_path = Path(output_dir)
    deliverable_path = Path(deliverable_dir)

    # Create deliverable directory
    deliverable_path.mkdir(exist_ok=True)

    # Track statistics
    stats = {
        "total_tasks": 0,
        "tasks_with_outputs": 0,
        "total_files_copied": 0,
        "tasks_without_outputs": []
    }

    # Process each task
    for task_dir in sorted(output_path.iterdir()):
        if not task_dir.is_dir():
            continue

        task_id = task_dir.name
        stats["total_tasks"] += 1

        # Read execution metadata to get output files
        metadata_file = task_dir / "execution_metadata.json"
        if not metadata_file.exists():
            print(f"⚠️  No metadata for {task_id}, skipping")
            continue

        with open(metadata_file) as f:
            metadata = json.load(f)

        # Only process completed tasks
        if metadata.get("status") != "completed":
            continue

        output_files = metadata.get("output_files", [])

        if not output_files:
            print(f"⚠️  {task_id}: No output files")
            stats["tasks_without_outputs"].append(task_id)
            continue

        # Create task deliverable directory
        task_deliverable_dir = deliverable_path / task_id
        task_deliverable_dir.mkdir(exist_ok=True)

        # Copy output files
        files_copied = 0
        for filename in output_files:
            src = task_dir / filename
            dst = task_deliverable_dir / filename

            if src.exists():
                shutil.copy2(src, dst)
                files_copied += 1
                print(f"✓ {task_id}/{filename}")
            else:
                print(f"⚠️  {task_id}/{filename} not found")

        if files_copied > 0:
            stats["tasks_with_outputs"] += 1
            stats["total_files_copied"] += files_copied

    # Print summary
    print(f"\n{'='*80}")
    print("DELIVERABLES PREPARATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total completed tasks: {stats['total_tasks']}")
    print(f"Tasks with output files: {stats['tasks_with_outputs']}")
    print(f"Tasks without outputs: {len(stats['tasks_without_outputs'])}")
    print(f"Total files copied: {stats['total_files_copied']}")
    print(f"\nDeliverable directory: {deliverable_path.resolve()}")

    if stats['tasks_without_outputs']:
        print(f"\n⚠️  {len(stats['tasks_without_outputs'])} tasks had no output files:")
        for task_id in stats['tasks_without_outputs'][:10]:
            print(f"  - {task_id}")
        if len(stats['tasks_without_outputs']) > 10:
            print(f"  ... and {len(stats['tasks_without_outputs']) - 10} more")

    # Create a dataset update file with deliverable_files paths and text
    print(f"\n{'='*80}")
    print("CREATING DATASET UPDATE FILE")
    print(f"{'='*80}")

    dataset_updates = []

    # Process all completed tasks (including those without files)
    for task_dir in sorted(output_path.iterdir()):
        if not task_dir.is_dir():
            continue

        task_id = task_dir.name

        # Check if task completed
        metadata_file = task_dir / "execution_metadata.json"
        if not metadata_file.exists():
            continue

        with open(metadata_file) as f:
            metadata = json.load(f)

        if metadata.get("status") != "completed":
            continue

        # Clean up old log files - keep only the newest
        log_files = sorted(list(task_dir.glob("execution_*.log")))
        if len(log_files) > 1:
            newest_log = log_files[-1]
            for old_log in log_files[:-1]:
                try:
                    old_log.unlink()
                    print(f"  🗑️  Deleted old log: {task_id}/{old_log.name}")
                except Exception as e:
                    print(f"  ⚠️  Could not delete {old_log.name}: {e}")

        # Check for deliverable files
        task_deliverable_dir = deliverable_path / task_id
        deliverable_files = []
        if task_deliverable_dir.exists():
            files = [f.name for f in task_deliverable_dir.iterdir() if f.is_file()]
            deliverable_files = [f"deliverable_files/{task_id}/{f}" for f in files]

        # Extract deliverable_text from execution logs
        deliverable_text = ""

        # Only extract text if there are NO deliverable files
        # (if there are files, the deliverable is in the files, not text)
        if not deliverable_files and log_files:
            log_file = log_files[-1]  # Use the newest log
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()

                # Look for agent's final "Finish with message" - this is usually the answer
                if "Finish with message:" in log_content:
                    # Find the last occurrence (final answer)
                    idx = log_content.rfind("Finish with message:")
                    if idx != -1:
                        # Extract everything after "Finish with message:"
                        remaining = log_content[idx + len("Finish with message:"):]

                        # Take until the next major section marker or end
                        for stop_marker in ["\n\nTokens:", "\nAgent Action", "\nObservation", "Task completed", "📦"]:
                            if stop_marker in remaining:
                                remaining = remaining.split(stop_marker)[0]
                                break

                        deliverable_text = remaining.strip()
                        # Limit length
                        if len(deliverable_text) > 2000:
                            deliverable_text = deliverable_text[:2000] + "..."

            except Exception as e:
                print(f"⚠️  Could not read log for {task_id}: {e}")

        # Only add if there are files OR text
        if deliverable_files or deliverable_text:
            dataset_updates.append({
                "task_id": task_id,
                "deliverable_files": deliverable_files,
                "deliverable_text": deliverable_text
            })

    # Save dataset updates
    update_file = Path("dataset_updates.json")
    with open(update_file, "w") as f:
        json.dump(dataset_updates, f, indent=2)

    print(f"✓ Created {update_file} with {len(dataset_updates)} task updates")
    print(f"\nNext steps:")
    print(f"1. Upload deliverable_files/ directory to your HuggingFace dataset")
    print(f"2. Add deliverable_text and deliverable_files columns using dataset_updates.json")
    print(f"3. Make the dataset public")
    print(f"4. Submit the dataset URL")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Prepare deliverable files for GDPval submission")
    parser.add_argument(
        "--output-dir",
        default="output/claude-opus-4-5-20251101",
        help="Output directory containing evaluation results"
    )
    parser.add_argument(
        "--deliverable-dir",
        default="deliverable_files",
        help="Directory to create deliverables in (default: deliverable_files)"
    )

    args = parser.parse_args()
    prepare_deliverables(args.output_dir, args.deliverable_dir)

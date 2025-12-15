import json
from pathlib import Path

# List all downloaded tasks
base_dir = Path("gdpval_tasks")

if not base_dir.exists():
    print("❌ No tasks found. Run download_gdpval_dataset.py first.")
    exit(1)

tasks = []
for task_dir in sorted(base_dir.iterdir()):
    if task_dir.is_dir():
        metadata_file = task_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                tasks.append({
                    "task_id": metadata["task_id"],
                    "sector": metadata.get("sector", "N/A"),
                    "occupation": metadata.get("occupation", "N/A"),
                    "has_files": len(list(task_dir.glob("*"))) > 1  # More than just metadata.json
                })

print(f"Total tasks: {len(tasks)}\n")
print(f"{'Task ID':<40} {'Sector':<20} {'Occupation':<30} {'Files'}")
print("=" * 100)

for task in tasks:
    files_status = "✓" if task["has_files"] else "✗"
    print(f"{task['task_id']:<40} {task['sector']:<20} {task['occupation']:<30} {files_status}")

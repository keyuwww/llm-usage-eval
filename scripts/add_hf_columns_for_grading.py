from datasets import load_dataset
import json

# Load your duplicated dataset
ds = load_dataset("keyuuw/gdpval-claude-opus-eval")

# Load the updates from prepare_deliverables.py
with open("dataset_updates.json") as f:
    updates = json.load(f)

# Create a mapping of task_id -> update
update_map = {u["task_id"]: u for u in updates}

# Add columns to dataset
def add_deliverable_columns(example):
    task_id = example["task_id"]
    if task_id in update_map:
        example["deliverable_files"] = update_map[task_id]["deliverable_files"]
        example["deliverable_text"] = update_map[task_id]["deliverable_text"]
    else:
        example["deliverable_files"] = []
        example["deliverable_text"] = ""
    return example

ds = ds.map(add_deliverable_columns)

# Save the updated dataset
ds.save_to_disk("./updated_dataset")
ds.push_to_hub("keyuuw/gdpval-claude-opus-eval")
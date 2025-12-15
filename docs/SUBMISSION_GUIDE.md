# GDPval Evaluation Submission Guide

## Step 1: Prepare Deliverable Files (Local)

Run the preparation script:
```bash
python3 scripts/prepare_deliverables.py --output-dir output/claude-opus-4-5-20251101
```

This creates:
- `deliverable_files/` directory with your output files organized by task_id
- `dataset_updates.json` with the deliverable_files paths for each task

## Step 2: Create HuggingFace Dataset

### 2.1 Duplicate the GDPval Dataset

1. Go to https://huggingface.co/datasets/openai/gdpval
2. Click "Duplicate this dataset" (or use https://huggingface.co/spaces/huggingface-projects/repo-duplicator)
3. Name it something like: `{your-username}/gdpval-claude-opus-eval`
4. Make sure it's set to **Public**

### 2.2 Download the Original Dataset

```bash
# Install huggingface-cli if needed
pip install huggingface_hub

# Download the dataset
git clone https://huggingface.co/datasets/{your-username}/gdpval-claude-opus-eval
cd gdpval-claude-opus-eval
```

## Step 3: Add Your Deliverable Files

### 3.1 Copy deliverable_files directory

```bash
# Copy from your eval directory to the HF dataset repo
cp -r /path/to/llm-usage-eval/deliverable_files ./
```

### 3.2 Add deliverable_text and deliverable_files columns

You need to modify the dataset to add two new columns. Here's a Python script:

```python
from datasets import load_dataset
import json

# Load your duplicated dataset
ds = load_dataset("{your-username}/gdpval-claude-opus-eval")

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
ds.push_to_hub("{your-username}/gdpval-claude-opus-eval")
```

## Step 4: Upload to HuggingFace

### 4.1 Commit and push

```bash
git add deliverable_files/
git add data/  # The updated dataset files
git commit -m "Add Claude Opus 4.5 evaluation results"
git push
```

### 4.2 Verify Upload

1. Go to your dataset page: `https://huggingface.co/datasets/{your-username}/gdpval-claude-opus-eval`
2. Check that `deliverable_files/` directory is visible
3. Click "Dataset viewer" to verify the new columns are present
4. Verify it's set to **Public**

## Step 5: Submit

1. Go to https://evals.openai.com/gdpval/grading
2. Submit your dataset URL:
   ```
   https://huggingface.co/datasets/{your-username}/gdpval-claude-opus-eval
   ```

## Notes

- Only completed tasks with output files will be included
- The `deliverable_text` column can be left empty or filled with summary text
- Make sure all files in `deliverable_files/` are properly uploaded
- The dataset must be **Public** for submission

## Troubleshooting

**Q: Some tasks don't have output files**
A: This is normal - tasks that failed or didn't produce files won't have deliverables. Only completed tasks with outputs are included.

**Q: How do I fill deliverable_text?**
A: You can leave it empty, or extract summary information from execution logs if needed.

**Q: The dataset is too large**
A: You can use Git LFS for large files:
```bash
git lfs install
git lfs track "deliverable_files/**/*"
git add .gitattributes
```

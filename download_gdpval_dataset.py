import os
import json
import urllib.request
import urllib.parse
from pathlib import Path
from datasets import load_dataset
from tqdm import tqdm

# Load the full dataset
print("Loading GDPval dataset...")
dataset = load_dataset("openai/gdpval", split="train")
print(f"Loaded {len(dataset)} tasks")

# Base directory for all tasks
base_dir = Path("gdpval_tasks")
base_dir.mkdir(exist_ok=True)

# Download all tasks and their files
for idx, sample in enumerate(tqdm(dataset, desc="Downloading tasks")):
    task_id = sample.get("task_id", f"task_{idx}")

    # Create task directory
    task_dir = base_dir / task_id
    task_dir.mkdir(exist_ok=True)

    # Save task metadata
    metadata = {
        "task_id": task_id,
        "prompt": sample.get("prompt", ""),
        "sector": sample.get("sector", ""),
        "occupation": sample.get("occupation", ""),
        "reference_files": sample.get("reference_files", []),
        "reference_file_urls": sample.get("reference_file_urls", []),
    }

    with open(task_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Download reference files
    reference_file_urls = sample.get("reference_file_urls", [])
    if reference_file_urls:
        for url in reference_file_urls:
            try:
                # Extract filename from URL (decode any URL encoding)
                filename = urllib.parse.unquote(url.split("/")[-1])
                filepath = task_dir / filename

                # Skip if already downloaded
                if filepath.exists():
                    continue

                # URL encode the entire URL to handle spaces and special characters
                encoded_url = urllib.parse.quote(url, safe=':/')
                urllib.request.urlretrieve(encoded_url, filepath)

            except Exception as e:
                print(f"\n⚠️  Error downloading {url} for task {task_id}: {e}")
                # Save error info
                with open(task_dir / "download_errors.txt", "a") as f:
                    f.write(f"{url}: {e}\n")

print(f"\n✅ Download complete! All tasks saved to: {base_dir.absolute()}")
print(f"Total tasks: {len(dataset)}")

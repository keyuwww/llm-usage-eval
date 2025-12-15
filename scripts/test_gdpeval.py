import os
import urllib.request
import urllib.parse
from pathlib import Path
from datasets import load_dataset

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool

# -----------------------------
# 1. Load ONE sample from GDPval
# -----------------------------
dataset = load_dataset("openai/gdpval", split="train")

sample = dataset[0]  # pick any sample; this is one evaluation task
prompt = sample["prompt"]
print("Loaded prompt:\n", prompt)
print("\nAvailable fields in sample:", list(sample.keys()))
print("\nReference file URLs:", sample.get("reference_file_urls", []))

# -----------------------------
# 2. Configure the OpenHands LLM
# -----------------------------
llm = LLM(
    model="openai/gpt-4o",                     # or another supported model
    api_key=os.getenv("OPENAI_API_KEY"),    
)

# -----------------------------
# 3. Build the Agent with Tools
# -----------------------------
agent = Agent(
    llm=llm,
    tools=[
        Tool(name=TerminalTool.name),
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
    ],
)

# -----------------------------
# 4. Create a conversation workspace
# -----------------------------
# Create a separate folder for this task based on task_id
task_id = sample.get("task_id", "unknown_task")
workspace = Path(os.getcwd()) / f"tasks/{task_id}"
workspace.mkdir(parents=True, exist_ok=True)

print(f"\nWorkspace: {workspace}")

# Download reference files if they exist
reference_file_urls = sample.get("reference_file_urls", [])
downloaded_files = []
if reference_file_urls:
    print(f"\nDownloading {len(reference_file_urls)} reference files...")
    for url in reference_file_urls:
        # Extract filename from URL (decode any URL encoding)
        filename = urllib.parse.unquote(url.split("/")[-1])
        filepath = workspace / filename

        print(f"  Downloading {filename}...")
        # URL encode the entire URL to handle spaces and special characters
        encoded_url = urllib.parse.quote(url, safe=':/')
        urllib.request.urlretrieve(encoded_url, filepath)
        print(f"  Saved to {filepath}")
        downloaded_files.append(filename)

conversation = Conversation(agent=agent, workspace=str(workspace))

# -----------------------------
# 5. Send the task to the agent
# -----------------------------
# First, inform the agent about available files and how to handle them
if downloaded_files:
    # Put critical instructions FIRST and make them very prominent
    files_info = "=" * 80 + "\n"
    files_info += "CRITICAL: READ THIS BEFORE STARTING\n"
    files_info += "=" * 80 + "\n\n"

    if any(f.endswith(('.xlsx', '.xls', '.csv')) for f in downloaded_files):
        files_info += "⚠️  EXCEL FILE HANDLING REQUIREMENTS:\n\n"
        files_info += "❌ DO NOT use 'python -c' with multi-line code (causes syntax errors)\n"
        files_info += "❌ DO NOT use file_editor tool to read/edit .xlsx files (they are binary)\n\n"
        files_info += "✅ REQUIRED WORKFLOW:\n"
        files_info += "   Step 1: Create a new .py file (e.g., 'analysis.py') using file_editor tool\n"
        files_info += "   Step 2: Write your pandas/Python code in that .py file\n"
        files_info += "   Step 3: Run it with terminal tool: python analysis.py\n\n"

    files_info += "Available reference files in your workspace:\n"
    files_info += "\n".join(f"  - {filename}" for filename in downloaded_files)
    files_info += "\n\n" + "=" * 80 + "\n"
    files_info += "TASK:\n"
    files_info += "=" * 80 + "\n"
    files_info += prompt
    conversation.send_message(files_info)
else:
    conversation.send_message(prompt)

# Run the agent
conversation.run()

print("\nAll done!")

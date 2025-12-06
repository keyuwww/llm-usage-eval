import os
import json
import sys
from pathlib import Path

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool


def run_task(task_id: str, base_dir: str = "gdpval_tasks"):
    """Run a single GDPval task using pre-downloaded files."""

    task_dir = Path(base_dir) / task_id

    if not task_dir.exists():
        print(f"❌ Task directory not found: {task_dir}")
        print("Run download_gdpval_dataset.py first to download the dataset.")
        return

    # Load task metadata
    metadata_file = task_dir / "metadata.json"
    if not metadata_file.exists():
        print(f"❌ Metadata file not found: {metadata_file}")
        return

    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    prompt = metadata["prompt"]
    print(f"Task ID: {task_id}")
    print(f"Sector: {metadata.get('sector', 'N/A')}")
    print(f"Occupation: {metadata.get('occupation', 'N/A')}")

    # List downloaded files
    downloaded_files = []
    for filepath in task_dir.iterdir():
        if filepath.name not in ["metadata.json", "download_errors.txt"]:
            downloaded_files.append(filepath.name)

    print(f"Reference files: {', '.join(downloaded_files) if downloaded_files else 'None'}")

    # Configure the LLM
    llm = LLM(
        model="openai/gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # Build the Agent
    agent = Agent(
        llm=llm,
        tools=[
            Tool(name=TerminalTool.name),
            Tool(name=FileEditorTool.name),
            Tool(name=TaskTrackerTool.name),
        ],
    )

    # Create conversation with task directory as workspace
    conversation = Conversation(agent=agent, workspace=str(task_dir))

    # Prepare the message with instructions
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

    # Send task and run
    conversation.send_message(files_info)
    conversation.run()

    print("\n✅ Task completed!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_gdpval_task.py <task_id>")
        print("\nExample: python run_gdpval_task.py 83d10b06-26d1-4636-a32c-23f92c57f30b")
        sys.exit(1)

    task_id = sys.argv[1]
    run_task(task_id)

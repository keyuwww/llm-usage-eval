import os
import json
import sys
import shutil
from pathlib import Path
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool

# Set environment variable to use BasicTerminal instead of TmuxTerminal
# This avoids tmux version compatibility issues
os.environ.setdefault("OPENHANDS_TERMINAL_TYPE", "basic")


class TeeOutput:
    """Writes to both a file and the original stream."""
    def __init__(self, file, stream):
        self.file = file
        self.stream = stream

    def write(self, data):
        self.file.write(data)
        self.stream.write(data)
        self.file.flush()
        self.stream.flush()

    def flush(self):
        self.file.flush()
        self.stream.flush()


def run_task(task_id: str, base_dir: str = "gdpval_tasks", output_dir: str = "output", model: str = "openai/gpt-4o"):
    """Run a single GDPval task using pre-downloaded files.

    Args:
        task_id: The task ID to run
        base_dir: Directory containing task data (default: gdpval_tasks)
        output_dir: Base output directory (default: output)
        model: Model to use (default: openai/gpt-4o)
               Examples: openai/gpt-4o, openai/gpt-4o-mini, anthropic/claude-3-5-sonnet-20241022
    """

    # Extract model name for directory organization (remove provider prefix)
    model_name = model.split("/")[-1] if "/" in model else model

    # Create output directory organized by model: output/{model_name}/{task_id}
    task_output_dir = Path(output_dir) / model_name / task_id
    task_output_dir.mkdir(parents=True, exist_ok=True)

    # Create log file for terminal output
    log_file = task_output_dir / f"execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Save execution metadata
    exec_metadata = {
        "task_id": task_id,
        "model": model,
        "model_name": model_name,
        "start_time": datetime.now().isoformat(),
        "status": "running",
    }

    # Open log file and redirect output
    with open(log_file, "w", buffering=1) as log:
        # Create tee outputs for stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        sys.stdout = TeeOutput(log, old_stdout)
        sys.stderr = TeeOutput(log, old_stderr)

        try:
            task_dir = Path(base_dir) / task_id
            # Convert to absolute path for OpenHands
            task_dir = task_dir.resolve()

            if not task_dir.exists():
                print(f"❌ Task directory not found: {task_dir}")
                print("Run download_gdpval_dataset.py first to download the dataset.")
                exec_metadata["status"] = "error"
                exec_metadata["error"] = "Task directory not found"
                return

            # Load task metadata
            metadata_file = task_dir / "metadata.json"
            if not metadata_file.exists():
                print(f"❌ Metadata file not found: {metadata_file}")
                exec_metadata["status"] = "error"
                exec_metadata["error"] = "Metadata file not found"
                return

            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            prompt = metadata["prompt"]
            print(f"Task ID: {task_id}")
            print(f"Sector: {metadata.get('sector', 'N/A')}")
            print(f"Occupation: {metadata.get('occupation', 'N/A')}")
            print(f"Output directory: {task_output_dir}")
            print(f"Log file: {log_file}")

            # List downloaded files
            downloaded_files = []
            for filepath in task_dir.iterdir():
                if filepath.name not in ["metadata.json", "download_errors.txt"]:
                    downloaded_files.append(filepath.name)

            print(f"Reference files: {', '.join(downloaded_files) if downloaded_files else 'None'}")
            print(f"Model: {model}")

            # Record existing files before agent runs (these are inputs)
            files_before = set(task_dir.iterdir())

            # Configure the LLM with appropriate API key
            # Determine API key based on model provider
            if "anthropic" in model.lower() or "claude" in model.lower():
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            else:
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable not set")

            llm = LLM(
                model=model,
                api_key=api_key,
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

            # Check for binary files
            binary_extensions = ('.xlsx', '.xls', '.docx', '.doc', '.pdf', '.pptx', '.ppt')
            has_binary_files = any(f.lower().endswith(binary_extensions) for f in downloaded_files)

            if has_binary_files:
                files_info += "⚠️  BINARY FILE HANDLING REQUIREMENTS:\n\n"
                files_info += "❌ DO NOT use 'python -c' with multi-line code (causes syntax errors)\n"
                files_info += "❌ DO NOT use file_editor tool on binary files (.xlsx, .docx, .pdf, etc.)\n"
                files_info += "   The file_editor can ONLY edit text files (.txt, .py, .json, .csv, etc.)\n\n"
                files_info += "✅ REQUIRED WORKFLOW for binary files:\n"
                files_info += "   Step 1: Create a Python script (.py file) using file_editor tool\n"
                files_info += "   Step 2: In the script, use appropriate libraries:\n"
                files_info += "          - Excel (.xlsx): pandas (pd.read_excel, pd.ExcelWriter)\n"
                files_info += "          - Word (.docx): python-docx library\n"
                files_info += "          - PDF (.pdf): PyPDF2 or pdfplumber\n"
                files_info += "   Step 3: Run the script with terminal tool: python your_script.py\n\n"

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

            # Identify and move output files
            print("\n📦 Separating inputs from outputs...")
            files_after = set(task_dir.iterdir())
            new_files = files_after - files_before

            # Get reference file names from metadata to be extra sure
            reference_file_names = set(metadata.get("reference_files", []))

            moved_files = []
            for filepath in new_files:
                # Skip metadata and error files
                if filepath.name in ["metadata.json", "download_errors.txt"]:
                    continue

                # This is an agent-generated output file
                try:
                    dest_path = task_output_dir / filepath.name
                    shutil.copy2(filepath, dest_path)
                    moved_files.append(filepath.name)
                    print(f"  ✓ Copied output: {filepath.name}")
                except Exception as e:
                    print(f"  ⚠️  Failed to copy {filepath.name}: {e}")

            # Save list of output files in metadata
            exec_metadata["status"] = "completed"
            exec_metadata["output_files"] = moved_files
            exec_metadata["reference_files"] = list(reference_file_names)

            if moved_files:
                print(f"\n✅ Moved {len(moved_files)} output file(s) to: {task_output_dir}")
            else:
                print(f"\n⚠️  No new output files detected (task may not have created files)")

        except Exception as e:
            print(f"\n❌ Task failed with error: {e}")
            exec_metadata["status"] = "failed"
            exec_metadata["error"] = str(e)
            exec_metadata.setdefault("output_files", [])
            exec_metadata.setdefault("reference_files", [])
            raise

        finally:
            # Restore stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Save execution metadata
            exec_metadata["end_time"] = datetime.now().isoformat()
            metadata_file = task_output_dir / "execution_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(exec_metadata, f, indent=2)

            print(f"\n📁 Output directory: {task_output_dir}")
            print(f"📄 Log file: {log_file}")
            if exec_metadata.get("output_files"):
                print(f"📝 Output files: {', '.join(exec_metadata['output_files'])}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run a single GDPval task")
    parser.add_argument("task_id", help="Task ID to run")
    parser.add_argument(
        "--model",
        default="openai/gpt-4o",
        help="Model to use (default: openai/gpt-4o). Examples: openai/gpt-4o-mini, anthropic/claude-3-5-sonnet-20241022"
    )
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

    args = parser.parse_args()
    run_task(args.task_id, args.base_dir, args.output_dir, args.model)

# LLM Usage Evaluation Framework

Evaluation framework for the GDPval dataset using the OpenHands SDK. This project allows you to evaluate multiple LLM models (GPT, Claude, etc.) on 220 real-world tasks and prepare results for submission.

## Project Structure

```
llm-usage-eval/
├── scripts/               # All executable scripts
│   ├── download_gdpval_dataset.py    # Download dataset and reference files
│   ├── run_one_task.py              # Run a single task
│   ├── run_batch_tasks.py           # Run multiple tasks with rate limiting
│   ├── find_remaining_tasks.py      # Find uncompleted tasks
│   ├── prepare_deliverables.py      # Prepare files for submission
│   ├── list_gdpval_tasks.py         # List downloaded tasks
│   ├── add_hf_columns_for_grading.py # Add columns to HuggingFace dataset
│   └── test_gdpeval.py              # Test script
├── docs/                 # Documentation
│   └── SUBMISSION_GUIDE.md          # HuggingFace submission guide
├── gdpval_tasks/         # Downloaded task data (220 tasks)
│   └── {task_id}/
│       ├── metadata.json             # Task metadata and prompt
│       └── reference_files...        # Reference files from dataset
├── output/               # Evaluation results by model
│   └── {model_name}/
│       └── {task_id}/
│           ├── execution_metadata.json  # Task execution info
│           ├── execution_*.log          # Terminal output
│           └── output_files...          # Agent-generated outputs
├── deliverable_files/    # Organized deliverables for submission
│   └── {task_id}/
│       └── output_files...
├── dataset_updates.json  # HuggingFace dataset column updates
└── remaining_tasks.txt   # List of uncompleted tasks
```

## Quick Start

### 1. Setup

```bash
# Install dependencies
uv pip install -r pyproject.toml

# Configure API keys
echo "OPENAI_API_KEY=sk-..." > .env
echo "ANTHROPIC_API_KEY=sk-..." >> .env
```

### 2. Download Dataset

```bash
python3 scripts/download_gdpval_dataset.py
```

This downloads all 220 GDPval tasks with reference files to `gdpval_tasks/`.

### 3. Run Evaluations

**Single task:**
```bash
python3 scripts/run_one_task.py <task_id> --model anthropic/claude-opus-4-5-20251101
```

**Batch processing:**
```bash
# Run all tasks with 60s delay between tasks (for rate limiting)
python3 scripts/run_batch_tasks.py --model anthropic/claude-opus-4-5-20251101 --delay 60

# Run specific tasks from a file
python3 scripts/run_batch_tasks.py --tasks-file remaining_tasks.txt --model openai/gpt-4o --delay 30
```

**Supported models:**
- `openai/gpt-4o`
- `openai/gpt-4o-mini`
- `openai/gpt-5.2`
- `anthropic/claude-opus-4-5-20251101`
- `anthropic/claude-3-5-sonnet-20241022`

### 4. Check Progress

```bash
python3 scripts/find_remaining_tasks.py --output-dir output/claude-opus-4-5-20251101

# Save remaining tasks to a file
python3 scripts/find_remaining_tasks.py --output-dir output/claude-opus-4-5-20251101 --save
```

### 5. Prepare for Submission

```bash
python3 scripts/prepare_deliverables.py --output-dir output/claude-opus-4-5-20251101
```

This creates:
- `deliverable_files/` - Output files organized by task_id
- `dataset_updates.json` - Data to add columns to HuggingFace dataset

See [docs/SUBMISSION_GUIDE.md](docs/SUBMISSION_GUIDE.md) for full submission instructions.

## How It Works

1. **Download Phase**: Downloads GDPval dataset and reference files (Excel, Word, PDF, etc.)
2. **Execution Phase**: OpenHands agent runs in isolated workspace for each task
   - Agent has access to TerminalTool, FileEditorTool, TaskTrackerTool
   - Agent receives task prompt and reference files
   - Agent generates output files or text answers
3. **Collection Phase**: Identifies and extracts output files/text
4. **Submission Phase**: Organizes deliverables for HuggingFace upload

## Evaluation Results

### Claude Opus 4.5
- Completed: 39/220 tasks
- Cost: ~$30 ($0.77/task average)
- Status: Stopped due to rate limiting and API overload

### GPT-5.2
- Completed: 42/220 tasks

## Notes

- **Rate Limiting**: Use `--delay 60` or higher for Anthropic models
- **Binary Files**: Agent automatically creates Python scripts to handle Excel/Word/PDF files
- **Output Organization**: Results are organized by model name in `output/{model_name}/`
- **Resume Capability**: Use `find_remaining_tasks.py` to continue after interruptions
- **Log Cleanup**: `prepare_deliverables.py` automatically deletes old logs and keeps newest

## Troubleshooting

**Task fails with file_text error:**
- This is a known issue but tasks still complete successfully
- Agent must provide `file_text` parameter when creating files

**Rate limit errors:**
- Increase `--delay` parameter (try 120 for Anthropic)
- Run fewer tasks at once

**Agent can't find reference files:**
- Ensure you ran `download_gdpval_dataset.py` first
- Check that files exist in `gdpval_tasks/{task_id}/`

## License

MIT

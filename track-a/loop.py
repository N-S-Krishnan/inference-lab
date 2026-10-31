import os
import json
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic


# Load environment variables from .env file
load_dotenv()

# Initialize the official client
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

MODEL = "claude-haiku-5-5"
MAX_STEPS = 10
TOKEN_BUDGET = 50000
MAX_OUTPUT = 20000

BASE_DIR = Path(__file__).parent
SCRATCH = (BASE_DIR / "scratch").resolve()
LOG_DIR = BASE_DIR / "runs"
LOG_DIR.mkdir(exist_ok=True)

ALLOWED_COMMANDS = {"python", "git"}


def safe_path(path: str):
    # Returns None if the path resolves outside the scratch folder
    target = (SCRATCH / path).resolve()
    if not target.is_relative_to(SCRATCH):
        return None
    return target


def read_file(path: str) -> str:
    target = safe_path(path)
    if target is None:
        return "Error: path is outside the scratch folder."
    if not target.is_file():
        return f"Error: no file named '{path}' in scratch."
    return target.read_text(encoding="utf-8")[:MAX_OUTPUT]


def list_dir(path: str = ".") -> str:
    target = safe_path(path)
    if target is None:
        return "Error: path is outside the scratch folder."
    if not target.is_dir():
        return f"Error: no folder named '{path}' in scratch."
    entries = sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir())
    return "\n".join(entries) or "(empty folder)"


def run_command(command: str) -> str:
    # No shell, so &&, |, and redirects do nothing here
    parts = command.split()
    if not parts:
        return "Error: empty command."
    if parts[0] not in ALLOWED_COMMANDS:
        return f"Error: '{parts[0]}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}."
    try:
        result = subprocess.run(parts, cwd=SCRATCH, capture_output=True, text=True, timeout=10)
    except FileNotFoundError:
        return f"Error: '{parts[0]}' is not installed or not on PATH."
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 10 seconds."
    return f"exit code {result.returncode}\n{(result.stdout + result.stderr)[:MAX_OUTPUT]}"


TOOLS = [
    {
        "name": "read_file",
        "description": "Read a text file in the scratch folder and return its contents.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path relative to scratch/"}},
            "required": ["path"],
        },
    },
    {
        "name": "list_dir",
        "description": "List the files and folders in a folder inside the scratch folder.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Folder path relative to scratch/, default '.'"}},
        },
    },
    {
        "name": "run_command",
        "description": "Run a command in the scratch folder. Only 'python' and 'git' are allowed.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "Command and arguments, e.g. 'python sample.py'"}},
            "required": ["command"],
        },
    },
]

TOOL_FUNCTIONS = {"read_file": read_file, "list_dir": list_dir, "run_command": run_command}


def run_tool(call) -> str:
    func = TOOL_FUNCTIONS.get(call.name)
    if func is None:
        return f"Error: unknown tool '{call.name}'."
    try:
        return func(**call.input)
    except Exception as e:
        return f"Error: {call.name} failed: {e}"


def run_agent_loop(prompt: str):
    print(f"🤖 Task assigned: '{prompt}'\n")

    messages = [{"role": "user", "content": prompt}]
    log_path = LOG_DIR / f"run-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"

    total_input_tokens = 0
    total_output_tokens = 0
    stop_reason = "step_limit"

    def log_step(record: dict):
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    for step in range(1, MAX_STEPS + 1):
        print(f"--- Step {step} ---")

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system="You are a helpful coding assistant. Use the tools to inspect the scratch folder.",
            tools=TOOLS,
            messages=messages,
        )

        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens
        messages.append({"role": "assistant", "content": response.content})

        for block in response.content:
            if block.type == "text":
                print(f"Claude: {block.text}")

        tool_calls = [b for b in response.content if b.type == "tool_use"]
        results = []
        for call in tool_calls:
            print(f"🛠️ {call.name}({call.input})")
            output = run_tool(call)
            print(f"   ↳ {output[:200]}")
            results.append({"type": "tool_result", "tool_use_id": call.id, "content": output})

        log_step({
            "step": step,
            "tool_calls": [{"name": c.name, "input": c.input} for c in tool_calls],
            "tool_results": [r["content"][:500] for r in results],
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        })

        if not tool_calls:
            stop_reason = "done"
            break

        # Stop before sending another request once the budget is spent
        if total_input_tokens + total_output_tokens >= TOKEN_BUDGET:
            stop_reason = "token_budget"
            print("Stopped: hit the token budget")
            break

        messages.append({"role": "user", "content": results})

    else:
        print("Stopped: hit the step limit")

    log_step({"stop_reason": stop_reason})

    print("\n" + "="*30)
    print("📊 USAGE")
    print(f"   Input Tokens:  {total_input_tokens}")
    print(f"   Output Tokens: {total_output_tokens}")
    print(f"   Log: {log_path}")
    print("="*30)

if __name__ == "__main__":
    user_prompt = "List the files in your scratch folder, read notes.txt, and tell me in one sentence what it says."
    run_agent_loop(user_prompt)

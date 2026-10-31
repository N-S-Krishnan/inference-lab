# Lab notebook: Track A

Format for every experiment: hypothesis BEFORE running, result AFTER.

## 2026-10-30 -> 2026-10-31
### Reading
- Building effective agents:
    - Prompt Chaining: decomposes a task into a sequence of steps, where each LLM call processes the output of the previous one
    - Routing: Classify input, send to specialized follow up output task.
    - Parallelization: LLMs can sometimes work on the same task simultaneously, having outputs aggregated programmatically. This workflow manifests in 2 key variations
    - Orchestrator-workers: In the orchestrator-workers workflow, a central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results. 
    - Evaluator-optimizer: One LLM generates a response, another provides feedback and evaluation in loop. 
- How to Build an Agent:
    - Agents can be as lightweight as ~400 lines of code
    - A simple definition: an LLM with a system prompt, a set of tools, and a set of permissions to interact with a remote local environment
    - **The exec loop**- Receive input, prompt model, detect `tool_use` request, execute tool function, feeding back into convo context
    - Agents can make their own decisions about when to use the tools you assign to them
    - The loop is the straightforward part. The variation lies in model quality, context handling, ui/ux, and the agent's integration into the SDLC

### Experiment: Loop v1
- Hypothesis: Bad loop exit conditions will cause the agent to retry tool usage and hit spend limit
- Result: Not reproduced. Four runs on the scratch task (`runs/`):
    - Worked: the model called `list_dir` then `read_file`, read `notes.txt`, and gave a correct summary in 2 steps (about 1,500 input and 200 output tokens). Ended with `stop_reason: done`.
    - Worked: the token budget stopped a run after step 1 when the budget was lowered to 500 in memory. The log ends with `stop_reason: token_budget`.
    - Worked: per-step JSONL logging, with tool calls, truncated results, and token counts.
    - Not observed: retry loops or stalls. No live run reached the step limit, and no run retried a tool after a failure.
    - Not tested live: the verification retry path. `verify_done` passed and failed correctly in isolation, but no run ended with a failed check.
- Surprises:
    - The Windows console crashed on the emoji in the first print (`cp1252` codec). Running with `PYTHONUTF8=1` fixed it.
    - The model's input tokens grow each step, because the full conversation is resent. Step 2 cost more input than step 1 in every run.
    - A tool call with no arguments arrived as `{}` rather than `{"path": "."}`. The default in `list_dir` handled it.
    - The early code I started from had bugs: `messages` was rebuilt on each call, so the model never saw tool results. It also had a non-Python condition line.

### Next session
- Hypothesis: The verification step will catch premature "done" claims on at least 3 of 5 tasks where the answer names a file that doesn't exist in scratch.
- Eval task idea: "Which function in `sample.py` multiplies two numbers, and on which line does it start?" The check compares the answer against the file with a grep, which tests whether the model reads the file instead of guessing. This needs no write tool.


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
- Result:
- Surprises:

### Next session
- Hypothesis:
- Eval task idea:


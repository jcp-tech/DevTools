# ADK Structure

## 1. Agent Types

Agents are the core building blocks of an ADK system. Use different agent types for different orchestration patterns.

### LlmAgent
- Description: Interacts with a Large Language Model (LLM). Receives user input, passes instruction + tools to the model, processes the model response.
- When to use: Any agent that needs natural language understanding, complex prompting, or tool use. The `root_agent.yaml` must be an `LlmAgent`.
- Key fields: `name`, `model` (e.g., `gemini-2.5-flash`), `instruction`, `tools`, `input_schema`, `output_schema`, `before_model_callbacks`, `after_model_callbacks`, `before_tool_callbacks`, `after_tool_callbacks`, `generate_content_config`.

### SequentialAgent
- Description: Executes `sub_agents` in a fixed linear order, passing one agent's output to the next.
- When to use: Strict step-by-step workflows (e.g., analyze → summarize → report).
- Key fields: `name`, `sub_agents`.

### ParallelAgent
- Description: Runs `sub_agents` concurrently, then aggregates results.
- When to use: Independent tasks that can run in parallel to speed up processing.
- Key fields: `name`, `sub_agents`.

### LoopAgent
- Description: Repeatedly executes `sub_agents` until a condition or `max_iterations` is reached.
- When to use: Iterative refinement or retry workflows (e.g., refine draft until criteria met).
- Key fields: `name`, `sub_agents`, `max_iterations`.

Important: Sequential/Parallel/Loop agents are orchestrators and do not include `model`, `instruction`, or `tools` fields — those belong to the `LlmAgent` sub-agents.

---

## 2. Tools

Tools extend LLM capabilities to interact with external systems, perform calculations, fetch data, or run custom logic.

### ADK Built-in Tools
Reference directly by name in an `LlmAgent`:
- Examples: `google_search`, `url_context`, `VertexAiSearchTool`, `transfer_to_agent` (injected for sub-agents), `load_memory`, `exit_loop`, `get_user_choice`.
- Usage (YAML snippet):
```yaml
tools:
    - name: google_search
    - name: url_context
```

### Custom Tools (Function Tools)
Create Python functions and reference them by fully qualified path.

Example: tools/dice_tool.py
```python
# tools/dice_tool.py
import random

def roll_dice(num_dice: int = 1, num_sides: int = 6) -> int:
        """Roll specified dice and return the total."""
        if num_dice <= 0 or num_sides <= 0:
                raise ValueError("Number of dice and sides must be positive.")
        return sum(random.randint(1, num_sides) for _ in range(num_dice))
```

Reference in `root_agent.yaml`:
```yaml
name: RootAgent
agent_class: LlmAgent
model: gemini-2.5-flash
instruction: "You are a helpful assistant. You can roll dice using the dice_tool."
tools:
    - name: pipeline_planner.tools.dice_tool.roll_dice
```

Notes:
- Tool definitions can accept parameters in YAML for simple cases, but complex configuration is best done by instantiating tool objects in Python and referencing them.

---

## 3. Callbacks

Callbacks let you inject logic at lifecycle points for logging, input/output modification, security, or error handling.

Types:
- `before_agent_callbacks` / `after_agent_callbacks` — run before/after an agent executes.
- `before_model_callbacks` / `after_model_callbacks` — run before/after an LLM call inside an `LlmAgent`.
- `before_tool_callbacks` / `after_tool_callbacks` — run before/after a tool invocation.

Usage:
- Implement Python functions with the expected signatures and reference them by fully qualified path in the agent YAML.

Example (conceptual):
```yaml
before_model_callbacks:
    - my_project.callbacks.log_input.pre_model_callback
```

---

This file outlines the core ADK concepts: agent types (including orchestrators), tools (built-in and custom), and callback extension points to build flexible, production-ready multi-agent systems.
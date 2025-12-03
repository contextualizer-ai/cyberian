# Workflow Model

This document explains how workflows execute in cyberian, including task structure, execution order, and completion detection.

## Recursive Task Structure

### The Russian Doll Model

Workflows use a **recursive task tree** structure (like Russian nesting dolls):

```yaml
workflow
└── subtasks
    ├── task1
    │   └── subtasks
    │       ├── task1a
    │       └── task1b
    ├── task2
    └── task3
        └── subtasks
            └── task3a
```

Each task can contain:

- **Instructions** - What to do (terminal node)
- **Subtasks** - More tasks (branch node)
- **Both** - Instructions + subtasks (execute instructions, then subtasks)

### Why Recursive?

**Benefits:**

1. **Hierarchical organization** - Natural project structure
2. **Reusable patterns** - Subtasks can be composed
3. **Clear execution order** - Depth-first traversal
4. **Scalable complexity** - Add depth as needed

**Example:**

```yaml
name: build-project
subtasks:
  setup:
    subtasks:
      install_deps:
        instructions: "Install dependencies"
      configure:
        instructions: "Configure project"

  build:
    subtasks:
      compile:
        instructions: "Compile code"
      test:
        instructions: "Run tests"

  deploy:
    instructions: "Deploy to production"
```

## Execution Order

### Depth-First Traversal

Tasks execute in **depth-first** order:

```
Given:
  A
  ├── B
  │   ├── D
  │   └── E
  └── C
      └── F

Execution order: A → B → D → E → C → F
```

**Algorithm:**

```python
def execute_task(task):
    # 1. Execute task instructions (if any)
    if task.instructions:
        send_to_agent(task.instructions)
        wait_for_completion()

    # 2. Execute subtasks depth-first
    if task.subtasks:
        for subtask_name, subtask in task.subtasks.items():
            execute_task(subtask)  # Recursive call
```

### Execution Example

```yaml
name: research
subtasks:
  phase1:
    instructions: "Initial research"
    subtasks:
      deep_dive:
        instructions: "Deep dive on findings"

  phase2:
    instructions: "Analysis"
```

**Execution:**

1. phase1 instructions → "Initial research"
2. phase1.deep_dive instructions → "Deep dive on findings"
3. phase2 instructions → "Analysis"

### Sequential Guarantee

Tasks **always** execute sequentially:

- Task B waits for Task A to complete
- No parallel execution within a workflow
- Deterministic ordering

For parallel execution, use [server farms](../tutorials/multi-agent-farm.md).

## Completion Detection

### The Completion Status Mechanism

cyberian needs to know when a task completes. It does this by looking for a **completion status** in the agent's response.

**Default pattern:**

```
COMPLETION_STATUS: COMPLETE
```

**How it works:**

```python
def wait_for_completion(instructions):
    send_message(instructions)

    while True:
        status = get_status()
        if status == "idle":
            messages = get_recent_messages()
            if "COMPLETION_STATUS: COMPLETE" in messages[-1].content:
                return  # Task complete
            else:
                # Agent idle but didn't signal completion
                # This shouldn't happen
                raise Error("Agent stopped without completion status")

        sleep(poll_interval)
```

### Why Explicit Completion?

**Problem:** How do we know the agent is done vs. just paused?

**Without explicit completion:**

```
Agent: "I'm analyzing the data..."
[Agent goes idle]
```

Is it done, or waiting for something?

**With explicit completion:**

```
Agent: "Analysis complete. Results in analysis.txt"
       COMPLETION_STATUS: COMPLETE
[Agent goes idle]
```

Now we know it's done!

### Instructions Must Include Completion Status

```yaml
# Bad - task will hang
subtasks:
  task:
    instructions: "Do something"

# Good - task will complete
subtasks:
  task:
    instructions: |
      Do something
      COMPLETION_STATUS: COMPLETE
```

### Custom Completion Status (Loops)

For looping tasks, use custom status:

```yaml
subtasks:
  research:
    instructions: |
      Continue researching.
      If exhausted, output: COMPLETION_STATUS: DONE
      Otherwise output: COMPLETION_STATUS: CONTINUE

    loop_until:
      status: DONE
```

## Loop Execution

### Loop Until Pattern

Tasks can loop until a condition is met:

```yaml
subtasks:
  iterate:
    instructions: |
      Perform iteration.
      If converged: COMPLETION_STATUS: CONVERGED
      Otherwise: COMPLETION_STATUS: CONTINUE

    loop_until:
      status: CONVERGED
      message: "When done, output COMPLETION_STATUS: CONVERGED"
```

### Loop Algorithm

```python
def execute_looping_task(task):
    loop_status = task.loop_until.status

    while True:
        # Execute task
        send_message(task.instructions)
        wait_for_completion()

        # Check for loop exit status
        messages = get_recent_messages()
        if f"COMPLETION_STATUS: {loop_status}" in messages[-1].content:
            break  # Exit loop

        # Otherwise continue looping
```

### Loop Limit

**No built-in loop limit** - Tasks can loop indefinitely.

**Best practice:** Agent should have logic to eventually exit:

```yaml
instructions: |
  Perform iteration {{ iteration }}.

  Keep track of iterations. After 10, output:
  COMPLETION_STATUS: MAX_ITERATIONS

  If converged, output:
  COMPLETION_STATUS: CONVERGED

  Otherwise:
  COMPLETION_STATUS: CONTINUE
```

## Template Rendering

### When Templates Render

Templates render **once** before task execution:

```yaml
params:
  name:
    range: string

subtasks:
  greet:
    instructions: "Hello {{name}}"
```

**Timeline:**

1. Load workflow YAML
2. Collect parameters
3. **Render all templates** with parameters
4. Execute tasks with rendered instructions

### Rendering Context

Available variables:

```python
context = {
    # User-provided parameters
    **workflow_params,

    # Built-in variables
    "agent_type": args.agent_type,
    "skip_permissions": args.skip_permissions,
}
```

### Template Scope

Each task instruction is rendered **independently**:

```yaml
subtasks:
  task1:
    instructions: "Process {{input}}"  # Renders once

  task2:
    instructions: "Analyze {{input}}"  # Renders once (same context)
```

**No data flow between tasks** through templates. Tasks communicate via files:

```yaml
subtasks:
  producer:
    instructions: |
      Create data.
      Write to output.json
      COMPLETION_STATUS: COMPLETE

  consumer:
    instructions: |
      Read output.json
      Process data
      COMPLETION_STATUS: COMPLETE
```

## Success Criteria

### Validation After Execution

Success criteria run **after** a task completes:

```yaml
subtasks:
  generate:
    instructions: "Create output.txt. COMPLETION_STATUS: COMPLETE"

    success_criteria:
      python: |
        import os
        result = os.path.exists("output.txt")
      max_retries: 2
```

**Flow:**

```
1. Execute task instructions
2. Wait for COMPLETION_STATUS: COMPLETE
3. Run success_criteria Python code
4. If result == True: continue
5. If result == False: retry (up to max_retries)
6. If max retries exceeded: fail
```

### Success Criteria Execution

Success criteria runs in the **same working directory** as the task:

```python
# Change to working directory
os.chdir(working_dir)

# Execute user's Python code
exec(success_criteria.python)

# Check 'result' variable
if result:
    return True  # Success
else:
    return False  # Retry or fail
```

### Retry Logic

```python
max_retries = success_criteria.max_retries
attempts = 0

while attempts <= max_retries:
    execute_task(task)
    if check_success_criteria(task.success_criteria):
        return  # Success!
    attempts += 1

raise Error("Task failed after max retries")
```

## Provider Calls

### Alternative to Agent Instructions

Instead of sending instructions to an agent, call an external provider:

```yaml
subtasks:
  research:
    provider_call:
      provider: deep-research-client
      method: research
      params:
        query: "{{topic}}"
      output_file: "research.md"
```

### Provider Execution

```python
def execute_provider_call(provider_call):
    # 1. Resolve provider
    provider = get_provider(provider_call.provider)

    # 2. Call method
    result = provider.call_method(
        provider_call.method,
        **provider_call.params
    )

    # 3. Save output
    if provider_call.output_file:
        save_to_file(result, provider_call.output_file)

    # 4. No completion status needed (deterministic)
    return
```

**Key difference:** Provider calls are **synchronous and deterministic** - no need for completion detection.

## Agent Lifecycle

### Reuse Mode (Default)

Agent server runs throughout workflow:

```
workflow start
    │
    ├── start agent server
    │
    ├── task1 (agent maintains context)
    ├── task2 (agent remembers task1)
    ├── task3 (agent remembers task1, task2)
    │
    └── workflow end (server keeps running)
```

**Benefits:**

- Agent maintains context between tasks
- Faster (no server restart overhead)
- Can reference previous work

### Refresh Mode

Agent server restarts between tasks:

```
workflow start
    │
    ├── task1
    │   ├── start server
    │   ├── execute task1
    │   └── stop server
    │
    ├── task2
    │   ├── start server (fresh)
    │   ├── execute task2
    │   └── stop server
    │
    └── workflow end
```

**Benefits:**

- Each task gets clean state
- No context pollution
- More predictable behavior

**Cost:**

- Slower (server restart overhead)
- No memory between tasks

See [Agent Lifecycle](agent-lifecycle.md) for details.

## Error Handling

### Task Failure

A task fails if:

1. **Agent error** - Agent returns error status
2. **Timeout** - Task exceeds timeout
3. **Success criteria failure** - Max retries exceeded
4. **No completion status** - Agent stops without signaling completion

### Failure Propagation

```
Task fails
    │
    ├── Workflow execution stops
    │
    ├── Error reported to user
    │
    └── Subsequent tasks don't execute
```

**No error recovery** - Workflow stops on first failure.

### Partial Completion

If a workflow fails at task 5 of 10:

- Tasks 1-4: ✓ Completed
- Task 5: ✗ Failed
- Tasks 6-10: Not executed

**Work is preserved** - Completed tasks wrote files that remain.

## Performance Characteristics

### Task Overhead

Per task:

- Template rendering: ~1-5ms
- HTTP request: ~1-10ms
- Completion polling: 0.5s * iterations

**Dominated by agent execution time** (seconds to minutes).

### Scalability

Workflow complexity has minimal overhead:

- 10 tasks vs. 100 tasks: Same per-task cost
- Deep nesting: No additional cost
- Success criteria: Only adds validation time

**Bottleneck is always agent execution.**

## Related

- [Architecture](architecture.md) - Overall system design
- [Agent Lifecycle](agent-lifecycle.md) - Server state management
- [How-To: Write Workflows](../how-to/write-workflows.md) - Practical workflow patterns
- [Reference: Workflow Schema](../reference/workflow-schema.md) - Complete YAML spec

# Agent Lifecycle

This document explains how agent servers are managed during workflow execution and the implications of different lifecycle modes.

## Server Lifecycle Basics

### What is an Agent Server?

An agent server is an **agentapi process** that:

- Listens on a port (e.g., 3284)
- Maintains conversation state
- Executes agent (Claude, Aider, etc.)
- Persists in background

### Lifecycle Phases

```
Start → Running → Stop
  │       │         │
  │       │         └─► Process terminates
  │       │             Conversation lost
  │       │
  │       └─► Accepts messages
  │           Maintains state
  │
  └─► Process spawned
      Fresh state
```

## State Management

### What is Agent State?

Agent state includes:

- **Conversation history** - All messages exchanged
- **Agent memory** - Context window contents
- **Working directory** - Files created/modified
- **Tool permissions** - Approved/denied tools

### State Persistence

**During server lifetime:**

- State persists in memory
- Conversation accumulates
- Agent "remembers" previous interactions

**After server stops:**

- Memory state lost
- Conversation history lost
- Files remain (on disk)

## Reuse Mode

### What is Reuse Mode?

**Reuse mode** (default) keeps the same agent server running throughout workflow execution.

```yaml
name: my-workflow
agent_lifecycle: reuse  # Default, can omit

subtasks:
  task1:
    instructions: "Create plan.txt. COMPLETION_STATUS: COMPLETE"

  task2:
    instructions: "Read plan.txt and implement. COMPLETION_STATUS: COMPLETE"

  task3:
    instructions: "Review your implementation. COMPLETION_STATUS: COMPLETE"
```

### Execution Flow

```
Workflow starts
    │
    ├─► Start agent server (if not running)
    │
    ├─► task1
    │   └─► Agent: "I've created plan.txt"
    │
    ├─► task2
    │   └─► Agent: "I read plan.txt and implemented X"
    │          ↑ Remembers creating plan.txt
    │
    ├─► task3
    │   └─► Agent: "My implementation looks good"
    │          ↑ Remembers both task1 and task2
    │
    └─► Workflow ends (server keeps running)
```

### Benefits

1. **Context preservation** - Agent remembers previous tasks
2. **Faster execution** - No server restart overhead
3. **Natural conversation** - Can reference earlier work
4. **Continuous state** - Build on previous results

### Example: Iterative Development

```yaml
name: iterative-dev
agent_lifecycle: reuse

subtasks:
  design:
    instructions: |
      Design a Python class for user management.
      Write design to design.md
      COMPLETION_STATUS: COMPLETE

  implement:
    instructions: |
      Read design.md and implement the class.
      Save to user_manager.py
      COMPLETION_STATUS: COMPLETE

  test:
    instructions: |
      Write tests for your user_manager.py implementation.
      Save to test_user_manager.py
      COMPLETION_STATUS: COMPLETE

  refactor:
    instructions: |
      Review the code you wrote.
      Refactor for better readability.
      COMPLETION_STATUS: COMPLETE
```

The agent maintains context through all steps, knowing what it designed, implemented, and tested.

## Refresh Mode

### What is Refresh Mode?

**Refresh mode** restarts the agent server between each task, providing clean state.

```yaml
name: my-workflow
agent_lifecycle: refresh  # Restart between tasks

subtasks:
  task1:
    instructions: "Do task 1. COMPLETION_STATUS: COMPLETE"

  task2:
    instructions: "Do task 2. COMPLETION_STATUS: COMPLETE"
```

### Execution Flow

```
Workflow starts
    │
    ├─► task1
    │   ├─► Start agent server
    │   ├─► Agent: Executes task1 (clean state)
    │   └─► Stop agent server
    │
    ├─► task2
    │   ├─► Start fresh agent server
    │   ├─► Agent: Executes task2 (no memory of task1)
    │   └─► Stop agent server
    │
    └─► Workflow ends
```

### Benefits

1. **Clean state** - No context pollution
2. **Predictable behavior** - Each task isolated
3. **Fresh context** - Agent starts from scratch
4. **Independent tasks** - Can run in any order

### Example: Independent Analysis

```yaml
name: independent-analysis
agent_lifecycle: refresh

params:
  data_file:
    range: string
    required: true

subtasks:
  statistical_analysis:
    instructions: |
      Read {{data_file}}
      Perform statistical analysis
      Write results to stats.md
      COMPLETION_STATUS: COMPLETE

  visualization_analysis:
    instructions: |
      Read {{data_file}}
      Create visualizations
      Write code to visualize.py
      COMPLETION_STATUS: COMPLETE

  summary:
    instructions: |
      Read {{data_file}}
      Write executive summary to summary.md
      COMPLETION_STATUS: COMPLETE
```

Each task gets fresh agent with no bias from previous tasks.

## Choosing a Mode

### Use Reuse Mode When:

- **Tasks build on each other** - Later tasks reference earlier work
- **Iterative workflows** - Progressive refinement
- **Speed matters** - Avoid restart overhead
- **Continuous context helpful** - Agent knowledge accumulates

**Examples:**

- Software development (design → implement → test → refactor)
- Research (gather → analyze → synthesize → report)
- Content creation (outline → draft → edit → finalize)

### Use Refresh Mode When:

- **Tasks are independent** - No relationship between tasks
- **Clean state required** - Avoid context pollution
- **Testing needed** - Each task should work standalone
- **Long workflows** - Context window might overflow

**Examples:**

- Parallel analysis of multiple datasets
- Independent code reviews
- A/B testing different approaches
- Batch processing unrelated items

### Performance Trade-offs

**Reuse mode:**

```
task1: 30s
task2: 30s (no restart overhead)
task3: 30s (no restart overhead)
Total: 90s
```

**Refresh mode:**

```
task1: 30s + 5s restart
task2: 30s + 5s restart
task3: 30s + 5s restart
Total: 105s (15s overhead)
```

Restart overhead is typically **2-10 seconds** depending on agent type.

## Command-Line Override

### Override in Workflow File

```yaml
name: my-workflow
agent_lifecycle: reuse  # Default for this workflow
```

### Override from Command Line

```bash
# Override to refresh
cyberian run my-workflow.yaml --agent-lifecycle refresh

# Override to reuse
cyberian run my-workflow.yaml --agent-lifecycle reuse
```

Command-line flag **takes precedence** over workflow file.

## Context Window Considerations

### Context Window Overflow

Agents have limited context windows:

- Claude 3.5 Sonnet: 200k tokens (~600 pages)
- Context fills with conversation history
- Eventually, earliest messages dropped

### Symptoms of Overflow

```
Agent: "I don't recall creating plan.txt"
       ↑ Too much history, early messages dropped
```

### Mitigation Strategies

1. **Use refresh mode** for long workflows
2. **Break into smaller workflows**
3. **Save intermediate results to files**
4. **Restart agent manually** between major phases

## State Isolation Patterns

### File-Based Communication

Even in refresh mode, tasks communicate via files:

```yaml
agent_lifecycle: refresh

subtasks:
  producer:
    instructions: |
      Generate data.
      Write to data.json
      COMPLETION_STATUS: COMPLETE

  consumer:
    instructions: |
      Read data.json  # File persists even with refresh
      Process data.
      COMPLETION_STATUS: COMPLETE
```

### Stateless Task Design

Design tasks to be **self-contained**:

```yaml
# Bad - relies on agent memory
subtasks:
  task1:
    instructions: "Remember this: X=42"
  task2:
    instructions: "What is X?"  # Fails in refresh mode

# Good - uses files
subtasks:
  task1:
    instructions: "Write X=42 to state.txt. COMPLETION_STATUS: COMPLETE"
  task2:
    instructions: "Read state.txt and use X. COMPLETION_STATUS: COMPLETE"
```

## Manual Server Management

### Starting Server Manually

```bash
# Start server before workflow
cyberian server start claude --port 3284 --skip-permissions

# Run workflow (uses existing server)
cyberian run workflow.yaml
```

Workflow will:

- Detect server is running
- Reuse it (regardless of agent_lifecycle setting)
- Not stop it when done

### Restarting for Fresh State

```bash
# Stop existing server
cyberian stop --port 3284

# Start fresh
cyberian server start claude --port 3284 --skip-permissions

# Run workflow with clean slate
cyberian run workflow.yaml
```

## Multi-Workflow Sessions

### Sequential Workflows (Shared State)

```bash
# Start server
cyberian server start claude --skip-permissions

# Run workflows sequentially, sharing agent state
cyberian run phase1.yaml
cyberian run phase2.yaml  # Remembers phase1
cyberian run phase3.yaml  # Remembers phase1 and phase2

# Cleanup
cyberian stop --port 3284
```

### Independent Workflows (Isolated State)

```bash
# Each workflow gets fresh state
cyberian run workflow1.yaml --agent-lifecycle refresh
cyberian run workflow2.yaml --agent-lifecycle refresh
cyberian run workflow3.yaml --agent-lifecycle refresh
```

Or use different ports:

```bash
cyberian run workflow1.yaml --port 3000 &
cyberian run workflow2.yaml --port 3001 &
cyberian run workflow3.yaml --port 3002 &
wait
```

## Best Practices

### Default to Reuse

Start with `reuse` mode (default):

- Simpler
- Faster
- More natural agent behavior

### Switch to Refresh When Needed

Use `refresh` when you observe:

- Context pollution
- Agent confusion
- Need for independence
- Very long workflows

### Document Your Choice

```yaml
name: my-workflow
description: Uses refresh mode for independent analysis
agent_lifecycle: refresh  # Clear intent
```

### Test Both Modes

For critical workflows, test with both modes:

```bash
# Test with reuse
cyberian run workflow.yaml --agent-lifecycle reuse

# Test with refresh
cyberian run workflow.yaml --agent-lifecycle refresh
```

Ensure workflow works correctly in both modes.

## Related

- [Architecture](architecture.md) - Server management details
- [Workflow Model](workflow-model.md) - Task execution flow
- [How-To: Write Workflows](../how-to/write-workflows.md) - Practical examples
- [Tutorial: Multi-Agent Farm](../tutorials/multi-agent-farm.md) - Multiple servers

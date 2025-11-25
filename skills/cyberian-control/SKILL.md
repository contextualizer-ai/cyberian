---
name: cyberian-control
description: Control and coordinate multiple Claude Code sessions via cyberian's agentapi wrapper. Use this proactively when tasks involve multi-agent orchestration, delegating work to other agents, or managing agent farms.
---

# Cyberian Control

## Overview

This skill enables a Claude Code session to control and coordinate other Claude Code (or other AI agent) sessions via the `cyberian` CLI tool, which wraps [agentapi](https://github.com/coder/agentapi).

**Use Cases:**
- Orchestrating multiple agents working on different aspects of a problem
- Delegating specialized tasks to dedicated agent instances
- Managing farms of agents for parallel processing
- Running complex multi-step workflows across multiple agents
- Monitoring and retrieving results from remote agent sessions

## When to Use This Skill

This skill should be invoked when:
- The user asks to control multiple Claude Code sessions
- Tasks involve delegating work to other agents
- You need to send messages to or monitor remote agents
- Managing agent server farms or workflows
- Coordinating parallel agent work

## Installation

The `cyberian` CLI must be installed and available:

```bash
# Install from PyPI
pip install cyberian

# Or use uvx for one-off commands
uvx cyberian --help

# For workflow/provider features
pip install cyberian[providers]
```

## Core Commands

### Sending Messages to Agents

Send a message to a remote agent and optionally wait for response:

```bash
# Fire-and-forget message
cyberian message "Write a hello world function in Python" -H localhost -P 3284

# Synchronous - wait for agent to complete
cyberian message "What is 2+2?" --sync -H localhost -P 3285

# With timeout
cyberian message "Complex task here" --sync --timeout 300 -H localhost -P 3286
```

**Options:**
- `--host`, `-H` - Agent API host (default: localhost)
- `--port`, `-P` - Agent API port (default: 3284)
- `--sync`, `-s` - Wait for agent response
- `--timeout`, `-T` - Timeout in seconds for sync mode (default: 60)
- `--type`, `-t` - Message type (default: "user")

### Checking Agent Status

Check if an agent is running and get its status:

```bash
cyberian status -H localhost -P 3284
```

### Retrieving Messages

Get conversation history from an agent:

```bash
# Get all messages as JSON
cyberian messages -H localhost -P 3284

# Get last 5 messages in YAML
cyberian messages -f yaml -l 5 -H localhost -P 3285

# Export to CSV
cyberian messages -f csv -H localhost -P 3286 > conversation.csv
```

**Options:**
- `--format`, `-f` - Output format: json, yaml, or csv
- `--last`, `-l` - Get only last N messages

### Managing Servers

Start a new agent server:

```bash
# Start Claude agent on port 3284
cyberian server claude -p 3284 -d /tmp/workdir --skip-permissions

# Start aider agent
cyberian server aider -p 3285 -d /path/to/project
```

**Options:**
- `agent` - Agent type (aider, claude, cursor, goose, custom)
- `--port`, `-p` - Port number (default: 3284)
- `--dir`, `-d` - Working directory
- `--skip-permissions`, `-s` - Skip permission checks

List running servers:

```bash
cyberian list-servers
```

Stop a server:

```bash
# By PID
cyberian stop 12345

# By port
cyberian stop -p 3284
```

### Managing Agent Farms

Start multiple agents from a config file:

```yaml
# farm.yaml
base_port: 4000
servers:
  - name: researcher
    agent_type: claude
    directory: /tmp/researcher
    skip_permissions: true
    template_directory: .config  # Copy config to each server

  - name: coder
    agent_type: claude
    directory: /tmp/coder
    port: 5000
    skip_permissions: true
```

```bash
cyberian farm start farm.yaml
```

**Farm Features:**
- Auto-assign ports starting from `base_port`
- Copy template directories (like `.claude/CLAUDE.md`) to each server
- Manage multiple specialized agents

### Running Workflows

Execute complex multi-step workflows defined in YAML:

```bash
# Basic workflow
cyberian run workflow.yaml -p query="quantum computing" -d ./output

# With specific agent type
cyberian run workflow.yaml -a claude -p topic="AI safety"

# With timeout and custom server
cyberian run workflow.yaml -H example.com -P 8080 -T 600
```

**Workflow Options:**
- `--param`, `-p` - Pass parameters (key=value)
- `--dir`, `-d` - Working directory
- `--agent-type`, `-a` - Agent type to use
- `--timeout`, `-T` - Timeout per task (default: 300s)
- `--agent-lifecycle` - `reuse` (keep server) or `refresh` (restart between tasks)

## Workflow System

### Basic Workflow Structure

```yaml
name: simple-task
description: A simple research task

params:
  query:
    range: string
    required: true

subtasks:
  research:
    instructions: |
      Research {{query}} and write a summary.
      COMPLETION_STATUS: COMPLETE
```

### Workflow with Subtasks

```yaml
name: complex-workflow
description: Multi-step research

params:
  query:
    range: string
    required: true

subtasks:
  initial_search:
    instructions: |
      Perform initial research on {{query}}.
      Write a research plan in PLAN.md.
      COMPLETION_STATUS: COMPLETE

  deep_dive:
    instructions: |
      Read PLAN.md and do deep dive into {{query}}.
      Write detailed findings in FINDINGS.md.
      COMPLETION_STATUS: COMPLETE

  summary:
    instructions: |
      Read FINDINGS.md and create final summary in SUMMARY.md.
      COMPLETION_STATUS: COMPLETE
```

### Looping Tasks

Tasks can loop until a condition is met:

```yaml
subtasks:
  iterate:
    instructions: |
      Keep researching {{query}}. Find new angles.
      When exhausted, yield: NO_MORE_RESEARCH

    loop_until:
      status: NO_MORE_RESEARCH
      message: |
        If all research avenues are exhausted,
        yield status: NO_MORE_RESEARCH
```

### Provider Calls

Call external providers directly (requires `pip install cyberian[providers]`):

```yaml
subtasks:
  research:
    provider_call:
      provider: deep-research-client
      method: research
      params:
        query: "{{query}}"
        provider: openai
        model: o3-mini
        use_cache: true
      output_file: "{{workdir}}/research.md"

  analyze:
    instructions: |
      Read {{workdir}}/research.md and create analysis.
      COMPLETION_STATUS: COMPLETE
```

## Common Patterns

### Pattern 1: Delegate Task to Remote Agent

```bash
# Start a remote agent for specialized work
cyberian server claude -p 4000 -d /tmp/specialist

# Send it a task
cyberian message "Implement a binary search tree in Rust" \
  --sync -P 4000 --timeout 300

# Get the results
cyberian messages -f yaml -l 10 -P 4000
```

### Pattern 2: Parallel Research with Farm

```yaml
# research-farm.yaml
base_port: 5000
servers:
  - name: quantum
    agent_type: claude
    directory: /tmp/quantum-research
    skip_permissions: true

  - name: classical
    agent_type: claude
    directory: /tmp/classical-research
    skip_permissions: true
```

```bash
# Start farm
cyberian farm start research-farm.yaml

# Send different tasks to each
cyberian message "Research quantum algorithms" -P 5000 &
cyberian message "Research classical algorithms" -P 5001 &

# Monitor status
cyberian status -P 5000
cyberian status -P 5001
```

### Pattern 3: Multi-Step Workflow

```yaml
# deep-research.yaml
name: deep-research
description: Comprehensive research workflow

params:
  query:
    range: string
    required: true

subtasks:
  initial:
    instructions: |
      Research {{query}}. Write initial findings.
      COMPLETION_STATUS: COMPLETE

  expand:
    instructions: |
      Read initial findings. Research deeper.
      COMPLETION_STATUS: COMPLETE

  synthesize:
    instructions: |
      Create final comprehensive report.
      COMPLETION_STATUS: COMPLETE
```

```bash
cyberian run deep-research.yaml \
  -p query="CRISPR applications" \
  -d ./research-output \
  -a claude
```

### Pattern 4: Hybrid Provider + Agent

```yaml
# hybrid-workflow.yaml
name: hybrid-research
description: Use provider for data, agent for synthesis

params:
  query:
    range: string
    required: true

subtasks:
  gather:
    provider_call:
      provider: deep-research-client
      method: research
      params:
        query: "{{query}}"
      output_file: "raw_data.md"

  analyze:
    instructions: |
      Read raw_data.md and create structured report.
      COMPLETION_STATUS: COMPLETE
```

## Best Practices

1. **Always specify ports** when working with multiple agents to avoid conflicts
2. **Use --sync mode** when you need to wait for agent completion
3. **Set appropriate timeouts** for complex tasks (use `-T` flag)
4. **Use farm template_directory** to share configuration across agents
5. **Monitor agent status** before sending new messages
6. **Retrieve conversation history** to check agent progress
7. **Use workflows** for complex multi-step tasks
8. **Use provider calls** for deterministic operations (research, data retrieval)
9. **Use agent_lifecycle: refresh** when tasks need isolated state

## Troubleshooting

### Check if Agent is Running

```bash
cyberian status -P 3284
cyberian list-servers
```

### Agent Not Responding

```bash
# Check status
cyberian status -P 3284

# Restart server
cyberian stop -p 3284
cyberian server claude -p 3284 -d /tmp/workdir
```

### View Agent Conversation

```bash
# See what the agent is doing
cyberian messages -f yaml -l 20 -P 3284
```

### Workflow Not Completing

Ensure tasks include completion status:
```yaml
instructions: |
  Do the work here.
  COMPLETION_STATUS: COMPLETE  # Required!
```

## Examples

See the `tests/examples/` directory for workflow examples:
- `deep-research.yaml` - Iterative research workflow
- `simple-provider-research.yaml` - Basic provider call
- `deep-research-with-provider.yaml` - Hybrid workflow

## Command Reference

All commands support `--help` for detailed options:

```bash
cyberian --help
cyberian message --help
cyberian server --help
cyberian farm --help
cyberian run --help
```

## Integration with Claude Code

This skill is designed to work seamlessly within Claude Code sessions. When you invoke this skill, Claude will use `cyberian` commands via the Bash tool to control remote agents. The skill provides the knowledge and patterns for effective multi-agent orchestration.

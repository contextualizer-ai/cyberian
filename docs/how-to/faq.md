# Frequently Asked Questions

Common questions about cyberian and multi-agent workflows.

## General

### What is cyberian?

cyberian is a Python CLI wrapper for [agentapi](https://github.com/coder/agentapi) that enables interaction with AI agent APIs in pipeline workflows. It provides:

- Multi-agent orchestration
- YAML-based workflow definitions
- Server lifecycle management
- Message routing and status monitoring

### Which agents does cyberian support?

cyberian works with any agent that integrates with agentapi, including:

| Agent | Status | Notes |
|-------|--------|-------|
| Claude Code | Fully supported | Primary target |
| OpenAI Codex | Supported | Requires specific flags |
| Aider | Supported | Basic integration |
| Custom agents | Supported | Via agentapi |

### How is cyberian different from direct agentapi usage?

cyberian adds:

- **Workflow orchestration**: YAML-defined task trees with loops, conditions, and retries
- **Template rendering**: Jinja2 templates for dynamic instructions
- **Success criteria**: Python-based validation of task outputs
- **Server management**: Farm mode for multi-agent setups
- **Message routing**: Easy message sending and retrieval

## Installation

### What are the system requirements?

- Python 3.10+
- [agentapi](https://github.com/coder/agentapi) installed and in PATH
- One or more supported agents (Claude Code, Codex, etc.)

### How do I install cyberian?

```bash
# Using uv (recommended)
uv pip install cyberian

# Using pip
pip install cyberian

# From source
git clone https://github.com/monarch-initiative/cyberian
cd cyberian
uv pip install -e .
```

### Do I need to install agentapi separately?

Yes. agentapi is the underlying server that manages agent processes:

```bash
# Install agentapi
go install github.com/coder/agentapi@latest

# Verify installation
agentapi --version
```

## Agents

### Which agent should I use?

| Use Case | Recommended Agent |
|----------|-------------------|
| General coding tasks | Claude Code |
| Long-running research | Claude Code or Codex |
| Interactive development | Claude Code |
| Automated pipelines | Either (with --skip-permissions) |

### How do I switch between agents?

Specify the agent type when starting a server or running a workflow:

```bash
# Claude Code
cyberian server start claude --skip-permissions

# Codex
cyberian server start codex --skip-permissions

# Run workflow with specific agent
cyberian run workflow.yaml --agent-type codex
```

### Can I run multiple agents simultaneously?

Yes, using different ports or farm mode:

```bash
# Manual: different ports
cyberian server start claude --port 3284
cyberian server start codex --port 3285

# Farm mode: automatic port assignment
cyberian farm start farm.yaml
```

### What does `-s` / `--skip-permissions` do and should I use it?

The `-s` or `--skip-permissions` flag tells the agent to bypass interactive approval prompts. This is **required for fully automated workflows**.

**Without `-s`:**

```bash
cyberian server start claude
```

The agent starts but will pause for permission approval on potentially dangerous operations (file writes, shell commands, etc.). You'll need to approve these via the agentapi web UI at `http://localhost:3284/chat`.

**With `-s`:**

```bash
cyberian server start claude -s
# or
cyberian server start claude --skip-permissions
```

The agent runs without pausing for approval. All operations execute automatically.

**Which flag gets passed?**

| Agent | Flag Passed |
|-------|-------------|
| Claude Code | `--dangerously-skip-permissions` |
| Codex | `--dangerously-bypass-approvals-and-sandbox` |

**When to use `-s`:**

- Automated pipelines and CI/CD
- Long-running research workflows
- Batch processing
- Any workflow that should run unattended

**When NOT to use `-s`:**

- Untrusted workflows or inputs
- Production systems with sensitive data
- When you want to review agent actions

**Our recommendation:** Be explicit about permissions. If you're running automated workflows, use `-s` deliberately. If you're experimenting or don't fully trust the workflow, omit it and approve actions via the web UI.

```bash
# Explicit automation mode
cyberian server start claude -s --dir /tmp/sandbox

# Interactive mode (review via web UI)
cyberian server start claude --dir /tmp/sandbox
```

See also: [Codex Integration](../integrations/codex.md) for Codex-specific permission settings via `config.toml`.

## Workflows

### What is the workflow format?

YAML files defining task trees:

```yaml
name: my-workflow
description: Example workflow
params:
  query:
    range: string
    required: true
subtasks:
  task1:
    instructions: |
      Do something with {{query}}.
      COMPLETION_STATUS: COMPLETE
```

See [Workflow Schema Reference](../reference/workflow-schema.md) for full details.

### How do loops work?

Use `loop_until` for iterative tasks:

```yaml
subtasks:
  iterate:
    instructions: Keep researching
    loop_until:
      status: DONE
      message: "When finished, output DONE"
```

The task repeats until the agent outputs the status string.

This implements the [Ralph Wiggum Pattern](../explanation/ralph-wiggum-pattern.md) - an autonomous iteration technique popularized in 2025 where agents loop until completion with state persisted in files.

### How do success criteria work?

Python code that validates task output:

```yaml
subtasks:
  generate:
    instructions: Create output.json
    success_criteria:
      python: |
        import os
        result = os.path.exists("output.json")
      max_retries: 3
      retry_message: "File not found. Please create output.json"
```

### Can I use external scripts for validation?

Yes:

```yaml
success_criteria:
  script: validate.py
  max_retries: 2
```

The script must set `result = True` or `result = False`.

### How do I pass parameters to workflows?

```bash
cyberian run workflow.yaml \
  --param query="climate change" \
  --param depth=3
```

In the workflow, access via Jinja2:

```yaml
instructions: Research {{query}} to depth {{depth}}
```

## Server Management

### How do I start a server?

```bash
# Basic start
cyberian server start claude

# With skip-permissions (for automation)
cyberian server start claude --skip-permissions

# Specific port
cyberian server start claude --port 4000

# Specific working directory
cyberian server start claude --dir /path/to/workspace
```

### How do I stop a server?

```bash
# By port
cyberian stop --port 3284

# By PID
cyberian stop 12345

# List servers first
cyberian list-servers
```

### What does --skip-permissions do?

It passes agent-specific flags to skip interactive approval prompts:

| Agent | Flag Passed |
|-------|-------------|
| Claude Code | `--dangerously-skip-permissions` |
| Codex | `--dangerously-bypass-approvals-and-sandbox` |

**Warning**: Only use in trusted automation environments.

### How do I check server status?

```bash
# Status of default server
cyberian status

# Specific port
cyberian status --port 4000

# List all servers
cyberian list-servers
```

## Messages

### How do I send a message?

```bash
# Fire and forget (async)
cyberian message "Do something"

# Wait for response (sync)
cyberian message "Do something" --sync

# With timeout
cyberian message "Do something" --sync --timeout 120
```

### How do I view conversation history?

```bash
# All messages
cyberian messages

# Last N messages
cyberian messages --last 5

# Different formats
cyberian messages --format yaml
cyberian messages --format json
cyberian messages --format csv
```

### What message formats are supported?

- `json` (default): JSON array
- `yaml`: YAML list
- `csv`: Comma-separated values
- `text`: Plain text

## Troubleshooting

### Why does my task never complete?

The agent must output `COMPLETION_STATUS: COMPLETE`. Ensure your instructions include this marker:

```yaml
instructions: |
  Do your task.

  When done, output:
  COMPLETION_STATUS: COMPLETE
```

### Why is Codex ignoring my first message?

Codex may show a startup banner in fresh directories. Solutions:

1. **Use `--skip-permissions`** to bypass approval prompts
2. **Use a trusted directory** (not /tmp)
3. **Configure config.toml** with `approval_policy = "never"`

See [Codex Integration Guide](../integrations/codex.md) for details.

### Why do I get connection errors?

1. Check server is running: `cyberian list-servers`
2. Verify port: `cyberian status --port <port>`
3. Wait for startup: servers need a few seconds to initialize

### How do I debug workflows?

1. Add verbose instructions:
   ```yaml
   instructions: |
     Debug: listing directory
     ls -la
     COMPLETION_STATUS: COMPLETE
   ```

2. Check conversation history:
   ```bash
   cyberian messages --last 10
   ```

3. Monitor status:
   ```bash
   watch -n 2 cyberian status
   ```

See [Troubleshooting Guide](troubleshooting.md) for more solutions.

## Performance

### How can I speed up workflows?

1. **Use fire-and-forget** for independent tasks:
   ```bash
   cyberian message "Task 1" &
   cyberian message "Task 2" &
   wait
   ```

2. **Use farm mode** for parallel execution:
   ```yaml
   servers:
     - name: worker1
     - name: worker2
   ```

3. **Reduce polling interval** (advanced):
   ```bash
   cyberian run workflow.yaml --poll-interval 1.0
   ```

### How much memory do agents use?

Varies by agent and task complexity. Monitor with:

```bash
# Watch memory usage
watch -n 5 "cyberian list-servers | head -1 && ps aux | grep agentapi"
```

## Security

### Is it safe to use --skip-permissions?

Only in trusted environments where:

- The agent is running in an isolated container/VM
- The workspace contains no sensitive data
- The workflow is from a trusted source

### How do I limit agent capabilities?

1. **Use workspace isolation**:
   ```bash
   cyberian server start claude --dir /tmp/sandbox
   ```

2. **Don't use --skip-permissions** in untrusted contexts

3. **For Codex**: Configure `sandbox_mode` in config.toml:
   ```toml
   sandbox_mode = "workspace-write"  # or "read-only"
   ```

### Can agents access the internet?

Depends on agent and configuration:

- **Claude Code**: Yes, by default
- **Codex**: Configurable via `sandbox_mode`

## Integration

### Can I use cyberian with CI/CD?

Yes. Example GitHub Actions workflow:

```yaml
- name: Run cyberian workflow
  run: |
    cyberian server start claude --skip-permissions &
    sleep 5
    cyberian run workflow.yaml --param input="$INPUT"
    cyberian stop --port 3284
```

### Can I call cyberian from Python?

Not directly as a library (yet), but you can:

1. Use subprocess:
   ```python
   import subprocess
   result = subprocess.run(["cyberian", "status"], capture_output=True)
   ```

2. Use the agentapi HTTP API directly

### Does cyberian support webhooks/callbacks?

Not currently. For notifications, see [NOTIFY_FEATURE.md](https://github.com/monarch-initiative/cyberian/blob/main/NOTIFY_FEATURE.md).

## Getting Help

### Where can I report bugs?

Open an issue at [https://github.com/monarch-initiative/cyberian/issues](https://github.com/monarch-initiative/cyberian/issues)

Include:
- cyberian version (`cyberian --version`)
- Command run
- Error message
- Relevant workflow YAML

### Where can I ask questions?

- GitHub Discussions
- GitHub Issues (for bugs)

### How do I contribute?

See [Contributing Guide](../development/contributing.md).

## See Also

- [Troubleshooting](troubleshooting.md) - Detailed problem solutions
- [CLI Commands Reference](../reference/cli-commands.md) - All commands
- [Workflow Schema](../reference/workflow-schema.md) - YAML format
- [Codex Integration](../integrations/codex.md) - Codex-specific guide

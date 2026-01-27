# OpenAI Codex Integration

This guide covers using cyberian with OpenAI Codex, including configuration, troubleshooting, and best practices for automated workflows.

## Overview

[OpenAI Codex](https://openai.com/codex) is a code-focused AI agent. cyberian supports Codex with:

- Automatic permission flag mapping
- Extended startup timeouts
- Welcome banner detection and retry
- Support for Codex config.toml settings

## Quick Start

### Basic Usage

```bash
# Start Codex server
cyberian server start codex --skip-permissions

# Send a message
cyberian message "Write a Python function to calculate factorial" --sync

# Run a workflow
cyberian run workflow.yaml --agent-type codex
```

### With Workflow

```yaml
name: codex-task
description: Run task with Codex
subtasks:
  implement:
    instructions: |
      Implement a binary search function in Python.
      Include docstring and type hints.
      COMPLETION_STATUS: COMPLETE
```

```bash
cyberian run codex-task.yaml --agent-type codex --skip-permissions
```

## Configuration

### Codex config.toml

Codex reads configuration from `~/.codex/config.toml`. This file controls approval policies, sandbox settings, and more.

#### Location

```
~/.codex/config.toml
```

Create if it doesn't exist:

```bash
mkdir -p ~/.codex
touch ~/.codex/config.toml
```

#### Key Settings for Automation

For fully automated workflows, use this configuration:

```toml
# ~/.codex/config.toml

# Never pause for approval (automation mode)
approval_policy = "never"

# Full filesystem and network access
sandbox_mode = "danger-full-access"

# Enable shell tool
[features]
shell_tool = true
```

#### Approval Policy Options

| Policy | Description | Use Case |
|--------|-------------|----------|
| `never` | Never pause for approval | Automated pipelines |
| `on-request` | Pause only when requested | Interactive development |
| `on-failure` | Pause after failures | Semi-automated |
| `untrusted` | Always pause | Maximum safety |

```toml
# Most permissive (for automation)
approval_policy = "never"

# Most restrictive (for safety)
approval_policy = "untrusted"
```

#### Sandbox Mode Options

| Mode | Description | Access |
|------|-------------|--------|
| `read-only` | Read-only filesystem | Safest |
| `workspace-write` | Write only to workspace | Balanced |
| `danger-full-access` | Full access | Most permissive |

```toml
# For automation requiring file writes
sandbox_mode = "danger-full-access"

# For safer operation
sandbox_mode = "workspace-write"
```

#### Project Trust Levels

Mark specific directories as trusted:

```toml
# Trust a specific project directory
[projects."/path/to/my/project"]
trust_level = "trusted"

# Trust the workspace used by cyberian
[projects."/tmp/cyberian_research"]
trust_level = "trusted"
```

#### Profiles

Define named profiles for different use cases:

```toml
# Default profile
profile = "automation"

[profiles.automation]
approval_policy = "never"
sandbox_mode = "danger-full-access"

[profiles.interactive]
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[profiles.safe]
approval_policy = "untrusted"
sandbox_mode = "read-only"
```

Use a profile:

```bash
codex --profile safe
```

### cyberian Settings

#### Skip Permissions Flag

`--skip-permissions` maps to the correct Codex flag:

```bash
# This command:
cyberian server start codex --skip-permissions

# Executes:
agentapi server codex --port 3284 -- --dangerously-bypass-approvals-and-sandbox
```

#### Extended Timeout

Codex startup can take longer than Claude. cyberian automatically extends the readiness timeout to 120 seconds for Codex.

## Startup Behavior

### Welcome Banner

When Codex starts in a fresh directory, it may display a welcome banner:

```
Welcome to OpenAI Codex!

Available commands:
/init - Initialize project
/approvals - Configure approval settings
```

This can cause the first message to be "swallowed". cyberian handles this by:

1. Detecting the welcome banner pattern
2. Automatically resending the first message

### Trusted vs Untrusted Directories

Codex treats directories differently based on trust:

| Directory Type | Behavior |
|---------------|----------|
| Trusted (configured) | Normal operation |
| Untrusted (new/temp) | May show banner, require approval |

**Recommendation**: For automated workflows, either:

1. Use `approval_policy = "never"` in config.toml
2. Mark your workspace as trusted
3. Use `--skip-permissions` flag

## Workflow Best Practices

### Use workdir_base for Trusted Paths

Instead of letting cyberian create workspaces in `/tmp`:

```bash
# May trigger untrusted directory behavior
cyberian run workflow.yaml --dir /tmp/random

# Better: use a pre-configured trusted path
cyberian run workflow.yaml --dir ~/projects/cyberian-workspace
```

### Configure Trust Level

```toml
# In ~/.codex/config.toml
[projects."~/projects/cyberian-workspace"]
trust_level = "trusted"
```

### Handle Long Tasks

Codex may need more time. Increase timeouts:

```bash
cyberian run workflow.yaml --timeout 600  # 10 minutes per task
```

### Example: Deep Research with Codex

```yaml
name: codex-research
description: Research workflow optimized for Codex
requires_workdir: true
params:
  query:
    range: string
    required: true
subtasks:
  research:
    instructions: |
      Research {{query}} thoroughly.

      1. Search for relevant papers
      2. Summarize key findings
      3. Write a report to REPORT.md

      COMPLETION_STATUS: COMPLETE
    success_criteria:
      python: |
        import os
        result = os.path.exists("REPORT.md")
      max_retries: 2
```

```bash
# Run with Codex
cyberian run codex-research.yaml \
  --agent-type codex \
  --skip-permissions \
  --param query="transformer architectures" \
  --dir ~/research/transformers
```

## Troubleshooting

### First Message Ignored

**Symptoms**: Task doesn't execute, only welcome banner appears.

**Solutions**:

1. Use `--skip-permissions`:
   ```bash
   cyberian server start codex --skip-permissions
   ```

2. Set `approval_policy = "never"` in config.toml

3. Mark directory as trusted:
   ```toml
   [projects."/your/workspace"]
   trust_level = "trusted"
   ```

### Server Timeout on Startup

**Symptoms**: "Server did not become ready within 30s"

**Cause**: Codex takes longer to start than the default timeout.

**Solution**: cyberian automatically extends to 120s for Codex. If still failing:

1. Check Codex is installed correctly
2. Check agentapi logs:
   ```bash
   cat /path/to/workspace/agentapi_stderr.log
   ```

3. Try starting manually:
   ```bash
   agentapi server codex --port 3284
   ```

### Environment Mismatch

**Symptoms**: Codex works in terminal but not when spawned by cyberian.

**Cause**: Different PATH or environment when spawned as subprocess.

**Solutions**:

1. Check PATH includes codex:
   ```bash
   which codex
   ```

2. Use absolute path in config.toml:
   ```toml
   # If codex is installed in a specific location
   # Configure shell environment
   [shell_environment_policy]
   inherit = "all"
   ```

3. Check agentapi logs for errors

### Permission Prompts

**Symptoms**: Workflow hangs waiting for input.

**Cause**: Codex waiting for approval.

**Solutions**:

1. Use `--skip-permissions` flag
2. Set `approval_policy = "never"` in config.toml
3. Use `sandbox_mode = "danger-full-access"` for full access

### Sandbox Restrictions

**Symptoms**: "Permission denied" or file operation failures.

**Cause**: Sandbox mode restricting access.

**Solutions**:

1. Use more permissive sandbox:
   ```toml
   sandbox_mode = "danger-full-access"
   ```

2. Or allow specific paths:
   ```toml
   [sandbox_workspace_write]
   writable_roots = ["/tmp/cyberian", "~/projects"]
   ```

## Configuration Reference

### Full Automation Config

```toml
# ~/.codex/config.toml for fully automated cyberian workflows

# Never pause for approval
approval_policy = "never"

# Full access
sandbox_mode = "danger-full-access"

# Default model
model = "gpt-4-turbo"

# Enable features
[features]
shell_tool = true
web_search_request = true

# Trust cyberian workspaces
[projects."/tmp/cyberian"]
trust_level = "trusted"

# Shell environment
[shell_environment_policy]
inherit = "all"
```

### Safe Development Config

```toml
# ~/.codex/config.toml for safer interactive use

# Pause on request
approval_policy = "on-request"

# Workspace write only
sandbox_mode = "workspace-write"

# Model
model = "gpt-4-turbo"

# Limited features
[features]
shell_tool = true
web_search_request = false
```

### Profile-Based Config

```toml
# ~/.codex/config.toml with multiple profiles

# Default to safe mode
profile = "safe"

[profiles.safe]
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[profiles.automation]
approval_policy = "never"
sandbox_mode = "danger-full-access"

[profiles.research]
approval_policy = "never"
sandbox_mode = "workspace-write"

[features]
shell_tool = true
web_search_request = true
```

Use profiles:

```bash
# Safe mode (default)
codex

# Automation mode
codex --profile automation

# Or set environment
export CODEX_PROFILE=automation
```

## Comparison: Claude vs Codex

| Feature | Claude Code | Codex |
|---------|-------------|-------|
| Skip permissions flag | `--dangerously-skip-permissions` | `--dangerously-bypass-approvals-and-sandbox` |
| Config location | `~/.claude/settings.json` | `~/.codex/config.toml` |
| Startup time | Fast (~5s) | Slower (~15-30s) |
| Welcome banner | No | Yes (in untrusted dirs) |
| First message retry | Not needed | Automatic in cyberian |
| Server readiness timeout | 30s | 120s (extended) |

## See Also

- [FAQ](../how-to/faq.md) - Common questions
- [Troubleshooting](../how-to/troubleshooting.md) - General troubleshooting
- [Manage Servers](../how-to/manage-servers.md) - Server lifecycle
- [Workflow Schema](../reference/workflow-schema.md) - YAML format
- [Codex Configuration Reference](https://developers.openai.com/codex/config-reference/) - Official docs

# cyberian

[![PyPI](https://img.shields.io/pypi/v/cyberian.svg)](https://pypi.org/project/cyberian/) [![Python](https://img.shields.io/pypi/pyversions/cyberian.svg)](https://pypi.org/project/cyberian/) [![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause) [![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://monarch-initiative.github.io/cyberian) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

A Python CLI wrapper for [agentapi](https://github.com/coder/agentapi) that enables automated agent pipelines and workflows.

## Overview

`cyberian` provides a comprehensive command-line interface for:

- **Sending messages** to AI agents via agentapi
- **Managing agentapi servers** (start, stop, list)
- **Running server farms** - managing multiple agent servers simultaneously
- **Running complex workflows** from YAML definitions with recursive task trees
- **Template-based instructions** using Jinja2 for dynamic workflows

## Installation

### Prerequisites

cyberian requires [`agentapi`](https://github.com/coder/agentapi) to be installed and available on your PATH. See the [agentapi installation guide](https://github.com/coder/agentapi#installation) for instructions.

### Install cyberian

```bash
pip install cyberian
```

Or you can bypass installation using `uvx`:

`uvx cyberian`

### Claude Code Skill

A Claude Code skill is available for multi-agent orchestration. See [cyberian-control/README.md](cyberian-control/README.md) for details.

To install the skill in Claude Code:
```
/plugin marketplace add cyberian-skills
```

## Quick Start

```bash
# Start an agentapi server
cyberian server start claude --skip-permissions --port 3284 --dir /tmp/workdir

# Send a message
cyberian message "Write a hello world function in Python"

# check status
cyberian status

# get messages
cyberian messages

# view in chat interface
open http://localhost:3284/chat
```

    
# Start a farm of multiple servers

```
cyberian farm start my-farm.yaml
```

# Run a workflow

```
cyberian run deep-research.yaml --param query="Function of human CFAP300 gene"
```

## Commands

### Quick Reference: Common Shorthands

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--host` | `-H` | Agent API host |
| `--port` | `-P` or `-p` | Port (use `-p` for server/stop, `-P` elsewhere) |
| `--type` | `-t` | Message type |
| `--sync` | `-s` | Synchronous mode (message) |
| `--timeout` | `-T` | Timeout in seconds |
| `--format` | `-f` | Output format (json/yaml/csv) |
| `--last` | `-l` | Get last N messages |
| `--dir` | `-d` | Working directory |
| `--agent-type` | `-a` | Agent type for workflows |
| `--skip-permissions` | `-s` | Skip permission checks |
| `--param` | `-p` | Workflow parameter |

### message - Send messages to agent

Send messages to a running agentapi server. Supports both fire-and-forget and synchronous modes.

```bash
# Basic message
cyberian message "Your prompt here"

# Synchronous mode - wait for response
cyberian message "What is 2+2?" -s
```

**Options:**
- `content` - Message content (required, positional argument)
- `--type`, `-t` - Message type (default: "user")
- `--host`, `-H` - Agent API host (default: "localhost")
- `--port`, `-P` - Agent API port (default: 3284)
- `--sync`, `-s` - Wait for agent response and return last agent message
- `--timeout`, `-T` - Timeout in seconds when using --sync (default: 60)
- `--poll-interval` - Status polling interval in seconds (default: 0.5)

### messages - Retrieve conversation history

Get messages from the agent conversation history with multiple output formats.

```bash
# Get all messages as JSON (default)
cyberian messages

# Get last 5 messages in YAML format
cyberian messages -f yaml -l 5

# Export to CSV
cyberian messages -f csv > conversation.csv

# Custom server
cyberian messages -H example.com -P 8080
```

**Options:**
- `--host`, `-H` - Agent API host (default: "localhost")
- `--port`, `-P` - Agent API port (default: 3284)
- `--format`, `-f` - Output format: json, yaml, or csv (default: "json")
- `--last`, `-l` - Get only the last N messages

### status - Check agent status

Check if the agentapi server is running and get its status.

```bash
# Check default server
cyberian status

# Check custom server
cyberian status -H example.com -P 8080
```

**Options:**
- `--host`, `-H` - Agent API host (default: "localhost")
- `--port`, `-P` - Agent API port (default: 3284)

### server - Start agentapi server

Start an agentapi server with the specified agent type.

```bash
# Start default custom agent
cyberian server

# Start Claude agent on port 8080 (using shorthand)
cyberian server claude -p 8080

# Start in specific directory
cyberian server aider -d /path/to/project

# Skip permissions and set directory
cyberian server claude -d /my/project -s

# With CORS settings
cyberian server claude --allowed-origins "https://example.com" --allowed-hosts "example.com"
```

**Options:**
- `agent` - Agent type (e.g., aider, claude, cursor, goose) (default: "custom")
- `--port`, `-p` - Port to run the server on (default: 3284)
- `--dir`, `-d` - Directory to change to before starting the server
- `--skip-permissions`, `-s` - Skip permission checks (translates to agent-specific flags)
- `--allowed-hosts` - HTTP allowed hosts (comma-separated)
- `--allowed-origins` - HTTP allowed origins (comma-separated)

### farm - Manage multiple servers

Start and manage a farm of multiple agentapi servers from a single YAML configuration file.

#### farm start - Start a farm of servers

```bash
# Start a farm from config file
cyberian farm start my-farm.yaml

# Example farm configuration
cat > farm.yaml << 'EOF'
base_port: 4000
servers:
  - name: worker1
    agent_type: claude
    directory: /tmp/worker1
    skip_permissions: true
    template_directory: .config  # Copy config files to each server

  - name: worker2
    agent_type: claude
    directory: /tmp/worker2
    port: 5000  # Explicit port
    skip_permissions: true
EOF

cyberian farm start farm.yaml
```

**Farm Configuration Options:**

- `base_port` - Base port for auto-assignment (default: 3284)
  - First server gets this port, second gets base_port+1, etc.
  - Explicit `port` in server config overrides auto-assignment
- `servers` - List of server configurations

**Server Configuration Options:**

- `name` - **Required**. Logical name for the server
- `agent_type` - Agent type (e.g., aider, claude, cursor, goose) (default: "custom")
- `directory` - **Required**. Working directory for the server
- `port` - Optional explicit port (overrides auto-assignment)
- `skip_permissions` - Skip permission checks (default: false)
- `allowed_hosts` - HTTP allowed hosts (comma-separated)
- `allowed_origins` - HTTP allowed origins (comma-separated)
- `template_directory` - Optional directory to copy to working directory (see below)

**Template Directory Feature:**

The `template_directory` parameter copies configuration files to each server's working directory:

```yaml
servers:
  - name: worker1
    directory: /tmp/worker1
    template_directory: farm-template  # Relative to farm.yaml
```

This will recursively copy all contents from `farm-template/` (including hidden files and directories starting with `.`) to `/tmp/worker1/`. This is useful for:

- Copying `.claude/CLAUDE.md` configuration files
- Distributing shared project settings
- Setting up consistent environments across multiple servers

**Example with Template:**

```bash
# Create a template directory
mkdir -p farm-template/.claude
cat > farm-template/.claude/CLAUDE.md << 'EOF'
# Project Instructions
- Use test-driven development
- Follow PEP 8 style guidelines
EOF

# Create farm config using the template
cat > farm.yaml << 'EOF'
base_port: 4000
servers:
  - name: worker1
    agent_type: claude
    directory: /tmp/worker1
    template_directory: farm-template
  - name: worker2
    agent_type: claude
    directory: /tmp/worker2
    template_directory: farm-template
EOF

# Start the farm (both servers get the .claude config)
cyberian farm start farm.yaml
```

### list-servers - Find running servers

List all running agentapi server processes.

```bash
cyberian list-servers
```

### stop - Stop a server

Stop a running agentapi server by PID or port.

```bash
# Stop by process ID
cyberian stop 12345

# Stop by port number (using shorthand)
cyberian stop -p 3284
```

**Options:**
- `pid` - Process ID of the server to stop (positional)
- `--port`, `-p` - Port number to find and stop the server

### run - Execute workflows

Run complex multi-step workflows defined in YAML files.

```bash
# Basic workflow execution
cyberian run workflow.yaml

# With parameters (using shorthands)
cyberian run workflow.yaml -p query="climate change" -p depth="comprehensive"

# Change directory and specify agent type
cyberian run workflow.yaml -d /my/project -a claude

# Skip permission checks (passes to template context)
cyberian run workflow.yaml -s

# All options combined with shorthands
cyberian run workflow.yaml -H example.com -P 8080 -T 600 -d ./workspace -a aider -s
```

**Options:**
- `workflow_file` - Path to workflow YAML file (required, positional)
- `--host`, `-H` - Agent API host (default: "localhost")
- `--port`, `-P` - Agent API port (default: 3284)
- `--timeout`, `-T` - Timeout in seconds per task (default: 300)
- `--dir`, `-d` - Change to this directory before running workflow
- `--agent-type`, `-a` - Agent type to use (added to template context)
- `--skip-permissions`, `-s` - Skip permission checks (added to template context)
- `--param`, `-p` - Parameter in format key=value (can be used multiple times)
- `--agent-lifecycle` - Agent server lifecycle mode: `reuse` (default, keeps server running) or `refresh` (restarts server between tasks for clean state)

## Workflow System

### YAML Workflow Structure

Workflows are defined using a recursive task model (Russian dolls) where each task can contain subtasks.

#### Basic Workflow

```yaml
name: simple-task
description: A simple task
instructions: |
  Research {{query}} and write a summary.

params:
  query:
    range: string
    required: true
```

#### Workflow with Subtasks

```yaml
name: complex-workflow
description: Multi-step research workflow

params:
  query:
    range: string
    required: true

subtasks:
  initial_search:
    instructions: |
      Perform initial research on {{query}}.
      Write a research plan.

  deep_dive:
    instructions: |
      Based on the research plan, do a deep dive into {{query}}.
      Write detailed findings.

  summary:
    instructions: |
      Summarize all findings about {{query}}.
```

#### Looping Tasks

Tasks can loop until a condition is met using `loop_until`:

```yaml
name: iterative-research
description: Keep researching until exhausted

params:
  query:
    range: string
    required: true

subtasks:
  iterate:
    instructions: |
      Keep researching {{query}}. Find new angles and perspectives.

    loop_until:
      status: NO_MORE_RESEARCH
      message: |
        If you think all research avenues are exhausted,
        yield status: NO_MORE_RESEARCH
```

#### Provider Calls

Tasks can call external providers directly instead of using agents. This is useful for deterministic operations like research, data retrieval, or API calls.

**Installation:**

```bash
# Install with provider support
pip install cyberian[providers]
```

**Basic Provider Call:**

```yaml
name: simple-research
description: Research using deep-research-client provider

params:
  query:
    range: string
    required: true
  output:
    range: string
    required: true

subtasks:
  research:
    provider_call:
      provider: deep-research-client
      method: research
      params:
        query: "{{query}}"
        use_cache: true
      output_file: "{{output}}"
```

**Hybrid Workflow (Provider + Agent):**

Combine provider calls for data gathering with agent-based synthesis:

```yaml
name: deep-research-hybrid
description: Use provider for research, agent for analysis

params:
  query:
    range: string
    required: true
  workdir:
    range: string
    required: true

subtasks:
  # Provider gathers data
  gather_data:
    provider_call:
      provider: deep-research-client
      method: research
      params:
        query: "{{query}}"
        provider: openai  # specific provider
        model: o3-mini    # specific model
      output_file: "{{workdir}}/raw_research.md"

  # Agent synthesizes and organizes
  create_report:
    instructions: |
      Read {{workdir}}/raw_research.md and create a structured
      report with citations in REPORT.md.
      COMPLETION_STATUS: COMPLETE
```

**Provider Methods:**

The `deep-research-client` provider supports:
- `research` - Perform deep research on a query
- `list_providers` - List available research providers
- `list_models` - List available models

**Provider Parameters:**

```yaml
provider_call:
  provider: deep-research-client
  method: research
  params:
    query: "{{query}}"           # Required: research question
    provider: openai             # Optional: specific provider (openai, perplexity, consensus, falcon)
    model: o3-mini              # Optional: specific model
    use_cache: true             # Optional: enable caching
    provider_params: {}         # Optional: provider-specific parameters
  output_file: "{{workdir}}/results.md"  # Optional: save results to file
```

**Success Criteria with Providers:**

Provider calls support success criteria validation:

```yaml
subtasks:
  research:
    provider_call:
      provider: deep-research-client
      method: research
      params:
        query: "{{query}}"
      output_file: "{{workdir}}/results.md"
    success_criteria:
      python: |
        import os
        result = os.path.exists("{{workdir}}/results.md")
      max_retries: 0
```

#### Agent Lifecycle Control

Control how agent servers are managed during workflow execution using `agent_lifecycle`:

```yaml
name: multi-step-workflow
description: Workflow with fresh agent state per task
agent_lifecycle: refresh  # restart server between tasks

subtasks:
  step1:
    instructions: |
      First task with clean state

  step2:
    instructions: |
      Second task with fresh agent (no memory of step1)
```

**Lifecycle Modes:**
- `reuse` (default) - Keep the same agent server running throughout the workflow. Agent maintains context and memory between tasks.
- `refresh` - Restart the agent server between each task. Each task gets a clean agent state with no memory of previous tasks.

**Use Cases for `refresh` mode:**
- Tasks that need isolated, clean environments
- Preventing context pollution between unrelated tasks
- Testing tasks independently
- Long workflows where agent context might become too large

**Command-line override:**
```bash
# Override workflow's agent_lifecycle setting
cyberian run workflow.yaml --agent-lifecycle refresh
```

### Template Variables

All instruction fields support Jinja2 templating with variables from:

1. **Required parameters** defined in `params`
2. **Command-line parameters** via `--param key=value`
3. **Built-in context** from `--agent-type` and `--skip-permissions`

Example:

```yaml
instructions: |
  Use {{agent_type}} to analyze {{query}}.
  Skip permissions: {{skip_permissions}}
```

```bash
cyberian run workflow.yaml \
  --agent-type claude \
  --skip-permissions \
  --param query="AI safety"
```

### Task Execution Model

The TaskRunner executes workflows with the following behavior:

1. **Depth-first traversal** - Tasks execute in order, with subtasks completing before siblings
2. **Completion detection** - Each task must report `COMPLETION_STATUS: COMPLETE` or `COMPLETION_STATUS: ERROR`
3. **Loop handling** - Looping tasks repeat until the specified status appears in agent response
4. **Template rendering** - All `{{variables}}` are rendered before sending to agent
5. **Status polling** - Waits for agent to reach stable state before proceeding

## Examples

### Example: Deep Research Workflow

See [tests/examples/deep-research.yaml](tests/examples/deep-research.yaml):

```yaml
name: deep-research
description: Iteratively performs deep research on a topic

requires_workdir: true

params:
  query:
    range: string
    required: true

subtasks:
  initial_search:
    instructions: |
      Perform deep research on {{query}}.
      Write a comprehensive research plan.

  iterate:
    instructions: |
      Continue researching {{query}}.
      Explore new angles and perspectives.

    loop_until:
      status: NO_MORE_RESEARCH
      message: |
        If you think all research avenues are exhausted,
        yield status: NO_MORE_RESEARCH
```

Run it:

```bash
cyberian run tests/examples/deep-research.yaml \
  -p query="quantum computing" \
  -d ./research-output \
  -a claude
```

## Documentation Website

[https://monarch-initiative.github.io/cyberian](https://monarch-initiative.github.io/cyberian)

## Repository Structure

* [docs/](docs/) - mkdocs-managed documentation
* [project/](project/) - project files (auto-generated, do not edit)
* [src/cyberian/](src/cyberian/) - source code
  * `cli.py` - Typer-based CLI interface
  * `runner.py` - TaskRunner for executing workflows
  * `models.py` - Pydantic models for workflow definitions
* [tests/](tests/) - pytest test suite
  * [examples/](tests/examples/) - Example workflow YAML files

## Developer Tools

This project uses [just](https://github.com/casey/just/) as a command runner.

Common commands:

```bash
# Run all tests
just test

# Run pytest only
just pytest

# Run type checking
just mypy

# Run formatting checks
just format

# Serve documentation locally
just _serve
```

To see all available commands:

```bash
just --list
```

## Development

### Running from source

```bash
# Install dependencies
uv sync

# Run CLI
uv run cyberian --help

# Run tests
uv run pytest tests/

# Type checking
uv run mypy src/cyberian/
```

### Project Stack

- **Python 3.10+** with `uv` for dependency management
- **Typer** for CLI interface
- **httpx** for HTTP client
- **Pydantic** for data validation
- **Jinja2** for template rendering
- **pytest** for testing with parametrization
- **mypy** for static type checking

## Credits

This project uses the template [monarch-project-copier](https://github.com/monarch-initiative/monarch-project-copier)

Built as a wrapper around [agentapi](https://github.com/coder/agentapi)

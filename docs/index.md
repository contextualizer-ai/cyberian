# cyberian

**A Python CLI wrapper for [agentapi](https://github.com/coder/agentapi) that enables automated agent pipelines and workflows.**

[![asciicast](https://asciinema.org/a/U3zU02WqnFgq31nSxa8unSOpG.svg)](https://asciinema.org/a/U3zU02WqnFgq31nSxa8unSOpG)

## What is cyberian?

`cyberian` provides a comprehensive command-line interface for orchestrating AI agents through agentapi. It enables you to:

- **Send messages** to AI agents via agentapi with synchronous or asynchronous modes
- **Manage agentapi servers** - start, stop, and list running servers
- **Run server farms** - manage multiple agent servers simultaneously
- **Execute complex workflows** from YAML definitions with recursive task trees
- **Use template-based instructions** with Jinja2 for dynamic, parameterized workflows
- **Call external providers** directly in workflows for deterministic operations

## Quick Start

```bash
# Install
pip install cyberian

# Start an agentapi server
cyberian server start claude --skip-permissions --port 3284 --dir /tmp/workdir

# Send a message
cyberian message "Write a hello world function in Python"

# Check status
cyberian status

# View in chat interface
open http://localhost:3284/chat
```

## Key Features

### Simple Message Sending

```bash
# Fire-and-forget message
cyberian message "Your prompt here"

# Synchronous mode - wait for response
cyberian message "What is 2+2?" --sync
```

### Server Farm Management

Start and manage multiple agent servers from a single configuration:

```bash
cyberian farm start my-farm.yaml
```

```yaml
base_port: 4000
servers:
  - name: worker1
    agent_type: claude
    directory: /tmp/worker1
    skip_permissions: true
  - name: worker2
    agent_type: claude
    directory: /tmp/worker2
```

### Workflow Automation

Execute complex multi-step workflows with recursive task trees:

```bash
cyberian run deep-research.yaml --param query="quantum computing"
```

```yaml
name: deep-research
description: Iteratively performs deep research on a topic

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
        If exhausted, yield status: NO_MORE_RESEARCH
```

## Installation

```bash
# Basic installation
pip install cyberian

# With provider support for external API calls
pip install cyberian[providers]

# Or use without installation
uvx cyberian
```

## Where to Go Next

<div class="grid cards" markdown>

-   :material-school:{ .lg .middle } **Tutorials**

    ---

    New to cyberian? Start here to learn the basics.

    [:octicons-arrow-right-24: Getting Started](tutorials/getting-started.md)

-   :material-book-open-variant:{ .lg .middle } **How-To Guides**

    ---

    Task-oriented guides for specific problems.

    [:octicons-arrow-right-24: Browse Guides](how-to/index.md)

-   :material-lightbulb:{ .lg .middle } **Explanation**

    ---

    Understand how cyberian works under the hood.

    [:octicons-arrow-right-24: Learn Concepts](explanation/index.md)

-   :material-book-alphabet:{ .lg .middle } **Reference**

    ---

    Complete reference for all commands and schemas.

    [:octicons-arrow-right-24: CLI Reference](reference/cli-commands.md)

</div>

## Integration with Claude Code

A Claude Code skill is available for multi-agent orchestration:

```bash
/plugin marketplace add cyberian-skills
```

See [Claude Code Skill](integrations/claude-skill.md) for details.

## Project Links

- **Documentation**: [https://monarch-initiative.github.io/cyberian](https://monarch-initiative.github.io/cyberian)
- **Source Code**: [https://github.com/monarch-initiative/cyberian](https://github.com/monarch-initiative/cyberian)
- **Issue Tracker**: [https://github.com/monarch-initiative/cyberian/issues](https://github.com/monarch-initiative/cyberian/issues)
- **agentapi**: [https://github.com/coder/agentapi](https://github.com/coder/agentapi)

## Technology Stack

- **Python 3.10+** with `uv` for dependency management
- **Typer** for CLI interface
- **httpx** for HTTP client interactions
- **Pydantic** for data modeling and validation
- **Jinja2** for template rendering in workflows
- **pytest** for comprehensive testing

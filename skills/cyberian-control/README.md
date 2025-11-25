# Cyberian Control Skill

A Claude Code skill for controlling and coordinating multiple AI agent sessions using the `cyberian` CLI.

## Overview

This skill enables a Claude Code session to:
- Control multiple other Claude Code (or AI agent) sessions
- Send messages to and retrieve results from remote agents
- Start and manage farms of agents for parallel processing
- Execute complex multi-step workflows across agents
- Coordinate multi-agent research, development, and other tasks

## Use Cases

- **Multi-agent orchestration** - Coordinate multiple agents working on different aspects of a problem
- **Delegated tasks** - Send specialized tasks to dedicated agent instances
- **Parallel processing** - Run multiple agents simultaneously on related tasks
- **Complex workflows** - Execute multi-step processes with handoffs between agents
- **Distributed development** - Coordinate agents for research, coding, testing, and documentation

## Installation

### Prerequisites

1. **Install cyberian CLI:**

```bash
# From PyPI
pip install cyberian

# Or use uvx for one-off commands
uvx cyberian --help

# For provider features (optional)
pip install cyberian[providers]
```

2. **Install the skill via Claude Code marketplace:**

In Claude Code, run:
```
/plugin marketplace add cyberian-skills
```

Then browse and install the `cyberian-control` plugin.

### Alternative: Direct Installation

Copy the `cyberian-control` directory to your project's `.claude/skills/` directory:

```bash
# From the cyberian repository
cp -r cyberian-control /path/to/your/project/.claude/skills/
```

## Quick Start

### Example 1: Delegate a Task

```bash
# Start a remote agent
cyberian server claude -p 4000 -d /tmp/specialist --skip-permissions

# In Claude Code session, the skill helps you send tasks:
cyberian message "Write a binary search tree implementation in Rust" \
  --sync --timeout 300 --port 4000

# Retrieve results
cyberian messages --format yaml --last 10 --port 4000
```

### Example 2: Parallel Research

```bash
# Start a farm of research agents
cyberian farm start cyberian-control/examples/farm-config.yaml

# Send different research angles to different agents
cyberian message "Research quantum computing history" -P 5000 &
cyberian message "Research quantum computing applications" -P 5001 &
cyberian message "Research quantum computing challenges" -P 5002 &
wait

# Collect results from all agents
cyberian messages -f yaml -P 5000 > quantum-history.yaml
cyberian messages -f yaml -P 5001 > quantum-apps.yaml
cyberian messages -f yaml -P 5002 > quantum-challenges.yaml
```

### Example 3: Run a Multi-Step Workflow

```bash
cyberian run cyberian-control/examples/multi-agent-research.yaml \
  -p query="CRISPR gene editing" \
  -d ./research-output \
  -a claude
```

## Skill Features

### Commands Covered

The skill provides comprehensive knowledge about these cyberian commands:

- **`cyberian message`** - Send messages to agents (with sync mode)
- **`cyberian messages`** - Retrieve conversation history
- **`cyberian status`** - Check agent status
- **`cyberian server`** - Start agent servers
- **`cyberian farm`** - Manage multiple agents
- **`cyberian run`** - Execute workflows
- **`cyberian list-servers`** - List running servers
- **`cyberian stop`** - Stop servers

### Common Patterns

The skill includes examples for:

1. **Sequential workflows** - Tasks that build on each other
2. **Parallel execution** - Multiple agents working simultaneously
3. **Iterative refinement** - Looping until completion criteria met
4. **Hybrid provider+agent** - Using providers for data, agents for synthesis
5. **Farm-based coordination** - Managing specialized agent pools

### Example Files

- **Shell Scripts:**
  - `simple-delegation.sh` - Delegate single task
  - `parallel-research.sh` - Run parallel research
  - `monitor-farm.sh` - Monitor agent farm status

- **Workflow Files:**
  - `multi-agent-research.yaml` - Coordinated research from multiple angles
  - `delegated-coding.yaml` - Multi-agent software development
  - `farm-config.yaml` - Example farm configuration

## How It Works

When you invoke this skill in a Claude Code session, Claude gains access to comprehensive knowledge about:

1. **Cyberian CLI syntax and options** - All commands, flags, and parameters
2. **Workflow system** - YAML structure for complex multi-step tasks
3. **Farm management** - Running multiple agents with shared configuration
4. **Best practices** - Proven patterns for multi-agent coordination
5. **Troubleshooting** - Common issues and solutions

The skill is designed to be invoked automatically when Claude detects you're working on multi-agent coordination tasks.

## Testing

The skill includes comprehensive tests to ensure quality:

```bash
# Run skill tests
uv run pytest tests/test_skill.py -v
```

Tests verify:
- Marketplace configuration is valid
- Skill metadata is properly formatted
- Example files exist and are valid
- Documentation is comprehensive
- Shell scripts are executable

## Documentation

- **[SKILL.md](SKILL.md)** - Complete skill reference loaded by Claude
- **[examples/README.md](examples/README.md)** - Example usage documentation
- **[Example workflows](examples/)** - Sample YAML workflows and scripts

## Architecture

```
cyberian-control/
├── SKILL.md              # Main skill documentation (loaded by Claude)
├── README.md             # This file
└── examples/
    ├── README.md         # Example documentation
    ├── simple-delegation.sh
    ├── parallel-research.sh
    ├── monitor-farm.sh
    ├── multi-agent-research.yaml
    ├── delegated-coding.yaml
    └── farm-config.yaml
```

## Best Practices

1. **Always specify ports** when running multiple agents
2. **Use meaningful working directories** to keep agent workspaces isolated
3. **Set appropriate timeouts** for complex tasks
4. **Monitor agent status** before sending new tasks
5. **Use farm template directories** to share configuration
6. **Clean up servers** when done: `cyberian stop -p PORT`

## Troubleshooting

### Skill Not Loading

Ensure the plugin is installed:
```
/plugin
# Select "Manage and uninstall plugins"
# Verify cyberian-control is listed
```

### Cyberian Command Not Found

Install the CLI:
```bash
pip install cyberian
# or
uvx cyberian --help
```

### Agent Not Responding

Check status and restart if needed:
```bash
cyberian status -P 3284
cyberian stop -p 3284
cyberian server claude -p 3284 -d /tmp/workdir
```

## Contributing

This skill is part of the [cyberian](https://github.com/monarch-initiative/cyberian) project.

To contribute:
1. Fork the repository
2. Create your feature branch
3. Add tests for any changes
4. Submit a pull request

## License

Same license as the cyberian project.

## Links

- [Cyberian Documentation](https://monarch-initiative.github.io/cyberian)
- [Cyberian GitHub Repository](https://github.com/monarch-initiative/cyberian)
- [agentapi](https://github.com/coder/agentapi) - The underlying API wrapper
- [Claude Code Skills Documentation](https://support.claude.com/en/articles/12512198-creating-custom-skills)

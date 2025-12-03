# Claude Code Skill

The `cyberian-control` skill enables Claude Code sessions to control and coordinate multiple AI agent instances.

## Overview

The cyberian-control skill provides comprehensive knowledge about using cyberian's CLI to orchestrate multi-agent workflows. When installed, Claude can automatically use this skill when working on tasks involving:

- Multi-agent coordination
- Delegating tasks to remote agents
- Managing agent farms
- Running complex workflows
- Parallel agent execution

## Installation

### Method 1: Via Marketplace (Recommended)

In Claude Code, run:

```
/plugin marketplace add cyberian-skills
```

Then browse and install the `cyberian-control` plugin.

### Method 2: Copy to Project

Copy the skill to your project's skills directory:

```bash
cp -r cyberian-control /path/to/your/project/.claude/skills/
```

## What the Skill Provides

The skill teaches Claude how to:

### 1. Send Messages to Agents

```bash
# Fire-and-forget
cyberian message "Your task here" -P 3284

# Wait for completion
cyberian message "Your task here" --sync -P 3284
```

### 2. Manage Agent Servers

```bash
# Start an agent
cyberian server claude -p 3284 -d /tmp/workdir

# Check status
cyberian status -P 3284

# Stop an agent
cyberian stop -p 3284
```

### 3. Run Agent Farms

```yaml
# farm.yaml
base_port: 4000
servers:
  - name: researcher
    agent_type: claude
    directory: /tmp/researcher
    skip_permissions: true

  - name: coder
    agent_type: claude
    directory: /tmp/coder
    skip_permissions: true
```

```bash
cyberian farm start farm.yaml
```

### 4. Execute Workflows

```yaml
# workflow.yaml
name: research-task
description: Multi-step research

params:
  query:
    range: string
    required: true

subtasks:
  gather:
    instructions: |
      Research {{query}}. Save to RESEARCH.md.
      COMPLETION_STATUS: COMPLETE

  analyze:
    instructions: |
      Analyze RESEARCH.md. Create ANALYSIS.md.
      COMPLETION_STATUS: COMPLETE
```

```bash
cyberian run workflow.yaml -p query="topic" -d ./output
```

## Use Cases

### 1. Parallel Research

Have multiple agents research different aspects of a topic simultaneously:

```bash
# Start farm
cyberian farm start research-farm.yaml

# Send different topics to each
cyberian message "Research history of X" -P 5000 &
cyberian message "Research current state of X" -P 5001 &
cyberian message "Research future of X" -P 5002 &
wait

# Collect results
cyberian messages -f yaml -P 5000 > history.yaml
cyberian messages -f yaml -P 5001 > current.yaml
cyberian messages -f yaml -P 5002 > future.yaml
```

### 2. Delegated Development

Delegate different parts of a project to specialized agents:

```bash
# Agent 1: Backend
cyberian message "Implement backend API" -P 4000 --sync

# Agent 2: Frontend
cyberian message "Implement frontend UI" -P 4001 --sync

# Agent 3: Tests
cyberian message "Write tests for backend and frontend" -P 4002 --sync
```

### 3. Iterative Refinement

Use workflows with looping for iterative improvement:

```yaml
subtasks:
  refine:
    instructions: |
      Improve the solution. When perfect: REFINEMENT_COMPLETE
    loop_until:
      status: REFINEMENT_COMPLETE
```

### 4. Hybrid Workflows

Combine providers (for data) with agents (for synthesis):

```yaml
subtasks:
  gather:
    provider_call:
      provider: deep-research-client
      method: research
      params:
        query: "{{query}}"
      output_file: "data.md"

  synthesize:
    instructions: |
      Read data.md and create report.
      COMPLETION_STATUS: COMPLETE
```

## Examples

The skill includes several examples in `cyberian-control/examples/`:

### Shell Scripts

- **simple-delegation.sh** - Delegate single task to agent
- **parallel-research.sh** - Run parallel research across agents
- **monitor-farm.sh** - Monitor agent farm in real-time

### Workflow Files

- **multi-agent-research.yaml** - Coordinated multi-perspective research
- **delegated-coding.yaml** - Multi-agent software development
- **farm-config.yaml** - Example farm configuration

## How Claude Uses the Skill

When you ask Claude to coordinate multiple agents or run complex multi-agent workflows, Claude will:

1. **Invoke the skill** - Load the cyberian-control knowledge
2. **Plan the coordination** - Design the multi-agent approach
3. **Execute commands** - Use `cyberian` CLI via Bash tool
4. **Monitor progress** - Check agent status and retrieve results
5. **Synthesize results** - Combine outputs from multiple agents

## Best Practices

The skill teaches Claude these best practices:

1. **Always specify ports** when working with multiple agents
2. **Use --sync mode** when you need to wait for completion
3. **Set appropriate timeouts** for complex tasks
4. **Monitor agent status** before sending new tasks
5. **Use farm template directories** to share configuration
6. **Clean up servers** when done

## Skill Architecture

```
cyberian-control/
├── SKILL.md              # Main skill (loaded by Claude)
├── README.md             # Installation & overview
└── examples/
    ├── README.md         # Example documentation
    ├── *.sh              # Shell script examples
    └── *.yaml            # Workflow examples
```

The `SKILL.md` file contains the complete knowledge that Claude loads, including:

- When to use the skill
- Complete command reference
- Common patterns
- Workflow system
- Best practices
- Troubleshooting

## Testing

The skill includes comprehensive tests:

```bash
uv run pytest tests/test_skill.py -v
```

Tests verify:
- Marketplace configuration
- Skill structure and metadata
- Example files validity
- Documentation completeness

## Resources

- **[Skill README](../cyberian-control/README.md)** - Installation and overview
- **[Skill Documentation](../cyberian-control/SKILL.md)** - Complete reference
- **[Examples](../cyberian-control/examples/)** - Sample workflows and scripts
- **[Cyberian Documentation](index.md)** - Main cyberian docs

## Publishing the Skill

To make the skill available to others:

1. **Ensure repo is public** on GitHub
2. **Users install via marketplace:**
   ```
   /plugin marketplace add owner/repo-name
   ```

3. **Or via local path during development:**
   ```
   /plugin marketplace add /path/to/cyberian/.claude-plugin/marketplace.json
   ```

Users will then be able to browse and install the `cyberian-control` skill from the plugin marketplace.

## Advanced Usage

### Custom Farm Configurations

Create specialized farms for different use cases:

```yaml
# ml-research-farm.yaml
base_port: 6000
servers:
  - name: data-scientist
    agent_type: claude
    directory: /tmp/data-sci
    template_directory: ./templates/data-science

  - name: ml-engineer
    agent_type: claude
    directory: /tmp/ml-eng
    template_directory: ./templates/ml-engineering

  - name: researcher
    agent_type: claude
    directory: /tmp/researcher
    template_directory: ./templates/research
```

### Template Directories

Share configuration across farm agents:

```bash
# Create template
mkdir -p templates/researcher/.claude
cat > templates/researcher/.claude/CLAUDE.md << 'EOF'
# Research Agent
- Focus on comprehensive information gathering
- Cite sources
- Be thorough and analytical
EOF

# Farm config references it
# template_directory: ./templates/researcher
```

### Complex Workflows

Build multi-stage workflows with dependencies:

```yaml
name: complex-project
description: Multi-stage development workflow

params:
  feature:
    range: string
    required: true

subtasks:
  design:
    instructions: |
      Design {{feature}}. Create DESIGN.md.
      COMPLETION_STATUS: COMPLETE

  implement_backend:
    instructions: |
      Read DESIGN.md. Implement backend.
      COMPLETION_STATUS: COMPLETE

  implement_frontend:
    instructions: |
      Read DESIGN.md. Implement frontend.
      COMPLETION_STATUS: COMPLETE

  test:
    instructions: |
      Write tests for backend and frontend.
      COMPLETION_STATUS: COMPLETE

  document:
    instructions: |
      Create comprehensive documentation.
      COMPLETION_STATUS: COMPLETE
```

## Troubleshooting

### Skill Not Loading

Verify installation:
```
/plugin
# Select "Manage and uninstall plugins"
# Check if cyberian-control is listed
```

### Commands Not Working

Ensure cyberian CLI is installed:
```bash
pip install cyberian
# or
uvx cyberian --help
```

### Agent Not Responding

Check and restart:
```bash
cyberian status -P 3284
cyberian stop -p 3284
cyberian server claude -p 3284 -d /tmp/workdir
```

## Future Enhancements

Potential future additions to the skill:

- More workflow examples for specific domains
- Integration with additional agent types
- Advanced coordination patterns
- Performance optimization examples
- Multi-machine deployment examples

## Contributing

To contribute to the skill:

1. Fork the cyberian repository
2. Modify files in `cyberian-control/`
3. Add tests in `tests/test_skill.py`
4. Submit pull request

Contributions welcome for:
- New example workflows
- Additional patterns
- Documentation improvements
- Bug fixes

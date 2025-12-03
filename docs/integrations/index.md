# Integrations

cyberian integrates with various tools and services to extend its capabilities.

## Available Integrations

### [Claude Code Skill](claude-skill.md)

A Claude Code skill for multi-agent orchestration. Install with:

```bash
/plugin marketplace add cyberian-skills
```

Use the skill to manage cyberian workflows directly from Claude Code.

## Integration Patterns

### Claude Code + cyberian

Use Claude Code to:

- Author workflows interactively
- Debug workflow execution
- Manage server farms
- Coordinate multiple agents

### Multi-Agent Workflows

Coordinate multiple agents via farms:

```bash
cyberian farm start farm.yaml

# Run workflows on different agents
cyberian run task1.yaml --port 4000 &
cyberian run task2.yaml --port 4001 &
wait
```

## See Also

- [Tutorial: Multi-Agent Farm](../tutorials/multi-agent-farm.md)
- [How-To: Manage Servers](../how-to/manage-servers.md)

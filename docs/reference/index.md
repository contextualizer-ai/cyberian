# Reference Documentation

The reference section provides **information-oriented** documentation: complete specifications, command references, and schemas.

## What is Reference Documentation?

Reference docs are like a dictionary - you look things up when you need specific information:

- Complete command syntax
- All available options
- YAML schema specifications
- Configuration file formats

For learning, see [Tutorials](../tutorials/index.md). For solving problems, see [How-To Guides](../how-to/index.md).

## Available References

### [CLI Commands](cli-commands.md)

Complete reference for all cyberian commands:

- `message` - Send messages to agents
- `messages` - Retrieve conversation history
- `status` - Check agent status
- `server` - Start agentapi servers
- `farm` - Manage server farms
- `list-servers` - Find running servers
- `stop` - Stop servers
- `run` - Execute workflows

Each command includes:

- Full syntax
- All options and flags
- Shorthands
- Examples
- Exit codes

### [Workflow Schema](workflow-schema.md)

Complete YAML schema specification for workflows:

- Top-level workflow fields
- Task structure
- Parameter types
- Loop configuration
- Success criteria
- Provider calls
- All optional fields

Includes:

- Field descriptions
- Types and constraints
- Required vs optional
- Default values
- Examples

### [Configuration](configuration.md)

Configuration file formats:

- Farm configuration files
- Server configuration
- Template directories
- CORS settings

## Using Reference Docs

**Look things up** when you need to know:

- "What flags does `message` accept?"
- "What's the syntax for loop_until?"
- "What fields are required in a farm config?"

**Don't read cover-to-cover** - Use as a reference when needed.

## See Also

- **[Tutorials](../tutorials/index.md)** - Learning-oriented guides
- **[How-To Guides](../how-to/index.md)** - Task-oriented recipes
- **[Explanation](../explanation/index.md)** - Understanding-oriented discussions

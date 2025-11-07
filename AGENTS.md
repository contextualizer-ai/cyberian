# AGENTS.md - Project Summary for AI Agents

## Project Overview

**cyberian** is a Python CLI wrapper for [agentapi](https://github.com/coder/agentapi) that enables interaction with AI agent APIs in pipeline workflows.

**Repository**: https://github.com/monarch-initiative/cyberian
**Documentation**: https://monarch-initiative.github.io/cyberian

## Purpose

This tool provides a command-line interface for:
- Sending messages to agent APIs with synchronous/asynchronous modes
- Retrieving conversation history in multiple formats (JSON, YAML, CSV)
- Monitoring agent status and availability
- Managing agent servers (start, list, discover)
- Integration into automated pipelines and batch workflows

## Core Functionality

### Commands

The CLI provides the following subcommands:

#### 1. `message` - Send messages to an agent API

Send a message to an agentapi server with optional synchronous waiting.

**Usage**: `cyberian message CONTENT [OPTIONS]`

**Arguments**:
- `CONTENT` - Message content (positional, required)

**Options**:
- `--type TEXT` - Message type (default: "user")
- `--host TEXT` - Agent API host (default: "localhost")
- `--port INTEGER` - Agent API port (default: 3284)
- `--sync` - Wait for agent response and return only the last agent message
- `--timeout INTEGER` - Timeout in seconds when using --sync (default: 60)
- `--poll-interval FLOAT` - Status polling interval in seconds (default: 0.5)

**Examples**:
```bash
# Send message (async, returns immediately)
cyberian message "Hello, agent!"

# Send and wait for response (sync)
cyberian message "What is 2+2?" --sync

# Custom timeout for long-running tasks
cyberian message "Analyze large codebase" --sync --timeout 120

# Different message type
cyberian message "System initialization" --type system
```

#### 2. `messages` - Retrieve conversation history

Retrieve all messages from the agent API with flexible output formatting.

**Usage**: `cyberian messages [OPTIONS]`

**Options**:
- `--host TEXT` - Agent API host (default: "localhost")
- `--port INTEGER` - Agent API port (default: 3284)
- `--format [json|yaml|csv]` - Output format (default: "json")
- `--last INTEGER` - Get only the last N messages

**Examples**:
```bash
# Get all messages (JSON format)
cyberian messages

# Get messages in YAML
cyberian messages --format yaml

# Get last 5 messages as CSV
cyberian messages --format csv --last 5

# Combine filters
cyberian messages --last 10 --format yaml
```

#### 3. `status` - Check agent API server status

Check if the agent server is running and get status information.

**Usage**: `cyberian status [OPTIONS]`

**Options**:
- `--host TEXT` - Agent API host (default: "localhost")
- `--port INTEGER` - Agent API port (default: 3284)

**Examples**:
```bash
# Check status of default server
cyberian status

# Check remote server
cyberian status --host api.example.com --port 8080
```

#### 4. `server` - Start an agentapi server

Start an agentapi server process with specified agent type.

**Usage**: `cyberian server [AGENT] [OPTIONS]`

**Arguments**:
- `AGENT` - Agent type: aider, claude, cursor, goose, custom, etc. (default: "custom")

**Options**:
- `--port, -p INTEGER` - Port to run the server on (default: 3284)
- `--allowed-hosts TEXT` - HTTP allowed hosts (comma-separated)
- `--allowed-origins TEXT` - HTTP allowed origins (comma-separated)

**Examples**:
```bash
# Start server with default "custom" agent
cyberian server

# Start Claude agent
cyberian server claude

# Custom port
cyberian server aider --port 8080

# With CORS configuration
cyberian server goose --allowed-hosts "localhost,example.com"
```

**Note**: The specified agent executable must be installed and available in your PATH.

#### 5. `list-servers` - List running agentapi processes

Discover all running agentapi server processes using `ps`.

**Usage**: `cyberian list-servers`

**Output**: Shows PID and full command line for each running agentapi server.

**Examples**:
```bash
# List all running servers
cyberian list-servers

# Example output:
# Running agentapi servers:
# --------------------------------------------------------------------------------
# 12345 agentapi server custom --port 3284
# 67890 agentapi server claude --port 8080
```

## Technology Stack

- **Python**: 3.10+
- **CLI Framework**: Typer
- **HTTP Client**: httpx
- **Package Management**: uv
- **Command Runner**: just
- **Testing**: pytest
- **Type Checking**: mypy
- **Linting/Formatting**: ruff

## Project Structure

```
cyberian/
├── src/cyberian/
│   ├── cli.py           # Main CLI implementation
│   ├── __init__.py
│   └── _version.py
├── tests/
│   ├── test_commands.py # Command tests
│   ├── test_message.py  # Message functionality tests
│   └── test_simple.py   # Basic tests
├── docs/                # MkDocs documentation
├── pyproject.toml       # Project configuration
├── justfile             # Command recipes
└── CLAUDE.md            # Development guidelines
```

## Key Files

- **src/cyberian/cli.py** (~250 lines) - Main CLI implementation with all commands
- **tests/test_commands.py** - Tests for messages, status, server, list-servers commands
- **tests/test_message.py** - Tests for message command including sync mode
- **pyproject.toml** - Dependencies and project metadata
- **justfile** - Development workflow commands
- **CLAUDE.md** - Development guidelines and instructions
- **NOTIFY_FEATURE.md** - Future enhancement documentation (background notifications)

## Development Workflow

### Essential Commands

```bash
# Install dependencies
just install

# Run all tests
just test

# Run specific test suite
just pytest

# Type checking
just mypy

# Linting/formatting
just format

# Run CLI
uv run cyberian --help

# Serve documentation
just _serve
```

### Testing Philosophy

- **Test-Driven Development**: Write tests before implementation
- **pytest-style tests**: Uses pytest with fixtures and parametrization
- **Comprehensive coverage**: 38 tests covering all commands and features
- **Mocking HTTP calls**: Uses `unittest.mock.patch` for httpx requests
- **Parametrized tests**: Testing multiple scenarios efficiently
- **Doctests**: Used for documentation and testing
- **Full functionality tests**: Tests must validate actual behavior, not just pass

### Code Quality Standards

- **Avoid try/except blocks** unless interfacing with external systems
- **No code duplication**
- **Parsimonious solutions**
- **Type hints** with mypy validation
- **Comprehensive doctests** in all functions

## API Endpoints Wrapped

The CLI wraps these agentapi endpoints:

- `POST /message` - Send messages
- `GET /messages` - Retrieve conversation history
- `GET /status` - Check server status

## Pipeline Integration Examples

### Basic Message Flow
```bash
# Send a message and capture response
RESPONSE=$(cyberian message "Analyze this codebase" --sync)
echo "$RESPONSE" > analysis.txt
```

### Batch Processing with CSV Output
```bash
# Get conversation history as CSV for analysis
cyberian messages --format csv --last 100 > conversation.csv

# Process with other tools
cat conversation.csv | grep "error" | wc -l
```

### Multi-Server Setup
```bash
# Start multiple agents on different ports
cyberian server claude --port 3284 &
cyberian server aider --port 3285 &

# Wait a bit for servers to start
sleep 2

# List all running servers
cyberian list-servers

# Send messages to different agents
cyberian message "Review this code" --port 3284 --sync > claude-review.txt
cyberian message "Fix this bug" --port 3285 --sync > aider-fix.txt
```

### Automated Workflow
```bash
#!/bin/bash
# automated-review.sh

# Start server in working directory
cd /my/project
cyberian server aider --port 3300 &
SERVER_PID=$!

# Wait for server startup
sleep 3

# Send analysis request
cyberian message "Analyze all Python files in this directory" \
  --port 3300 \
  --sync \
  --timeout 300 > analysis.md

# Get structured conversation data
cyberian messages --port 3300 --format yaml > conversation.yaml

# Cleanup
kill $SERVER_PID
```

## Integration with Pipelines

This tool is designed for pipeline integration where AI agents need to:
- Process batch requests
- Maintain conversation context
- Output structured data (CSV/YAML/JSON)
- Run automated workflows
- Monitor agent availability

## Dependencies

### Core Runtime
- `typer >= 0.9.0` - CLI framework
- `httpx >= 0.27.0` - HTTP client
- `pyyaml >= 6.0` - YAML support
- `pydantic >= 2.12.3` - Data validation
- `linkml-runtime >= 1.9.4` - Data modeling

### Development
- `pytest` - Testing
- `mypy` - Type checking
- `ruff` - Linting/formatting
- `mkdocs-material` - Documentation

## Architecture Notes

- **Single module design**: All CLI logic in `src/cyberian/cli.py`
- **Stateless commands**: Each command is independent
- **External dependencies**: Wraps the `agentapi` tool (must be installed separately)
- **Process management**: Uses subprocess for server control
- **HTTP communication**: All agent interactions via HTTP/REST

## Common Development Tasks

### Adding a new command

1. Add command function to `src/cyberian/cli.py`
2. Use `@app.command()` decorator
3. Include docstring with examples
4. Write tests in `tests/test_commands.py`
5. Run `just test` to validate

### Testing HTTP interactions

Tests use `unittest.mock.patch` to mock httpx calls:

```python
with patch("cyberian.cli.httpx.get") as mock_get:
    mock_response = Mock()
    mock_response.json.return_value = {"status": "ok"}
    mock_get.return_value = mock_response
    # Test code here
```

## Related Projects

- **agentapi**: The underlying agent API server this tool wraps
- **monarch-project-copier**: Template used for project scaffolding

## Contributing

See `CONTRIBUTING.md` for contribution guidelines.

## License

BSD-3-Clause

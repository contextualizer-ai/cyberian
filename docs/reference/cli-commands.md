# CLI Command Reference

Complete reference for all cyberian commands.

## Global Options

All commands support:

- `-h`, `--help` - Show help message

## Quick Reference: Common Shorthands

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

## message

Send a message to an AI agent via agentapi.

### Synopsis

```bash
cyberian message [OPTIONS] CONTENT
```

### Description

Sends a message to a running agentapi server. Supports both fire-and-forget mode (default) and synchronous mode where cyberian waits for the agent's response.

### Arguments

- `CONTENT` - **Required**. The message content to send to the agent.

### Options

| Option | Shorthand | Type | Default | Description |
|--------|-----------|------|---------|-------------|
| `--host` | `-H` | string | `localhost` | Agent API host |
| `--port` | `-P` | integer | `3284` | Agent API port |
| `--type` | `-t` | string | `user` | Message type |
| `--sync` | `-s` | flag | `false` | Wait for agent response |
| `--timeout` | `-T` | integer | `60` | Timeout in seconds (only with --sync) |
| `--poll-interval` | | float | `0.5` | Status polling interval in seconds |

### Message Types

- `user` - User message (default)
- `system` - System message
- `assistant` - Assistant message (simulated)

### Examples

**Basic message (fire-and-forget):**

```bash
cyberian message "Write a hello world function in Python"
```

**Synchronous mode:**

```bash
cyberian message "What is 2+2?" --sync
```

**With timeout:**

```bash
cyberian message "Complex task" --sync --timeout 300
```

**Different message type:**

```bash
cyberian message "You are a helpful assistant" --type system
```

**Custom server:**

```bash
cyberian message "Hello" --host example.com --port 8080
```

**Using shorthands:**

```bash
cyberian message "Hello" -H example.com -P 8080 -s -T 120
```

### Exit Codes

- `0` - Success
- `1` - Error (connection failed, timeout, etc.)

### See Also

- [messages](#messages) - Retrieve conversation history
- [status](#status) - Check agent status
- [How-To: Send Messages](../how-to/send-messages.md)

---

## messages

Retrieve conversation history from the agent.

### Synopsis

```bash
cyberian messages [OPTIONS]
```

### Description

Gets messages from the agent conversation history. Supports multiple output formats and filtering.

### Options

| Option | Shorthand | Type | Default | Description |
|--------|-----------|------|---------|-------------|
| `--host` | `-H` | string | `localhost` | Agent API host |
| `--port` | `-P` | integer | `3284` | Agent API port |
| `--format` | `-f` | string | `json` | Output format |
| `--last` | `-l` | integer | | Get only last N messages |

### Output Formats

- `json` - JSON array (default)
- `yaml` - YAML format
- `csv` - CSV format (type, content, timestamp)

### Examples

**Get all messages (JSON):**

```bash
cyberian messages
```

**Get last 5 messages:**

```bash
cyberian messages --last 5
```

**YAML format:**

```bash
cyberian messages --format yaml
```

**CSV export:**

```bash
cyberian messages --format csv > conversation.csv
```

**Custom server:**

```bash
cyberian messages --host example.com --port 8080
```

**Using shorthands:**

```bash
cyberian messages -f yaml -l 10
```

### Output Structure

**JSON:**

```json
[
  {
    "type": "user",
    "content": "Hello",
    "timestamp": "2024-01-01T00:00:00Z"
  },
  {
    "type": "assistant",
    "content": "Hi!",
    "timestamp": "2024-01-01T00:00:01Z"
  }
]
```

### Exit Codes

- `0` - Success
- `1` - Error (connection failed, etc.)

### See Also

- [message](#message) - Send messages
- [How-To: Send Messages](../how-to/send-messages.md)

---

## status

Check if the agentapi server is running and get its status.

### Synopsis

```bash
cyberian status [OPTIONS]
```

### Description

Checks the status of an agentapi server, including whether it's busy or idle.

### Options

| Option | Shorthand | Type | Default | Description |
|--------|-----------|------|---------|-------------|
| `--host` | `-H` | string | `localhost` | Agent API host |
| `--port` | `-P` | integer | `3284` | Agent API port |

### Examples

**Check default server:**

```bash
cyberian status
```

**Check custom server:**

```bash
cyberian status --host example.com --port 8080
```

**Using shorthands:**

```bash
cyberian status -H example.com -P 8080
```

### Output

```json
{
  "status": "idle",
  "conversation_id": "uuid",
  "available": true
}
```

### Status Values

- `idle` - Agent is ready for work
- `busy` - Agent is currently processing
- `error` - An error occurred

### Exit Codes

- `0` - Success (server is running)
- `1` - Error (connection failed, server not running)

### See Also

- [server](#server) - Start servers
- [list-servers](#list-servers) - Find running servers

---

## server

Start an agentapi server.

### Synopsis

```bash
cyberian server start [OPTIONS] [AGENT_TYPE]
```

### Description

Starts an agentapi server in the background with the specified agent type.

### Arguments

- `AGENT_TYPE` - Optional. Agent type to use. Default: `custom`

### Agent Types

- `custom` - Custom agent (default)
- `claude` - Claude agent
- `aider` - Aider agent
- `cursor` - Cursor agent
- `goose` - Goose agent

### Options

| Option | Shorthand | Type | Default | Description |
|--------|-----------|------|---------|-------------|
| `--port` | `-p` | integer | `3284` | Port to run on |
| `--dir` | `-d` | string | | Working directory |
| `--skip-permissions` | `-s` | flag | `false` | Skip permission checks |
| `--allowed-hosts` | | string | | HTTP allowed hosts (comma-separated) |
| `--allowed-origins` | | string | | HTTP allowed origins (comma-separated) |

### Examples

**Start default server:**

```bash
cyberian server start
```

**Start Claude agent:**

```bash
cyberian server start claude
```

**With specific port:**

```bash
cyberian server start claude --port 8080
```

**With working directory:**

```bash
cyberian server start claude --dir /path/to/project
```

**Skip permissions:**

```bash
cyberian server start claude --skip-permissions
```

**With CORS settings:**

```bash
cyberian server start claude \
  --allowed-origins "https://example.com" \
  --allowed-hosts "example.com"
```

**Using shorthands:**

```bash
cyberian server start claude -p 8080 -d /my/project -s
```

### Exit Codes

- `0` - Success (server started)
- `1` - Error (port in use, invalid agent type, etc.)

### See Also

- [stop](#stop) - Stop servers
- [list-servers](#list-servers) - Find running servers
- [status](#status) - Check server status
- [How-To: Manage Servers](../how-to/manage-servers.md)

---

## farm

Manage server farms.

### Synopsis

```bash
cyberian farm start [OPTIONS] CONFIG_FILE
```

### Description

Starts and manages multiple agentapi servers from a single YAML configuration file.

### Arguments

- `CONFIG_FILE` - **Required**. Path to farm configuration YAML file.

### Examples

**Start farm:**

```bash
cyberian farm start my-farm.yaml
```

### Exit Codes

- `0` - Success (farm started)
- `1` - Error (config invalid, ports in use, etc.)

### See Also

- [Reference: Configuration](configuration.md) - Farm config format
- [Tutorial: Multi-Agent Farm](../tutorials/multi-agent-farm.md)

---

## list-servers

List all running agentapi server processes.

### Synopsis

```bash
cyberian list-servers [OPTIONS]
```

### Description

Finds and lists all running agentapi server processes with their PIDs, ports, and command lines.

### Options

None.

### Examples

**List all servers:**

```bash
cyberian list-servers
```

### Output

```
PID    NAME      CPU  COMMAND
12345  agentapi  0.1  /usr/local/bin/agentapi claude --port 3284
12346  agentapi  0.2  /usr/local/bin/agentapi aider --port 3285
```

### Exit Codes

- `0` - Success
- `1` - Error

### See Also

- [server](#server) - Start servers
- [stop](#stop) - Stop servers
- [How-To: Manage Servers](../how-to/manage-servers.md)

---

## stop

Stop a running agentapi server.

### Synopsis

```bash
cyberian stop [OPTIONS] [PID]
```

### Description

Stops a running agentapi server by process ID or port number.

### Arguments

- `PID` - Optional. Process ID of server to stop.

### Options

| Option | Shorthand | Type | Default | Description |
|--------|-----------|------|---------|-------------|
| `--port` | `-p` | integer | | Find and stop server on this port |

### Examples

**Stop by PID:**

```bash
cyberian stop 12345
```

**Stop by port:**

```bash
cyberian stop --port 3284
```

**Using shorthand:**

```bash
cyberian stop -p 3284
```

### Exit Codes

- `0` - Success (server stopped)
- `1` - Error (server not found, permission denied, etc.)

### See Also

- [server](#server) - Start servers
- [list-servers](#list-servers) - Find running servers
- [How-To: Manage Servers](../how-to/manage-servers.md)

---

## run

Execute a workflow from a YAML file.

### Synopsis

```bash
cyberian run [OPTIONS] WORKFLOW_FILE
```

### Description

Executes a multi-step workflow defined in a YAML file. Automatically starts an agentapi server if needed.

### Arguments

- `WORKFLOW_FILE` - **Required**. Path to workflow YAML file.

### Options

| Option | Shorthand | Type | Default | Description |
|--------|-----------|------|---------|-------------|
| `--host` | `-H` | string | `localhost` | Agent API host |
| `--port` | `-P` | integer | `3284` | Agent API port |
| `--timeout` | `-T` | integer | `300` | Timeout per task (seconds) |
| `--dir` | `-d` | string | | Working directory |
| `--agent-type` | `-a` | string | | Agent type (added to template context) |
| `--skip-permissions` | `-s` | flag | `false` | Skip permissions (added to template context) |
| `--param` | `-p` | string | | Parameter in format key=value (repeatable) |
| `--agent-lifecycle` | | string | `reuse` | Agent lifecycle mode: `reuse` or `refresh` |

### Lifecycle Modes

- `reuse` - Keep agent running, maintains context (default)
- `refresh` - Restart agent between tasks, clean state

### Examples

**Basic workflow:**

```bash
cyberian run workflow.yaml
```

**With parameters:**

```bash
cyberian run workflow.yaml --param query="climate change"
```

**Multiple parameters:**

```bash
cyberian run workflow.yaml \
  --param query="AI safety" \
  --param depth="comprehensive" \
  --param format="markdown"
```

**With working directory:**

```bash
cyberian run workflow.yaml --dir /tmp/workspace
```

**Agent lifecycle control:**

```bash
cyberian run workflow.yaml --agent-lifecycle refresh
```

**All options:**

```bash
cyberian run workflow.yaml \
  --host example.com \
  --port 8080 \
  --timeout 600 \
  --dir ./workspace \
  --agent-type claude \
  --skip-permissions \
  --param query="topic" \
  --agent-lifecycle reuse
```

**Using shorthands:**

```bash
cyberian run workflow.yaml -H localhost -P 3284 -T 600 -d ./workspace -a claude -s -p query="topic"
```

### Exit Codes

- `0` - Success (workflow completed)
- `1` - Error (task failed, timeout, invalid YAML, etc.)

### See Also

- [Reference: Workflow Schema](workflow-schema.md) - YAML specification
- [How-To: Write Workflows](../how-to/write-workflows.md)
- [Tutorial: Your First Workflow](../tutorials/first-workflow.md)
- [Explanation: Workflow Model](../explanation/workflow-model.md)

---

## Environment Variables

Currently cyberian does not use environment variables. All configuration is via command-line flags.

## Configuration Files

cyberian does not use a global configuration file. Configuration is specified per-command or per-workflow.

For farm configuration, see [Configuration Reference](configuration.md).

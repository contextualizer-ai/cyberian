# How to Manage Servers

This guide covers server lifecycle management: starting, stopping, listing, and configuring agentapi servers.

## Start a Server

**Problem:** You need to start an agentapi server.

**Solution:**

```bash
# Start with defaults (custom agent, port 3284)
cyberian server start

# Start specific agent type
cyberian server start claude

# Full configuration
cyberian server start claude \
  --port 8080 \
  --dir /my/project \
  --skip-permissions
```

**Options:**

- `agent` - Agent type: `claude`, `aider`, `cursor`, `goose`, `custom` (default: `custom`)
- `--port`, `-p` - Port number (default: 3284)
- `--dir`, `-d` - Working directory
- `--skip-permissions`, `-s` - Auto-approve tool permissions

**When to use:**

- Beginning a new session
- Starting agents in specific directories
- Setting up isolated environments

## Stop a Server

**Problem:** You need to stop a running server.

**Solution:**

```bash
# Stop by port
cyberian stop --port 3284

# Stop by PID
cyberian stop 12345

# Using shorthand
cyberian stop -p 3284
```

**Find the server first:**

```bash
# List all servers
cyberian list-servers

# Output shows PID and port
# 12345  agentapi  0.1  /usr/local/bin/agentapi  --port 3284
```

**Example:**

```bash
# Stop all agentapi servers
cyberian list-servers | grep agentapi | awk '{print $1}' | while read pid; do
  cyberian stop "$pid"
done
```

## List Running Servers

**Problem:** You need to see all running agentapi servers.

**Solution:**

```bash
cyberian list-servers
```

**Output shows:**

- Process ID (PID)
- Command name
- CPU usage
- Full command with arguments

**Example:**

```bash
# Check if any servers are running
if cyberian list-servers | grep -q agentapi; then
  echo "Servers are running"
else
  echo "No servers running"
fi
```

## Check Server Status

**Problem:** You need to verify a server is responding.

**Solution:**

```bash
# Check default server
cyberian status

# Check specific port
cyberian status --port 8080

# Check remote server
cyberian status --host example.com --port 3284
```

**Output:**

```json
{
  "status": "idle",
  "conversation_id": "abc123",
  "available": true
}
```

**Status values:**

- `idle` - Ready for work
- `busy` - Currently processing
- `error` - Something went wrong

**Example:**

```bash
# Wait for server to be ready
while ! cyberian status --port 3284 > /dev/null 2>&1; do
  echo "Waiting for server..."
  sleep 2
done
echo "Server is ready!"
```

## Configure Port Numbers

**Problem:** Port 3284 is already in use.

**Solution:**

```bash
# Use a different port
cyberian server start claude --port 4000

# Then connect using that port
cyberian message "Hello" --port 4000
cyberian status --port 4000
```

**Avoid conflicts:**

```bash
# Check what ports are in use
cyberian list-servers

# Choose an unused port
cyberian server start claude --port 5000
```

## Set Working Directory

**Problem:** You need the agent to work in a specific directory.

**Solution:**

```bash
# Start server in project directory
cyberian server start claude --dir /path/to/project

# Or use shorthand
cyberian server start claude -d /path/to/project
```

**Example:**

```bash
# Start agent for specific project
mkdir -p ~/projects/my-app
cyberian server start claude \
  --dir ~/projects/my-app \
  --port 3000 \
  --skip-permissions

# Agent can now access project files
cyberian message "List all Python files" --port 3000 --sync
```

## Skip Permission Prompts

**Problem:** You don't want to manually approve every tool use.

**Solution:**

```bash
# Auto-approve all tool permissions
cyberian server start claude --skip-permissions

# Or use shorthand
cyberian server start claude -s
```

**When to use:**

- Trusted environments
- Automated workflows
- Development and testing

**When NOT to use:**

- Untrusted code
- Production environments
- When you want manual control

## Configure CORS

**Problem:** You need to access the server from a web application.

**Solution:**

```bash
cyberian server start claude \
  --allowed-origins "https://myapp.com,https://staging.myapp.com" \
  --allowed-hosts "myapp.com,staging.myapp.com"
```

**Example:**

```bash
# Allow multiple origins
cyberian server start claude \
  --port 3284 \
  --allowed-origins "http://localhost:3000,https://app.example.com" \
  --allowed-hosts "localhost,app.example.com" \
  --skip-permissions
```

This enables your web app to make requests to the agentapi server.

## Run Multiple Servers

**Problem:** You need multiple agents running simultaneously.

**Solution:**

```bash
# Start servers on different ports
cyberian server start claude --port 3000 --dir /tmp/agent1 --skip-permissions
cyberian server start claude --port 3001 --dir /tmp/agent2 --skip-permissions
cyberian server start claude --port 3002 --dir /tmp/agent3 --skip-permissions

# Use them independently
cyberian message "Task 1" --port 3000
cyberian message "Task 2" --port 3001
cyberian message "Task 3" --port 3002
```

**Better solution:** Use server farms:

```yaml
# farm.yaml
base_port: 3000
servers:
  - name: agent1
    agent_type: claude
    directory: /tmp/agent1
    skip_permissions: true
  - name: agent2
    agent_type: claude
    directory: /tmp/agent2
    skip_permissions: true
  - name: agent3
    agent_type: claude
    directory: /tmp/agent3
    skip_permissions: true
```

```bash
cyberian farm start farm.yaml
```

See [Tutorial: Multi-Agent Farm](../tutorials/multi-agent-farm.md) for details.

## Restart a Server

**Problem:** You need to restart a server with clean state.

**Solution:**

```bash
# Stop the server
cyberian stop --port 3284

# Wait a moment
sleep 2

# Start again
cyberian server start claude --port 3284 --skip-permissions
```

**Example script:**

```bash
#!/bin/bash
PORT=3284

# Stop if running
if cyberian list-servers | grep -q "port $PORT"; then
  cyberian stop --port $PORT
  sleep 2
fi

# Start fresh
cyberian server start claude \
  --port $PORT \
  --dir /tmp/agent-workspace \
  --skip-permissions

echo "Server restarted on port $PORT"
```

## Different Agent Types

**Problem:** You want to use different agent types.

**Solution:**

```bash
# Claude
cyberian server start claude

# Aider
cyberian server start aider

# Cursor
cyberian server start cursor

# Goose
cyberian server start goose

# Custom
cyberian server start custom
```

Each agent type may have different capabilities and behavior.

## Logging and Debugging

**Problem:** You need to debug server issues.

**Solution:**

Check the server's working directory for logs:

```bash
# If you set --dir /tmp/agent
ls -la /tmp/agent/

# Look for log files
cat /tmp/agent/*.log
```

Check server status:

```bash
# Detailed status
cyberian status --port 3284

# Check if process is running
cyberian list-servers | grep 3284
```

## Related Guides

- [Send Messages](send-messages.md) - Interact with running servers
- [Tutorial: Getting Started](../tutorials/getting-started.md) - Basic server operations
- [Tutorial: Multi-Agent Farm](../tutorials/multi-agent-farm.md) - Manage multiple servers
- [Troubleshooting](troubleshooting.md) - Common server issues

## See Also

- [CLI Reference: server](../reference/cli-commands.md#server)
- [CLI Reference: stop](../reference/cli-commands.md#stop)
- [CLI Reference: list-servers](../reference/cli-commands.md#list-servers)
- [CLI Reference: status](../reference/cli-commands.md#status)

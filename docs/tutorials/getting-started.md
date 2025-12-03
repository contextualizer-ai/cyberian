# Getting Started with cyberian

**Time: 10 minutes**

This tutorial will guide you through installing cyberian and performing your first interactions with an AI agent via agentapi.

## Prerequisites

- Python 3.10 or later
- An agentapi-compatible agent installed (e.g., Claude Code, Aider, Cursor, Goose)

## Step 1: Install cyberian

Install cyberian using pip:

```bash
pip install cyberian
```

Verify the installation:

```bash
cyberian --help
```

You should see a list of available commands.

!!! tip "Using uvx"
    You can also run cyberian without installing it using `uvx`:
    ```bash
    uvx cyberian --help
    ```

## Step 2: Start an agentapi Server

Start a Claude agent server on port 3284:

```bash
cyberian server start claude --skip-permissions --port 3284 --dir /tmp/my-first-agent
```

Let's break down this command:

- `server start` - Start a new agentapi server
- `claude` - Use Claude as the agent type
- `--skip-permissions` - Don't prompt for tool permissions (auto-approve)
- `--port 3284` - Run on port 3284 (the default)
- `--dir /tmp/my-first-agent` - Use this directory as the working directory

!!! info "What just happened?"
    cyberian started an agentapi server in the background. The server is now running and waiting for messages at `http://localhost:3284`.

## Step 3: Check Server Status

Verify that your server is running:

```bash
cyberian status
```

You should see output like:

```json
{
  "status": "idle",
  "conversation_id": "...",
  "available": true
}
```

The `status: "idle"` means the agent is ready and waiting for work.

## Step 4: Send Your First Message

Send a simple message to the agent:

```bash
cyberian message "Write a hello world function in Python"
```

This sends the message and returns immediately (fire-and-forget mode).

## Step 5: View the Conversation

Get all messages from the conversation:

```bash
cyberian messages
```

You'll see a JSON array with all messages including:

- Your user message
- The agent's response
- Any tool calls the agent made

!!! tip "Viewing in Browser"
    You can also view the conversation in a web interface:
    ```bash
    open http://localhost:3284/chat
    ```

## Step 6: Use Synchronous Mode

Send a message and wait for the response:

```bash
cyberian message "What is 2 + 2?" --sync
```

With `--sync`, cyberian will:

1. Send your message
2. Poll the server until the agent finishes
3. Return the agent's response

You should see something like:

```
2 + 2 equals 4.
```

## Step 7: Get Recent Messages

Get just the last 3 messages:

```bash
cyberian messages --last 3
```

Or export to YAML format:

```bash
cyberian messages --format yaml --last 5
```

or CSV:

```bash
cyberian messages --format csv --last 5
```

!!! tip "Shorthand"
    You can also use `-f` instead of `--format`, and `-l` instead of `--last`
    ```bash
    cyberian messages -f csv -f 5
    ```

## Step 8: Stop the Server

When you're done, find the server:

```bash
cyberian list-servers
```

This shows all running agentapi servers with their PIDs and ports.

Stop the server by port:

```bash
cyberian stop --port 3284
```

Or by PID:

```bash
cyberian stop <PID>
```

Or all servers:

```bash
cyberian stop --all
```

!!! tip "Shorthand"
    You can omit the PID and the command will stop the current server
    ```bash
    cyberian server stop
    ```

## What You've Learned

Congratulations! You've learned how to:

- Install cyberian
- Start an agentapi server
- Send messages (fire-and-forget and synchronous)
- Check server status
- View conversation history
- Stop servers

## Next Steps

- **[Your First Workflow](first-workflow.md)** - Learn to write YAML workflows
- **[How-To: Send Messages](../how-to/send-messages.md)** - Advanced message sending patterns
- **[How-To: Manage Servers](../how-to/manage-servers.md)** - Server lifecycle management

## Troubleshooting

### Server won't start

Make sure the port isn't already in use:

```bash
cyberian list-servers
```

Try a different port:

```bash
cyberian server start claude --port 3285
```

### Connection refused

Check that the server is running:

```bash
cyberian status
```

Make sure you're using the correct port:

```bash
cyberian status --port 3284
```

### See Also

- [How-To: Troubleshooting](../how-to/troubleshooting.md) for more common issues

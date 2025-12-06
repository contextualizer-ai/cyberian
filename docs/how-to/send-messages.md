# How to Send Messages

This guide covers different patterns for sending messages to agents via cyberian.

## Fire-and-Forget Messages

**Problem:** You want to send a message without waiting for a response.

**Solution:**

```bash
cyberian message "Your prompt here"
```

The command returns immediately. The agent processes the message asynchronously.

**When to use:**

- Quick commands that don't need immediate feedback
- Starting long-running tasks
- Queueing multiple messages

**Example:**

```bash
# Start a long research task
cyberian message "Research quantum computing and write a comprehensive report to report.md"

# Check later
cyberian messages --last 1
```

## Synchronous Messages

**Problem:** You want to wait for the agent's response before continuing.

**Solution:**

```bash
cyberian message "What is 2 + 2?" --sync
```

This polls the server until the agent responds, then returns the last agent message.

**Options:**

```bash
# Custom timeout (default: 60 seconds)
cyberian message "Complex task" --sync --timeout 300

# Custom poll interval (default: 0.5 seconds)
cyberian message "Quick task" --sync --poll-interval 0.1
```

**When to use:**

- You need the response before proceeding
- Scripting that depends on agent output
- Interactive sessions

**Example:**

```bash
# Get answer and use it
ANSWER=$(cyberian message "What is the capital of France?" --sync)
echo "Answer: $ANSWER"
```

## Custom Server Location

**Problem:** You need to connect to a server on a different host/port.

**Solution:**

```bash
# Different port
cyberian message "Hello" --port 8080

# Different host
cyberian message "Hello" --host example.com --port 3284

# Using shorthand
cyberian message "Hello" -H example.com -P 8080
```

**Example:**

```bash
# Connect to remote server
cyberian message "Check system status" \
  --host agent.mycompany.com \
  --port 9000 \
  --sync
```

## Message Types

**Problem:** You need to send non-user messages (system, assistant, etc.).

**Solution:**

```bash
# User message (default)
cyberian message "Hello"

# System message
cyberian message "You are a helpful assistant" --type system

# Using shorthand
cyberian message "Context info" -t system
```

**When to use:**

- Setting context with system messages
- Simulating multi-turn conversations
- Testing agent behavior with different message types

## Handling Timeouts

**Problem:** The agent takes longer than expected and times out.

**Solution:**

```bash
# Increase timeout for long-running tasks
cyberian message "Perform extensive analysis" --sync --timeout 600

# Or use fire-and-forget and poll manually
cyberian message "Long task"
sleep 10
cyberian status
cyberian messages --last 1
```

**Example:**

```bash
# Long research with custom timeout
cyberian message "Deep research on AI safety" \
  --sync \
  --timeout 1800 \
  --poll-interval 2.0
```

## Error Handling in Scripts

**Problem:** You need to handle errors gracefully in bash scripts.

**Solution:**

```bash
#!/bin/bash

# Send message and capture exit code
if cyberian message "Test" --sync --timeout 30; then
  echo "Success!"
  cyberian messages --last 1
else
  echo "Error: Agent timed out or failed"
  exit 1
fi
```

**Robust example:**

```bash
#!/bin/bash
set -e  # Exit on error

# Check server is up
if ! cyberian status > /dev/null 2>&1; then
  echo "Server not running, starting..."
  cyberian server start claude --skip-permissions
  sleep 5
fi

# Send message with timeout
if cyberian message "Your task" --sync --timeout 120; then
  echo "Task completed"
else
  echo "Task failed or timed out"
  exit 1
fi
```

## Batch Message Sending

**Problem:** You need to send multiple messages in sequence.

**Solution:**

```bash
# Sequential tasks
cyberian message "Task 1: Research topic X" --sync
cyberian message "Task 2: Summarize findings from Task 1" --sync
cyberian message "Task 3: Create presentation from summary" --sync
```

**Better solution:** Use workflows for complex multi-step tasks:

```yaml
# tasks.yaml
name: batch-tasks
subtasks:
  task1:
    instructions: "Research topic X. COMPLETION_STATUS: COMPLETE"
  task2:
    instructions: "Summarize findings. COMPLETION_STATUS: COMPLETE"
  task3:
    instructions: "Create presentation. COMPLETION_STATUS: COMPLETE"
```

```bash
cyberian run tasks.yaml
```

## Message Output Formatting

**Problem:** You want to extract just the text response.

**Solution:**

```bash
# Sync mode returns just the agent's text
RESPONSE=$(cyberian message "Question?" --sync)
echo "$RESPONSE"

# Or parse JSON from messages command
cyberian messages --last 1 --format json | jq -r '.[0].content'
```

**Example:**

```bash
# Get answer and save to file
cyberian message "Explain quantum entanglement" --sync > explanation.txt

# Use in another command
SUMMARY=$(cyberian message "Summarize: $(cat data.txt)" --sync)
echo "$SUMMARY" > summary.txt
```

## Rate Limiting

**Problem:** You need to control message rate to avoid overwhelming the agent.

**Solution:**

```bash
# Send messages with delays
for msg in "Task 1" "Task 2" "Task 3"; do
  cyberian message "$msg"
  sleep 5  # Wait 5 seconds between messages
done
```

## Related Guides

- [Manage Servers](manage-servers.md) - Server lifecycle management
- [Write Workflows](write-workflows.md) - Multi-step task automation
- [Troubleshooting](troubleshooting.md) - Common issues with messages

## See Also

- [CLI Reference: message](../reference/cli-commands.md#message)
- [CLI Reference: messages](../reference/cli-commands.md#messages)
- [Explanation: Architecture](../explanation/architecture.md)

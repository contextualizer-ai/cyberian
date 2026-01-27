# Troubleshooting

This guide covers common problems and their solutions.

## Connection Issues

### Server Not Responding

**Problem:** `cyberian status` fails with connection error.

**Symptoms:**

```
Error: Connection refused
```

**Solutions:**

1. **Check if server is running:**

```bash
cyberian list-servers
```

If no servers are listed, start one:

```bash
cyberian server start claude --skip-permissions
```

2. **Verify port:**

```bash
# Make sure you're checking the right port
cyberian status --port 3284
```

3. **Check firewall:**

Ensure localhost connections on the port are allowed.

4. **Wait for startup:**

Server might still be starting:

```bash
sleep 3
cyberian status
```

### Wrong Port

**Problem:** Server is running but on different port.

**Solution:**

```bash
# Find all running servers
cyberian list-servers

# Look for agentapi processes and their ports
# Connect to the correct port
cyberian status --port <correct_port>
```

### Cannot Connect to Remote Server

**Problem:** Can't connect to server on another machine.

**Solutions:**

1. **Check CORS settings:**

Server must be started with appropriate CORS configuration:

```bash
cyberian server start claude \
  --allowed-origins "http://your-client-host:port" \
  --allowed-hosts "your-server-host"
```

2. **Check network:**

```bash
# Test basic connectivity
ping server-hostname

# Test port is open
nc -zv server-hostname 3284
```

3. **Firewall:**

Ensure the port is open on the server's firewall.

## Timeout Issues

### Message Timeouts

**Problem:** Messages timeout before agent completes.

**Symptoms:**

```
Error: Timeout waiting for agent response
```

**Solutions:**

1. **Increase timeout:**

```bash
# Default is 60 seconds, increase as needed
cyberian message "Complex task" --sync --timeout 300
```

2. **Use fire-and-forget:**

```bash
# Don't wait for response
cyberian message "Long running task"

# Check later
cyberian messages --last 1
```

3. **Check agent is working:**

```bash
# Monitor status
watch -n 2 cyberian status
```

Status should change from `idle` → `busy` → `idle`.

### Workflow Timeouts

**Problem:** Workflow tasks timeout.

**Solution:**

```bash
# Increase per-task timeout (default: 300 seconds)
cyberian run workflow.yaml --timeout 600
```

Or break tasks into smaller steps:

```yaml
# Instead of one large task
subtasks:
  big_task:
    instructions: "Do everything. COMPLETION_STATUS: COMPLETE"

# Break into smaller tasks
subtasks:
  step1:
    instructions: "Do part 1. COMPLETION_STATUS: COMPLETE"
  step2:
    instructions: "Do part 2. COMPLETION_STATUS: COMPLETE"
  step3:
    instructions: "Do part 3. COMPLETION_STATUS: COMPLETE"
```

## Workflow Issues

### Task Never Completes

**Problem:** Workflow hangs, task never finishes.

**Symptoms:**

cyberian waits indefinitely, agent shows `busy` status.

**Cause:** Agent didn't output `COMPLETION_STATUS: COMPLETE`.

**Solutions:**

1. **Check instructions:**

Ensure `COMPLETION_STATUS: COMPLETE` is in the instructions:

```yaml
subtasks:
  task:
    instructions: |
      Do something.
      COMPLETION_STATUS: COMPLETE  # Must include this!
```

2. **Make it explicit:**

```yaml
subtasks:
  task:
    instructions: |
      Do your task.

      When done, you MUST output exactly:
      COMPLETION_STATUS: COMPLETE
```

3. **Check agent output:**

```bash
# View conversation
cyberian messages --last 10
```

Look for what the agent actually output.

### Template Variables Not Rendering

**Problem:** Workflow has literal `{{variable}}` instead of value.

**Symptoms:**

```
Instructions contain: "Research {{query}}"
```

**Cause:** Parameter not provided or misspelled.

**Solutions:**

1. **Check parameter name:**

```yaml
params:
  query:  # Must match exactly
    range: string
    required: true
```

```bash
# Must use exact parameter name
cyberian run workflow.yaml --param query="value"
```

2. **Check parameter is required:**

```yaml
params:
  optional_param:
    range: string
    required: false

subtasks:
  task:
    instructions: |
      {% if optional_param %}
      Use: {{optional_param}}
      {% else %}
      No parameter provided
      {% endif %}
      COMPLETION_STATUS: COMPLETE
```

3. **Test template rendering:**

Add debug output:

```yaml
subtasks:
  debug:
    instructions: |
      Debug info:
      - query: {{query}}
      - defined: {% if query is defined %}YES{% else %}NO{% endif %}
      COMPLETION_STATUS: COMPLETE
```

### Success Criteria Always Fails

**Problem:** Success criteria keeps retrying and failing.

**Symptoms:**

```
Retry 1/3: Success criteria not met
Retry 2/3: Success criteria not met
Retry 3/3: Success criteria not met
Error: Task failed after max retries
```

**Solutions:**

1. **Debug the criteria:**

```yaml
success_criteria:
  python: |
    import os
    import sys

    # Debug output
    print("Checking file: results.txt", file=sys.stderr)
    print("CWD:", os.getcwd(), file=sys.stderr)
    print("Files:", os.listdir('.'), file=sys.stderr)

    # Actual check
    result = os.path.exists("results.txt")
    print("Result:", result, file=sys.stderr)
  max_retries: 1
```

2. **Check working directory:**

Success criteria runs in the workflow's working directory:

```bash
cyberian run workflow.yaml --dir /tmp/workspace
```

Ensure files are created there.

3. **Simplify the check:**

```yaml
# Complex check that might fail
success_criteria:
  python: |
    with open("output.json") as f:
      data = json.load(f)
    result = data['status'] == 'success'

# Simpler check
success_criteria:
  python: |
    import os
    result = os.path.exists("output.json")
  max_retries: 2
```

## Server Issues

### Port Already in Use

**Problem:** Can't start server, port is occupied.

**Symptoms:**

```
Error: Address already in use
```

**Solutions:**

1. **Find what's using the port:**

```bash
cyberian list-servers
```

2. **Use different port:**

```bash
cyberian server start claude --port 3285
```

3. **Stop existing server:**

```bash
cyberian stop --port 3284
```

### Multiple Servers Running

**Problem:** Too many servers, system is slow.

**Solution:**

```bash
# List all servers
cyberian list-servers

# Stop them
cyberian list-servers | grep agentapi | awk '{print $1}' | while read pid; do
  cyberian stop "$pid"
done
```

### Server Crashes

**Problem:** Server stops unexpectedly.

**Solutions:**

1. **Check logs:**

Look in the server's working directory for log files.

2. **Check system resources:**

```bash
# Memory usage
free -h

# CPU usage
top
```

Agent might be running out of memory.

3. **Restart with fresh state:**

```bash
cyberian stop --port 3284
sleep 2
cyberian server start claude --port 3284 --dir /tmp/fresh-workspace
```

## Permission Issues

### Permission Denied Errors

**Problem:** Agent can't access files or directories.

**Solutions:**

1. **Check directory permissions:**

```bash
# Ensure directory is writable
chmod 755 /path/to/workdir
```

2. **Use accessible directory:**

```bash
# Use /tmp for testing
cyberian server start claude --dir /tmp/test-workspace
```

3. **Check file ownership:**

```bash
ls -la /path/to/workdir
```

Ensure your user owns the files.

## Farm Issues

### Farm Won't Start

**Problem:** `cyberian farm start` fails.

**Solutions:**

1. **Check YAML syntax:**

```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('farm.yaml'))"
```

2. **Check directories exist:**

```yaml
servers:
  - name: worker1
    directory: /tmp/worker1  # Must be writable
```

```bash
# Create directories first
mkdir -p /tmp/worker1 /tmp/worker2
```

3. **Check ports available:**

```yaml
base_port: 4000  # Ensure 4000, 4001, etc. are free
```

```bash
cyberian list-servers  # Check for conflicts
```

### Template Directory Not Copying

**Problem:** Files from `template_directory` don't appear.

**Solutions:**

1. **Check path is relative to farm config:**

```yaml
# If farm.yaml is in /home/user/farms/
template_directory: my-template  # Looks in /home/user/farms/my-template
```

2. **Use absolute path:**

```yaml
template_directory: /absolute/path/to/template
```

3. **Check directory exists:**

```bash
ls -la farm-template/
```

## Template Issues

### Jinja2 Syntax Errors

**Problem:** Workflow fails with template error.

**Symptoms:**

```
Error: Jinja2 syntax error at line 5
```

**Solutions:**

1. **Check for unclosed tags:**

```yaml
# Bad
instructions: |
  {% if condition %}
  Do something
  # Missing {% endif %}

# Good
instructions: |
  {% if condition %}
  Do something
  {% endif %}
```

2. **Check for typos:**

```yaml
# Bad
{% fi condition %}  # Should be 'if'

# Good
{% if condition %}
```

3. **Test templates:**

Use Python to test:

```bash
python3 << 'EOF'
from jinja2 import Template
t = Template("{% if x %}Y{% endif %}")
print(t.render(x=True))
EOF
```

## Codex-Specific Issues

### First Message Ignored (Welcome Banner)

**Problem:** Codex shows startup banner instead of processing the first task.

**Symptoms:**

```
Welcome to OpenAI Codex!
Available commands:
/init - Initialize project
/approvals - Configure approval settings
```

Instead of actual task output.

**Cause:** Fresh/untrusted directories trigger Codex's welcome flow.

**Solutions:**

1. **Use --skip-permissions:**

```bash
cyberian server start codex --skip-permissions
```

2. **Configure config.toml:**

```toml
# ~/.codex/config.toml
approval_policy = "never"
sandbox_mode = "danger-full-access"
```

3. **Mark directory as trusted:**

```toml
# ~/.codex/config.toml
[projects."/your/workspace"]
trust_level = "trusted"
```

4. **cyberian auto-retry:**

cyberian automatically detects the welcome banner and resends the first message.

### Server Startup Timeout

**Problem:** "Server did not become ready within 30s" with Codex.

**Cause:** Codex takes longer to initialize than Claude.

**Note:** cyberian automatically extends timeout to 120s for Codex.

**If still failing:**

1. **Check Codex installation:**

```bash
which codex
codex --version
```

2. **Check agentapi logs:**

```bash
cat /path/to/workspace/agentapi_stderr.log
```

3. **Start manually to debug:**

```bash
agentapi server codex --port 3284 -- --dangerously-bypass-approvals-and-sandbox
```

### Codex Environment Mismatch

**Problem:** Codex works in terminal but not when spawned by cyberian.

**Symptoms:**

- Server starts but Codex process fails
- "codex: command not found" in logs
- Different behavior than manual execution

**Cause:** PATH or environment differs when spawned as subprocess.

**Solutions:**

1. **Check PATH:**

```bash
# Where is codex?
which codex

# Is it in a standard location?
echo $PATH
```

2. **Use absolute path (if needed):**

Ensure codex binary is in a standard PATH location, or configure shell environment:

```toml
# ~/.codex/config.toml
[shell_environment_policy]
inherit = "all"
```

3. **Check agentapi can find codex:**

```bash
# Test agentapi directly
agentapi server codex --port 9999
```

### Approval Prompts Block Workflow

**Problem:** Workflow hangs, waiting for interactive approval.

**Symptoms:**

- Status shows `waiting` indefinitely
- No output from agent
- Works fine when running codex manually

**Cause:** Codex approval policy requires user input.

**Solutions:**

1. **Use --skip-permissions flag:**

```bash
cyberian server start codex --skip-permissions
```

2. **Set approval_policy in config.toml:**

```toml
# ~/.codex/config.toml
approval_policy = "never"
```

3. **Use automation profile:**

```toml
# ~/.codex/config.toml
profile = "automation"

[profiles.automation]
approval_policy = "never"
sandbox_mode = "danger-full-access"
```

### Sandbox Blocks File Operations

**Problem:** Codex can't read/write files despite correct instructions.

**Symptoms:**

- "Permission denied" errors
- File operations silently fail
- Works in terminal but not via cyberian

**Cause:** Sandbox mode restricting filesystem access.

**Solutions:**

1. **Use full access mode:**

```toml
# ~/.codex/config.toml
sandbox_mode = "danger-full-access"
```

2. **Or allow specific paths:**

```toml
# ~/.codex/config.toml
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
writable_roots = ["/tmp/cyberian", "~/projects"]
```

3. **Verify directory permissions:**

```bash
ls -la /path/to/workspace
# Ensure user has write access
```

### Different Behavior in Fresh Directories

**Problem:** Workflow works in existing project but fails in new directory.

**Cause:** Codex trusts established projects but not fresh directories.

**Solutions:**

1. **Pre-create and trust the directory:**

```bash
mkdir -p /path/to/workspace
```

```toml
# ~/.codex/config.toml
[projects."/path/to/workspace"]
trust_level = "trusted"
```

2. **Use existing trusted directory:**

```bash
cyberian run workflow.yaml --dir ~/existing-project
```

3. **Initialize project first:**

```bash
# Create basic project structure
mkdir -p workspace && cd workspace
git init
echo "# Project" > README.md
```

### Codex Model Issues

**Problem:** Wrong model being used or model errors.

**Solutions:**

1. **Specify model in config.toml:**

```toml
# ~/.codex/config.toml
model = "gpt-4-turbo"
```

2. **Check API key:**

Ensure `OPENAI_API_KEY` is set:

```bash
echo $OPENAI_API_KEY
```

3. **Check model availability:**

Some models require specific access levels.

## Debug Techniques

### Enable Verbose Output

Add debug instructions:

```yaml
subtasks:
  debug:
    instructions: |
      List current directory:
      ls -la

      Show environment:
      env

      COMPLETION_STATUS: COMPLETE
```

### Check Conversation History

```bash
# See all messages
cyberian messages

# Last 5 messages
cyberian messages --last 5

# As YAML for readability
cyberian messages --format yaml --last 10
```

### Monitor Server Status

```bash
# Watch status change
watch -n 1 cyberian status

# Or in a loop
while true; do
  cyberian status
  sleep 2
done
```

## Getting Help

If you're still stuck:

1. **Check the logs** in the agent's working directory
2. **Simplify** - Create minimal reproduction
3. **File an issue** at [https://github.com/monarch-initiative/cyberian/issues](https://github.com/monarch-initiative/cyberian/issues)

Include:

- Your command
- The error message
- Relevant workflow YAML
- Output of `cyberian list-servers` and `cyberian status`

## Related Guides

- [Send Messages](send-messages.md) - Message patterns
- [Manage Servers](manage-servers.md) - Server lifecycle
- [Write Workflows](write-workflows.md) - Workflow authoring

## See Also

- [Reference: CLI Commands](../reference/cli-commands.md)
- [Explanation: Architecture](../explanation/architecture.md)

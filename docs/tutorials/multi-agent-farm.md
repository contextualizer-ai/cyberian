# Running a Multi-Agent Farm

**Time: 20 minutes**

This tutorial will teach you how to set up and manage a "farm" of multiple agent servers running in parallel, coordinated through cyberian.

## Prerequisites

- Completed [Getting Started](getting-started.md) and [Your First Workflow](first-workflow.md)
- Understanding of YAML syntax
- Multiple CPU cores (recommended for parallel work)

## What is a Server Farm?

A server farm is a collection of multiple agentapi servers running simultaneously, each:

- On its own port
- With its own working directory
- Potentially with different configurations
- Coordinated through a single YAML file

Farms enable parallel agent work and multi-agent orchestration.

## Step 1: Create a Simple Farm Configuration

Create a file called `my-farm.yaml`:

```yaml
base_port: 4000

servers:
  - name: worker1
    agent_type: claude
    directory: /tmp/worker1
    skip_permissions: true

  - name: worker2
    agent_type: claude
    directory: /tmp/worker2
    skip_permissions: true
```

Let's break this down:

- `base_port: 4000` - First server gets port 4000, second gets 4001, etc.
- `servers` - List of server configurations
  - `name` - Logical name for the server
  - `agent_type` - Agent to use (claude, aider, cursor, goose, custom)
  - `directory` - Working directory for this server
  - `skip_permissions` - Auto-approve tool permissions

## Step 2: Start the Farm

Start all servers:

```bash
cyberian farm start my-farm.yaml
```

cyberian will:

1. Create working directories if they don't exist
2. Start worker1 on port 4000
3. Start worker2 on port 4001
4. Report the status of each server

You should see output like:

```
Starting farm with 2 servers...
✓ worker1 started on port 4000
✓ worker2 started on port 4001
Farm started successfully!
```

## Step 3: Verify the Farm is Running

List all running servers:

```bash
cyberian list-servers
```

You should see both workers running.

Check individual server status:

```bash
# Check worker1
cyberian status --port 4000

# Check worker2
cyberian status --port 4001
```

## Step 4: Send Work to Different Servers

Send different tasks to each server:

```bash
# Task for worker1
cyberian message "Research Python async/await patterns. Save findings to research.md" \
  --port 4000 --sync

# Task for worker2
cyberian message "Research Python multiprocessing. Save findings to research.md" \
  --port 4001 --sync
```

Each server works independently in its own directory!

Check the results:

```bash
cat /tmp/worker1/research.md
cat /tmp/worker2/research.md
```

## Step 5: Use Template Directories

Template directories let you copy configuration files to each server. Create a farm template:

```bash
# Create template directory
mkdir -p farm-template/.claude

# Add project instructions
cat > farm-template/.claude/CLAUDE.md << 'EOF'
# Agent Instructions

- Use test-driven development
- Write concise, clear documentation
- Follow PEP 8 style guidelines
EOF

# Add other config files
echo "*.pyc" > farm-template/.gitignore
```

Update your farm configuration to use the template:

```yaml
base_port: 4000
template_directory: farm-template

servers:
  - name: worker1
    agent_type: claude
    directory: /tmp/worker1
    skip_permissions: true

  - name: worker2
    agent_type: claude
    directory: /tmp/worker2
    skip_permissions: true
```

Note: You can also specify `template_directory` per-server if needed.

Start the farm:

```bash
cyberian farm start my-farm.yaml
```

Verify templates were copied:

```bash
ls -la /tmp/worker1/.claude/
ls -la /tmp/worker2/.claude/
```

Both should have the `CLAUDE.md` file!

## Step 6: Explicit Port Assignment

Override auto-assignment with explicit ports:

```yaml
base_port: 4000

servers:
  - name: worker1
    agent_type: claude
    directory: /tmp/worker1
    port: 5000  # Explicit port
    skip_permissions: true

  - name: worker2
    agent_type: claude
    directory: /tmp/worker2
    # No explicit port, uses base_port+1 = 4001
    skip_permissions: true

  - name: worker3
    agent_type: claude
    directory: /tmp/worker3
    port: 6000  # Another explicit port
    skip_permissions: true
```

This gives you:

- worker1 on port 5000 (explicit)
- worker2 on port 4001 (auto-assigned)
- worker3 on port 6000 (explicit)

## Step 7: CORS Configuration

Configure CORS for web access:

```yaml
base_port: 4000

servers:
  - name: worker1
    agent_type: claude
    directory: /tmp/worker1
    skip_permissions: true
    allowed_origins: "https://myapp.com,https://staging.myapp.com"
    allowed_hosts: "myapp.com,staging.myapp.com"
```

This allows your web app to connect to the agentapi servers.

## Step 8: Stopping the Farm

Stop individual servers:

```bash
cyberian stop --port 4000
cyberian stop --port 4001
```

Or stop all servers at once:

```bash
# Get all PIDs
cyberian list-servers

# Stop each one
cyberian stop <PID1>
cyberian stop <PID2>
```

!!! tip "Scripting Shutdown"
    You can script farm shutdown:
    ```bash
    cyberian list-servers | grep agentapi | awk '{print $2}' | xargs -I {} cyberian stop {}
    ```

## Real-World Example: Parallel Research

Create a farm for parallel research:

```yaml
base_port: 5000

servers:
  - name: biology-researcher
    agent_type: claude
    directory: /tmp/research/biology
    skip_permissions: true

  - name: physics-researcher
    agent_type: claude
    directory: /tmp/research/physics
    skip_permissions: true

  - name: chemistry-researcher
    agent_type: claude
    directory: /tmp/research/chemistry
    skip_permissions: true
```

Send parallel research tasks:

```bash
# Start farm
cyberian farm start research-farm.yaml

# Parallel research tasks
cyberian message "Research CRISPR gene editing" --port 5000 --sync &
cyberian message "Research quantum entanglement" --port 5001 --sync &
cyberian message "Research carbon nanotubes" --port 5002 --sync &

# Wait for all to complete
wait

# Collect results
cat /tmp/research/biology/*.md
cat /tmp/research/physics/*.md
cat /tmp/research/chemistry/*.md
```

## What You've Learned

You now know how to:

- Create farm configuration files
- Start multiple agent servers simultaneously
- Use auto-assigned and explicit ports
- Copy template files to server directories
- Send work to specific servers
- Configure CORS for web access
- Stop farm servers

## Next Steps

- **[How-To: Write Workflows](../how-to/write-workflows.md)** - Combine workflows with farms
- **[Explanation: Architecture](../explanation/architecture.md)** - How farms work internally
- **[Reference: Configuration](../reference/configuration.md)** - Complete farm config reference

## Tips

!!! tip "Resource Management"
    Each server consumes memory and CPU. Monitor system resources when running large farms.

!!! tip "Port Conflicts"
    If ports are already in use, cyberian will fail to start. Use `cyberian list-servers` to check.

!!! tip "Log Files"
    Each server logs to its working directory. Check logs for debugging.

!!! warning "Cleanup"
    Remember to stop servers when done! Running servers consume resources.

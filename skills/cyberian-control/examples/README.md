# Cyberian Control Skill Examples

This directory contains example workflows and scripts demonstrating multi-agent coordination with cyberian.

## Shell Scripts

### simple-delegation.sh

Delegate a single task to a remote agent and wait for completion.

```bash
./simple-delegation.sh localhost 3284 "Write a function to calculate fibonacci numbers"
```

**Arguments:**
1. Host (default: localhost)
2. Port (default: 3284)
3. Task description (default: "Write a function to calculate fibonacci numbers")

### parallel-research.sh

Run parallel research tasks across multiple agents.

```bash
./parallel-research.sh "quantum computing" 5000
```

**Arguments:**
1. Research query (default: "artificial intelligence")
2. Base port (default: 5000, uses ports 5000-5002)

**Prerequisites:** Three agents must be running on consecutive ports starting at base_port.

### monitor-farm.sh

Monitor the status of a farm of agents in real-time.

```bash
./monitor-farm.sh 4000 3
```

**Arguments:**
1. Base port (default: 4000)
2. Number of agents (default: 3)

Monitors agents on ports base_port through base_port+num_agents-1.

## Workflow Files

### multi-agent-research.yaml

Coordinate multiple agents to research a topic from different perspectives.

```bash
cyberian run multi-agent-research.yaml \
  -p query="machine learning" \
  -d ./research-output
```

**What it does:**
1. Historical research (one agent)
2. Current state analysis (one agent)
3. Future trends research (one agent)
4. Synthesis of all findings (one agent)

### delegated-coding.yaml

Delegate software development tasks to specialized agents.

```bash
cyberian run delegated-coding.yaml \
  -p feature="user authentication" \
  -d ./project-output
```

**What it does:**
1. Design architecture
2. Implement backend (could be delegated to separate agent)
3. Implement frontend (could be delegated to separate agent)
4. Write tests
5. Create documentation

### farm-config.yaml

Configuration file for starting a farm of specialized agents.

```bash
cyberian farm start farm-config.yaml
```

**What it creates:**
- Researcher agent (port 5000)
- Coder agent (port 5001)
- Reviewer agent (port 5002)
- Writer agent (port 6000)

Each agent gets its own working directory and can have specialized configuration via template directories.

## Setting Up Template Directories

Template directories allow you to configure each agent with specific instructions:

```bash
# Create template for researcher agent
mkdir -p templates/researcher/.claude
cat > templates/researcher/.claude/CLAUDE.md << 'EOF'
# Research Agent Instructions
- Focus on comprehensive information gathering
- Cite sources
- Be thorough and analytical
EOF

# Create template for coder agent
mkdir -p templates/coder/.claude
cat > templates/coder/.claude/CLAUDE.md << 'EOF'
# Coder Agent Instructions
- Write clean, well-documented code
- Follow best practices
- Include tests
EOF
```

## Common Patterns

### Pattern 1: Sequential Workflow with Handoffs

```yaml
subtasks:
  research:
    instructions: |
      Research the topic. Save to RESEARCH.md.
      COMPLETION_STATUS: COMPLETE

  implement:
    instructions: |
      Read RESEARCH.md and implement the solution.
      COMPLETION_STATUS: COMPLETE
```

### Pattern 2: Parallel Tasks (Requires Farm)

```bash
# Start farm with multiple agents
cyberian farm start farm-config.yaml

# Send tasks to different agents in parallel
cyberian message "Task 1" -P 5000 &
cyberian message "Task 2" -P 5001 &
cyberian message "Task 3" -P 5002 &
wait
```

### Pattern 3: Iterative Refinement

```yaml
subtasks:
  iterate:
    instructions: |
      Improve the solution. When perfect, yield: REFINEMENT_COMPLETE

    loop_until:
      status: REFINEMENT_COMPLETE
```

## Tips

1. **Use meaningful working directories** - Keep each agent's workspace isolated
2. **Set appropriate timeouts** - Complex tasks need more time
3. **Monitor agent status** - Check `cyberian status` before sending new tasks
4. **Retrieve conversation history** - Use `cyberian messages` to see what agents have done
5. **Use template directories** - Share configuration across farm agents
6. **Clean up** - Stop servers when done: `cyberian stop -p PORT`

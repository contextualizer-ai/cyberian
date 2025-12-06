# Design Decisions

This document explains the rationale behind key design choices in cyberian.

## Why YAML for Workflows?

### The Decision

Workflows are defined in YAML rather than JSON, Python, or a DSL.

### Rationale

**Human-readable and writable:**

```yaml
# Clear, minimal syntax
name: my-workflow
subtasks:
  research:
    instructions: "Research the topic"
```

vs JSON:

```json
{
  "name": "my-workflow",
  "subtasks": {
    "research": {
      "instructions": "Research the topic"
    }
  }
}
```

**Comments supported:**

```yaml
# This task handles data processing
subtasks:
  process:
    instructions: "Process data"
```

**Multi-line strings:**

```yaml
instructions: |
  This is a long instruction
  that spans multiple lines
  and is easy to read
```

**Standard format:**

- Widely known
- Good editor support
- Existing tools for validation

### Trade-offs

**Advantages:**

- Readable
- Concise
- Comments
- Multi-line strings

**Disadvantages:**

- Less strict than JSON
- Whitespace significant
- Type coercion can surprise

**Alternatives considered:**

- **JSON** - Too verbose, no comments
- **TOML** - Good, but less common
- **Python DSL** - Too much power, requires Python knowledge
- **Custom DSL** - Reinventing the wheel

## Why Jinja2 for Templates?

### The Decision

Template variables use Jinja2 syntax (`{{variable}}`) rather than string interpolation or custom syntax.

### Rationale

**Powerful and familiar:**

```yaml
instructions: |
  {% if environment == "production" %}
  Deploy carefully!
  {% else %}
  Deploy freely
  {% endif %}
```

**Rich feature set:**

- Variables: `{{name}}`
- Conditionals: `{% if %}`
- Loops: `{% for %}`
- Filters: `{{name | upper}}`
- Tests: `{% if x is defined %}`

**Widely known:**

- Used in Ansible, Flask, Django
- Good documentation
- Familiar to many developers

### Trade-offs

**Advantages:**

- Powerful
- Proven
- Well-documented
- Extensive features

**Disadvantages:**

- Can be complex
- Learning curve
- Possible to write unmaintainable templates

**Alternatives considered:**

- **String formatting** (`f"{variable}"`) - Too limited
- **Custom syntax** (`$variable`) - Reinventing the wheel
- **No templating** - Not flexible enough

## Why Synchronous Polling?

### The Decision

Synchronous mode (`--sync`) polls the server repeatedly rather than using webhooks or async notification.

### Rationale

**Simple implementation:**

```python
while True:
    status = get_status()
    if status == "idle":
        return get_last_message()
    sleep(poll_interval)
```

**No infrastructure needed:**

- No webhook server
- No message queue
- No persistent connection

**Works everywhere:**

- Behind firewalls
- On localhost
- In containers
- No special networking

**Predictable behavior:**

- Easy to debug
- Easy to understand
- Easy to timeout

### Trade-offs

**Advantages:**

- Simple
- No infrastructure
- Works anywhere
- Easy to debug

**Disadvantages:**

- CPU overhead (minimal)
- Slightly slower response
- Network traffic (local, negligible)

**Alternatives considered:**

- **Webhooks** - Requires infrastructure
- **WebSockets** - More complex, persistent connection
- **Server-sent events** - One-way, still needs setup
- **Message queue** - Overkill for single-user tool

**Optimization:**

Polling interval is configurable:

```bash
# Responsive (polls every 100ms)
cyberian message "Quick task" --sync --poll-interval 0.1

# Efficient (polls every 2s)
cyberian message "Long task" --sync --poll-interval 2.0
```

## Why Recursive Task Trees?

### The Decision

Tasks can contain subtasks, which can contain subtasks, ad infinitum (Russian dolls).

### Rationale

**Natural hierarchy:**

```yaml
project:
  setup:
    install_deps: ...
    configure: ...
  build:
    compile: ...
    test: ...
  deploy: ...
```

Matches how humans think about projects.

**Composable:**

```yaml
# Reusable pattern
python_setup: &python_setup
  install_deps:
    instructions: "pip install -r requirements.txt"
  configure:
    instructions: "Setup config"

# Use in multiple workflows
project1:
  setup: *python_setup
project2:
  setup: *python_setup
```

**Scalable complexity:**

```yaml
# Simple
workflow:
  task1: ...
  task2: ...

# Complex
workflow:
  phase1:
    stage1:
      step1: ...
      step2: ...
    stage2: ...
  phase2: ...
```

### Trade-offs

**Advantages:**

- Hierarchical organization
- Infinite nesting
- Composable
- Intuitive

**Disadvantages:**

- Can be over-nested
- Harder to visualize deep trees

**Alternatives considered:**

- **Flat list** - Simple but loses organization
- **DAG (directed acyclic graph)** - More powerful but complex
- **State machine** - Powerful but harder to understand

## Why Explicit Completion Status?

### The Decision

Tasks must output `COMPLETION_STATUS: COMPLETE` rather than relying on agent idle detection.

### Rationale

**Unambiguous completion:**

```
Agent: "I'm working on it..."
[Goes idle - is it done or stuck?]
```

vs

```
Agent: "All done!"
       COMPLETION_STATUS: COMPLETE
[Goes idle - clearly complete]
```

**Supports loops:**

```yaml
loop_until:
  status: CONVERGED

# Agent can signal different statuses
COMPLETION_STATUS: CONTINUE  # Keep going
COMPLETION_STATUS: CONVERGED  # Stop looping
```

**Predictable behavior:**

- No guessing if agent is done
- No false positives
- Clear signal

### Trade-offs

**Advantages:**

- Unambiguous
- Supports loops
- Predictable
- Testable

**Disadvantages:**

- Requires discipline
- Agent must remember to output it
- Manual work for user

**Alternatives considered:**

- **Idle detection** - Ambiguous
- **Timeout-based** - Unreliable
- **LLM parsing** - Parse agent output to detect completion - Too fragile

## Why No Built-in Parallel Execution?

### The Decision

Tasks execute sequentially (depth-first). No parallel execution within a workflow.

### Rationale

**Simpler implementation:**

```python
for task in tasks:
    execute(task)  # Simple loop
```

vs parallel:

```python
async def execute_parallel():
    await asyncio.gather(*tasks)  # Complexity
```

**Predictable ordering:**

```yaml
subtasks:
  task1: ...  # Always runs first
  task2: ...  # Always runs second
```

**Single-agent model:**

- Most workflows use one agent
- Agent can't truly parallelize
- Sequential is natural

**Workaround exists:**

```bash
# Use server farms for parallelism
cyberian run task1.yaml --port 4000 &
cyberian run task2.yaml --port 4001 &
cyberian run task3.yaml --port 4002 &
wait
```

### Trade-offs

**Advantages:**

- Simple
- Predictable
- Easy to debug
- Matches agent model

**Disadvantages:**

- No parallelism
- Longer execution time
- Must use workaround for parallel work

**Future consideration:**

Parallel execution could be added:

```yaml
subtasks:
  parallel_group:
    parallel: true  # Future feature
    subtasks:
      task1: ...
      task2: ...
      task3: ...
```

## Why Stateless CLI?

### The Decision

cyberian doesn't maintain configuration files or persistent state.

### Rationale

**Unix philosophy:**

- Do one thing well
- Read from stdin, write to stdout
- Compose with other tools

**No config to manage:**

```bash
# No ~/.cyberianrc or config.yaml
# Everything specified in command
cyberian run workflow.yaml --port 3284
```

**Reproducible:**

```bash
# Same command = same result
cyberian message "Hello" --port 3284
```

**Simple mental model:**

- No hidden state
- No config to debug
- What you see is what you get

### Trade-offs

**Advantages:**

- Simple
- Reproducible
- No hidden state
- Unix philosophy

**Disadvantages:**

- Verbose commands
- Must specify --port repeatedly
- No defaults per-project

**Partial mitigation:**

```bash
# Use shell aliases
alias cy='cyberian --port 3284'
cy message "Hello"

# Or environment variables (future)
export CYBERIAN_PORT=3284
cyberian message "Hello"
```

## Why Python?

### The Decision

cyberian is written in Python rather than Go, Rust, or Node.js.

### Rationale

**Ecosystem:**

- Rich AI/ML ecosystem
- Typer for CLI
- Pydantic for validation
- httpx for HTTP

**Target audience:**

- AI/ML practitioners use Python
- Data scientists use Python
- Researchers use Python

**Rapid development:**

- Fast iteration
- Less boilerplate
- Dynamic typing aids prototyping

**agentapi compatibility:**

- Many agents (Aider, etc.) are Python
- Natural fit

### Trade-offs

**Advantages:**

- Rich ecosystem
- Audience alignment
- Fast development
- Good libraries

**Disadvantages:**

- Slower than compiled languages
- Runtime dependency (Python)
- Larger distribution

**Alternatives considered:**

- **Go** - Fast, small binaries, but less AI ecosystem
- **Rust** - Very fast, but steeper learning curve
- **Node.js** - Good ecosystem, but less AI-focused

**Performance:** Not a concern - bottleneck is always agent execution (seconds to minutes), not cyberian overhead (milliseconds).

## Why Wrapper, Not Fork?

### The Decision

cyberian wraps agentapi via HTTP rather than forking/embedding it.

### Rationale

**Separation of concerns:**

- agentapi: Agent communication
- cyberian: Workflow orchestration

**Maintainability:**

- Updates to agentapi don't affect cyberian
- Can use any agentapi version
- Clear boundaries

**Flexibility:**

- Connect to remote agentapi servers
- Use different agentapi implementations
- Server farms with multiple versions

**Simplicity:**

- No complex integration
- Standard HTTP API
- Easy to debug (curl, browser)

### Trade-offs

**Advantages:**

- Clean separation
- Maintainable
- Flexible
- Debuggable

**Disadvantages:**

- Requires agentapi installation
- HTTP overhead (negligible)
- Two processes vs one

**Alternatives considered:**

- **Embedding** - Tighter coupling, harder to maintain
- **Forking agentapi** - Would diverge, maintenance burden
- **Direct agent integration** - Reinventing agentapi

## Why No Authentication?

### The Decision

cyberian has no built-in authentication or authorization.

### Rationale

**Trust model:**

- Designed for localhost
- Single-user tool
- Trusted environment

**Simplicity:**

- No user management
- No token handling
- No security infrastructure

**Composability:**

```bash
# Use external auth if needed
nginx + auth → agentapi
         ↑
    cyberian
```

**Scope:**

- Not a multi-user platform
- Not a web service
- Developer tool

### Trade-offs

**Advantages:**

- Simple
- No auth complexity
- Fast development
- Clear scope

**Disadvantages:**

- Not suitable for multi-user
- Not suitable for public internet
- Must compose with other tools for auth

**Best practice:**

For production:

1. Run on localhost only
2. Or use reverse proxy with auth
3. Or use VPN/SSH tunneling
4. Or accept the risk (private network)

## Summary

cyberian's design prioritizes:

1. **Simplicity** - Easy to understand and use
2. **Composability** - Unix philosophy, works with other tools
3. **Flexibility** - YAML + Jinja2 = powerful workflows
4. **Maintainability** - Clean separation, minimal complexity
5. **Developer experience** - Fast iteration, good error messages

Trade-offs favor **developer productivity** over raw performance, since agent execution is the bottleneck.

## Related

- [Architecture](architecture.md) - Implementation details
- [Workflow Model](workflow-model.md) - Execution model
- [Agent Lifecycle](agent-lifecycle.md) - State management

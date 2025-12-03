# Architecture

This document explains cyberian's system architecture and how it interacts with agentapi.

## Overview

cyberian is a **CLI wrapper** around [agentapi](https://github.com/coder/agentapi), providing:

- Command-line interface for agent interaction
- Workflow orchestration layer
- Server farm management
- Template rendering

```
┌─────────────────────────────────────────┐
│            cyberian CLI                 │
│  ┌─────────────────────────────────┐   │
│  │  Commands (message, status, run)│   │
│  └──────────────┬──────────────────┘   │
│                 │                       │
│  ┌──────────────▼──────────────────┐   │
│  │  HTTP Client (httpx)            │   │
│  └──────────────┬──────────────────┘   │
└─────────────────┼───────────────────────┘
                  │ HTTP/REST
┌─────────────────▼───────────────────────┐
│         agentapi Server                 │
│  ┌─────────────────────────────────┐   │
│  │  HTTP API Endpoints             │   │
│  │  - POST /messages               │   │
│  │  - GET  /messages               │   │
│  │  - GET  /status                 │   │
│  └──────────────┬──────────────────┘   │
│                 │                       │
│  ┌──────────────▼──────────────────┐   │
│  │  AI Agent                       │   │
│  │  (Claude, Aider, Cursor, etc.)  │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Components

### CLI Layer

**Purpose:** Provide user-facing commands

**Technology:** Typer (Python CLI framework)

**Responsibilities:**

- Parse command-line arguments
- Validate input
- Format output (JSON, YAML, CSV)
- Handle errors gracefully

**Example:**

```python
@app.command()
def message(
    content: str,
    host: str = "localhost",
    port: int = 3284,
    sync: bool = False,
    timeout: int = 60
):
    # CLI logic
```

### HTTP Client Layer

**Purpose:** Communicate with agentapi servers

**Technology:** httpx (async-capable HTTP client)

**Endpoints:**

- `POST /messages` - Send message to agent
- `GET /messages` - Retrieve conversation history
- `GET /status` - Check agent status

**Communication Pattern:**

```
cyberian                  agentapi
   │                         │
   ├──POST /messages────────►│
   │                         │
   │◄─────200 OK─────────────┤
   │                         │
   ├──GET /status────────────►│
   │  (poll until idle)      │
   │◄─────200 OK─────────────┤
   │  {"status": "idle"}     │
```

### Workflow Engine

**Purpose:** Execute multi-step YAML workflows

**Components:**

1. **YAML Parser** - Load and validate workflow files
2. **Template Renderer** - Render Jinja2 templates
3. **Task Runner** - Execute tasks depth-first
4. **Completion Detector** - Look for `COMPLETION_STATUS`
5. **Success Validator** - Run Python success criteria

**Data Models (Pydantic):**

```python
class Task:
    name: str
    instructions: Optional[str]
    subtasks: Optional[Dict[str, Task]]
    loop_until: Optional[LoopUntil]
    success_criteria: Optional[SuccessCriteria]
    provider_call: Optional[ProviderCall]

class Workflow:
    name: str
    description: str
    params: Dict[str, Parameter]
    subtasks: Dict[str, Task]
    agent_lifecycle: Optional[str]
```

### Server Management

**Purpose:** Start, stop, and manage agentapi servers

**Process Management:**

cyberian uses subprocess management to:

- Start agentapi servers in background
- Track PIDs and ports
- Stop servers by PID or port
- List running servers

**Example:**

```python
# Start server
process = subprocess.Popen([
    "agentapi",
    agent_type,
    "--port", str(port),
    "--dir", working_dir
])

# Track in process table
servers[port] = process.pid
```

### Server Farms

**Purpose:** Manage multiple servers simultaneously

**Architecture:**

```
Farm Config (YAML)
    │
    ├──► Server 1 (port 4000, /tmp/worker1)
    ├──► Server 2 (port 4001, /tmp/worker2)
    └──► Server 3 (port 4002, /tmp/worker3)
```

**Features:**

- Auto port assignment (base_port + index)
- Template directory copying
- Independent working directories
- CORS configuration per-server

## Execution Flow

### Simple Message Flow

```
1. User: cyberian message "Hello"
2. CLI validates arguments
3. HTTP client POST to agentapi:3284/messages
4. agentapi forwards to agent
5. Agent processes message
6. HTTP client returns
7. CLI displays result
```

### Synchronous Message Flow

```
1. User: cyberian message "Hello" --sync
2. CLI validates arguments
3. HTTP client POST to agentapi:3284/messages
4. Loop:
   a. HTTP client GET /status
   b. If status == "busy", sleep 0.5s
   c. If status == "idle", break
   d. If timeout exceeded, error
5. HTTP client GET /messages?last=1
6. CLI displays agent's response
```

### Workflow Execution Flow

```
1. User: cyberian run workflow.yaml --param x=y
2. Load workflow YAML
3. Validate schema
4. Render templates with parameters
5. Start agent server (if not running)
6. Execute tasks depth-first:
   For each task:
     a. Render task instructions
     b. Send to agent
     c. Poll until completion status
     d. Validate success criteria (if any)
     e. Retry if needed
7. Stop agent server (if lifecycle=refresh)
8. Report results
```

## Communication Protocol

### Message Format

```json
{
  "type": "user",
  "content": "Your message here"
}
```

### Status Response

```json
{
  "status": "idle",
  "conversation_id": "uuid",
  "available": true
}
```

**Status values:**

- `idle` - Agent ready for work
- `busy` - Agent processing
- `error` - Something went wrong

### Messages Response

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

## State Management

### Stateless CLI

cyberian CLI is **stateless**:

- No persistent state
- No configuration files (by default)
- Each command is independent

### Stateful Server

agentapi servers are **stateful**:

- Maintain conversation history
- Preserve agent context
- Keep working directory state

### Workflow State

Workflow execution is **ephemeral**:

- State exists only during execution
- No state saved between runs
- Fresh start each time

**Exception:** Agent server state (if `agent_lifecycle=reuse`)

## Concurrency Model

### Sequential Execution

Tasks execute **sequentially** (depth-first):

```yaml
subtasks:
  task1: ...  # Executes first
  task2: ...  # Executes second
  task3: ...  # Executes third
```

### Parallel Execution

For parallel work, use **multiple servers**:

```bash
# Start farm
cyberian farm start farm.yaml

# Run workflows in parallel
cyberian run task1.yaml --port 4000 &
cyberian run task2.yaml --port 4001 &
cyberian run task3.yaml --port 4002 &

wait
```

## Error Handling

### Error Propagation

```
Agent Error
    │
    ├──► agentapi HTTP 500
    │
    ├──► httpx raises HTTPError
    │
    ├──► cyberian catches and formats
    │
    └──► User sees error message
```

### Retry Logic

Retry happens at:

1. **Success criteria level** - `max_retries` per task
2. **No retry at HTTP level** - Fails fast

### Timeout Handling

```
Synchronous message:
    │
    ├──► Poll status in loop
    │
    ├──► Increment elapsed time
    │
    ├──► If elapsed > timeout:
    │       └──► Raise TimeoutError
    │
    └──► Return result
```

## Security Considerations

### No Authentication

cyberian assumes:

- Trusted local environment
- agentapi on localhost
- No authentication needed

For production:

- Use CORS settings
- Run behind authentication proxy
- Limit network access

### Command Injection

Protected by:

- Typer argument parsing
- Subprocess with list arguments (not shell=True)
- No eval() of user input

### File Access

Agent has access to:

- Working directory (--dir)
- Any files agent can read

**Mitigation:**

- Use isolated working directories
- Run in containers
- Set appropriate file permissions

## Performance Characteristics

### HTTP Overhead

- Small (milliseconds per request)
- Negligible compared to agent processing time

### Polling Overhead

- Default: 0.5s intervals
- Configurable via `--poll-interval`
- Trade-off: responsiveness vs CPU usage

### Workflow Overhead

- YAML parsing: ~1-10ms
- Template rendering: ~1-5ms per task
- Negligible compared to agent execution

## Extensibility

### Plugin Points

Currently no formal plugin system, but extensible via:

1. **Custom agents** - Any agentapi-compatible agent
2. **Provider calls** - External service integration
3. **Success criteria** - Python code execution
4. **Templates** - Jinja2 filters and functions

### Future Extensions

Potential areas:

- Plugin system for providers
- Custom completion detectors
- Middleware for HTTP requests
- Event hooks for workflows

## Related

- [Workflow Model](workflow-model.md) - Task execution details
- [Agent Lifecycle](agent-lifecycle.md) - Server state management
- [Design Decisions](design-decisions.md) - Why this architecture?

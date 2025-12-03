# Configuration Reference

Complete reference for configuration file formats used by cyberian.

## Farm Configuration

Farm configuration files define multiple agentapi servers to run simultaneously.

### File Format

YAML file with the following structure:

```yaml
base_port: integer              # Optional
template_directory: string      # Optional
servers: array                  # Required
```

### Top-Level Fields

#### `base_port`

**Type:** `integer`

**Required:** No

**Default:** `3284`

**Description:** Base port for auto-assignment. First server gets this port, second gets `base_port + 1`, etc. Individual servers can override with explicit `port`.

**Example:**

```yaml
base_port: 4000
```

Servers will be assigned ports: 4000, 4001, 4002, ...

#### `template_directory`

**Type:** `string`

**Required:** No

**Description:** Directory to copy to each server's working directory. Path is relative to farm config file (or absolute). All contents (including hidden files) are copied recursively.

**Example:**

```yaml
template_directory: farm-template
```

Can be overridden per-server (see below).

#### `servers`

**Type:** `array`

**Required:** Yes

**Description:** List of server configurations.

**Structure:**

```yaml
servers:
  - name: string              # Required
    agent_type: string        # Optional, default: "custom"
    directory: string         # Required
    port: integer             # Optional (overrides auto-assignment)
    skip_permissions: boolean # Optional, default: false
    allowed_hosts: string     # Optional
    allowed_origins: string   # Optional
    template_directory: string # Optional (overrides global)
```

### Server Fields

#### `name`

**Type:** `string`

**Required:** Yes

**Description:** Logical name for the server (for identification).

**Example:**

```yaml
- name: worker1
```

#### `agent_type`

**Type:** `string`

**Required:** No

**Default:** `"custom"`

**Values:**

- `custom` - Custom agent
- `claude` - Claude agent
- `aider` - Aider agent
- `cursor` - Cursor agent
- `goose` - Goose agent

**Example:**

```yaml
- name: worker1
  agent_type: claude
```

#### `directory`

**Type:** `string`

**Required:** Yes

**Description:** Working directory for this server. Must be writable. Created if doesn't exist.

**Example:**

```yaml
- name: worker1
  directory: /tmp/worker1
```

#### `port`

**Type:** `integer`

**Required:** No

**Description:** Explicit port number. Overrides auto-assignment from `base_port`.

**Example:**

```yaml
- name: worker1
  port: 5000  # Explicit port
```

#### `skip_permissions`

**Type:** `boolean`

**Required:** No

**Default:** `false`

**Description:** If `true`, auto-approve tool permissions (passes agent-specific flag).

**Example:**

```yaml
- name: worker1
  skip_permissions: true
```

#### `allowed_hosts`

**Type:** `string`

**Required:** No

**Description:** Comma-separated list of allowed HTTP hosts for CORS.

**Example:**

```yaml
- name: worker1
  allowed_hosts: "localhost,example.com"
```

#### `allowed_origins`

**Type:** `string`

**Required:** No

**Description:** Comma-separated list of allowed HTTP origins for CORS.

**Example:**

```yaml
- name: worker1
  allowed_origins: "http://localhost:3000,https://example.com"
```

#### `template_directory`

**Type:** `string`

**Required:** No

**Description:** Per-server template directory. Overrides global `template_directory`.

**Example:**

```yaml
- name: worker1
  template_directory: worker1-template
```

### Complete Farm Example

```yaml
# Base port for auto-assignment
base_port: 4000

# Global template directory
template_directory: shared-config

servers:
  # Worker 1: Uses base_port (4000)
  - name: worker1
    agent_type: claude
    directory: /tmp/worker1
    skip_permissions: true

  # Worker 2: Uses base_port+1 (4001)
  - name: worker2
    agent_type: claude
    directory: /tmp/worker2
    skip_permissions: true
    template_directory: worker2-specific  # Override global template

  # Worker 3: Explicit port (5000)
  - name: worker3
    agent_type: aider
    directory: /tmp/worker3
    port: 5000  # Explicit port
    skip_permissions: false
    allowed_origins: "https://example.com"
    allowed_hosts: "example.com"
```

### Port Assignment Logic

```python
assigned_ports = []
next_auto_port = base_port

for server in servers:
    if server.port:
        # Explicit port
        assigned_port = server.port
    else:
        # Auto-assign
        assigned_port = next_auto_port
        next_auto_port += 1

    assigned_ports.append(assigned_port)
```

**Example:**

```yaml
base_port: 4000
servers:
  - name: w1              # Gets 4000 (auto)
  - name: w2
    port: 5000            # Gets 5000 (explicit)
  - name: w3              # Gets 4001 (auto, continues from 4000)
  - name: w4
    port: 6000            # Gets 6000 (explicit)
  - name: w5              # Gets 4002 (auto, continues from 4001)
```

Result: w1=4000, w2=5000, w3=4001, w4=6000, w5=4002

### Template Directory Behavior

**Directory structure:**

```
farm-config/
├── farm.yaml
└── farm-template/
    ├── .claude/
    │   └── CLAUDE.md
    ├── .gitignore
    └── config.json
```

**Farm config:**

```yaml
template_directory: farm-template
servers:
  - name: worker1
    directory: /tmp/worker1
```

**Result:**

```
/tmp/worker1/
├── .claude/
│   └── CLAUDE.md
├── .gitignore
└── config.json
```

All files (including hidden) are copied recursively.

### Validation

Farm configs are validated. Common errors:

**Missing required fields:**

```yaml
# Error: 'name' is required
servers:
  - agent_type: claude
    directory: /tmp/worker1
```

**Missing servers:**

```yaml
# Error: 'servers' is required
base_port: 4000
```

**Invalid port:**

```yaml
# Error: Port must be 1-65535
servers:
  - name: worker1
    port: 99999
```

## Global Configuration

Currently, cyberian does not use a global configuration file. All configuration is per-command or per-farm.

### Potential Future Configuration

A global `~/.cyberian/config.yaml` could support:

```yaml
# Future potential
default_host: localhost
default_port: 3284
default_agent_type: claude
```

This is not currently implemented.

## Environment Variables

cyberian does not currently use environment variables for configuration.

### Potential Future Variables

```bash
# Future potential
export CYBERIAN_HOST=localhost
export CYBERIAN_PORT=3284
export CYBERIAN_AGENT_TYPE=claude
```

This is not currently implemented.

## Best Practices

### Farm Configuration

**Use descriptive names:**

```yaml
# Good
servers:
  - name: research-agent-1
  - name: research-agent-2
  - name: code-review-agent

# Bad
servers:
  - name: agent1
  - name: agent2
  - name: agent3
```

**Organize working directories:**

```yaml
# Good - organized structure
servers:
  - name: worker1
    directory: /tmp/farm/worker1
  - name: worker2
    directory: /tmp/farm/worker2

# Bad - scattered
servers:
  - name: worker1
    directory: /tmp/w1
  - name: worker2
    directory: /home/user/worker2
```

**Use template directories for consistency:**

```yaml
# Create shared config once
template_directory: shared-config

servers:
  - name: worker1
    directory: /tmp/worker1
    # Gets shared-config copied

  - name: worker2
    directory: /tmp/worker2
    # Gets shared-config copied
```

**Document CORS settings:**

```yaml
servers:
  - name: api-agent
    # Allow web app to connect
    allowed_origins: "https://myapp.com"
    allowed_hosts: "myapp.com"
```

### Template Directories

**Structure templates well:**

```
farm-template/
├── .claude/
│   └── CLAUDE.md        # Agent instructions
├── .gitignore           # Standard ignores
├── README.md            # Documentation
└── templates/           # Any shared templates
    └── workflow.yaml
```

**Use for:**

- Agent instructions (`.claude/CLAUDE.md`)
- Shared configuration files
- Standard .gitignore
- Project templates
- Shared workflows

**Don't use for:**

- Large data files (slow to copy)
- Binary files (usually)
- Generated files

## See Also

- [Tutorial: Multi-Agent Farm](../tutorials/multi-agent-farm.md)
- [How-To: Manage Servers](../how-to/manage-servers.md)
- [CLI Reference: farm](cli-commands.md#farm)

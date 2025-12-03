# Workflow YAML Schema Reference

Complete specification for workflow YAML files.

## Overview

Workflows are YAML files that define multi-step tasks for agents to execute. They use a recursive task tree structure with Jinja2 template support.

## Top-Level Workflow Fields

```yaml
name: string                    # Required
description: string             # Required
requires_workdir: boolean       # Optional, default: false
agent_lifecycle: string         # Optional, default: "reuse"
params: object                  # Optional
subtasks: object                # Required
```

### `name`

**Type:** `string`

**Required:** Yes

**Description:** Unique identifier for the workflow.

**Example:**

```yaml
name: deep-research
```

### `description`

**Type:** `string`

**Required:** Yes

**Description:** Human-readable description of what the workflow does.

**Example:**

```yaml
description: Performs iterative deep research on a topic
```

### `requires_workdir`

**Type:** `boolean`

**Required:** No

**Default:** `false`

**Description:** If `true`, workflow requires `--dir` to be specified.

**Example:**

```yaml
requires_workdir: true
```

### `agent_lifecycle`

**Type:** `string`

**Required:** No

**Default:** `"reuse"`

**Values:**

- `reuse` - Keep agent running, maintain context
- `refresh` - Restart agent between tasks

**Description:** Controls agent server lifecycle during workflow execution.

**Example:**

```yaml
agent_lifecycle: refresh
```

### `params`

**Type:** `object`

**Required:** No

**Description:** Dictionary of parameter definitions.

**Structure:**

```yaml
params:
  param_name:
    range: string        # Type: string or integer
    required: boolean    # Required: true or false
```

**Example:**

```yaml
params:
  query:
    range: string
    required: true
  max_iterations:
    range: integer
    required: false
```

### `subtasks`

**Type:** `object`

**Required:** Yes

**Description:** Dictionary of tasks to execute.

**Structure:**

```yaml
subtasks:
  task_name:
    # Task fields (see Task Schema below)
```

## Task Schema

Tasks can be defined at any level of the hierarchy. Each task is a dictionary with the following possible fields:

```yaml
task_name:
  instructions: string              # Optional (terminal node)
  subtasks: object                  # Optional (branch node)
  loop_until: object                # Optional
  success_criteria: object          # Optional
  provider_call: object             # Optional (alternative to instructions)
```

### `instructions`

**Type:** `string`

**Required:** No (unless no `subtasks` or `provider_call`)

**Description:** Instructions for the agent. Supports Jinja2 templating. Must include completion status.

**Example:**

```yaml
instructions: |
  Research {{query}}.
  Write findings to research.md
  COMPLETION_STATUS: COMPLETE
```

### `subtasks`

**Type:** `object`

**Required:** No

**Description:** Nested tasks (recursive structure).

**Example:**

```yaml
subtasks:
  phase1:
    instructions: "Do phase 1. COMPLETION_STATUS: COMPLETE"
  phase2:
    instructions: "Do phase 2. COMPLETION_STATUS: COMPLETE"
```

### `loop_until`

**Type:** `object`

**Required:** No

**Description:** Configuration for looping tasks.

**Structure:**

```yaml
loop_until:
  status: string    # Required: status to wait for
  message: string   # Optional: additional instructions
```

**Example:**

```yaml
loop_until:
  status: CONVERGED
  message: |
    If converged, yield status: CONVERGED
```

### `success_criteria`

**Type:** `object`

**Required:** No

**Description:** Python code to validate task success.

**Structure:**

```yaml
success_criteria:
  python: string       # Required: Python code to execute
  max_retries: integer # Required: number of retries
```

**The Python code must set a variable named `result` to `True` or `False`.**

**Example:**

```yaml
success_criteria:
  python: |
    import os
    result = os.path.exists("output.txt")
  max_retries: 2
```

### `provider_call`

**Type:** `object`

**Required:** No (mutually exclusive with `instructions`)

**Description:** Call external provider instead of using agent.

**Structure:**

```yaml
provider_call:
  provider: string      # Required: provider name
  method: string        # Required: method to call
  params: object        # Required: method parameters
  output_file: string   # Optional: save output to file
```

**Example:**

```yaml
provider_call:
  provider: deep-research-client
  method: research
  params:
    query: "{{topic}}"
    provider: openai
    model: o3-mini
    use_cache: true
  output_file: "research.md"
```

## Complete Example

```yaml
name: comprehensive-research
description: Multi-stage research with validation

requires_workdir: true
agent_lifecycle: reuse

params:
  topic:
    range: string
    required: true
  max_depth:
    range: integer
    required: false

subtasks:
  # Provider call for initial research
  initial_research:
    provider_call:
      provider: deep-research-client
      method: research
      params:
        query: "{{topic}}"
        use_cache: true
      output_file: "initial.md"

    success_criteria:
      python: |
        import os
        result = os.path.exists("initial.md") and os.path.getsize("initial.md") > 100
      max_retries: 1

  # Agent-based deep dive
  deep_dive:
    subtasks:
      analysis:
        instructions: |
          Read initial.md
          Perform deep analysis on {{topic}}
          Write to analysis.md
          COMPLETION_STATUS: COMPLETE

      synthesis:
        instructions: |
          Read analysis.md
          Create synthesis in synthesis.md
          COMPLETION_STATUS: COMPLETE

  # Iterative refinement
  refine:
    instructions: |
      Review synthesis.md
      Refine and improve
      {% if max_depth %}
      Aim for depth level: {{max_depth}}
      {% endif %}

      If refined enough: COMPLETION_STATUS: DONE
      Otherwise: COMPLETION_STATUS: CONTINUE

    loop_until:
      status: DONE
      message: "When refined enough, yield status: DONE"

  # Final validation
  finalize:
    instructions: |
      Create final report in REPORT.md
      COMPLETION_STATUS: COMPLETE

    success_criteria:
      python: |
        import os
        result = os.path.exists("REPORT.md")
      max_retries: 0
```

## Template Variables

All `instructions` and `provider_call.params` fields support Jinja2 templating.

### Available Variables

**User-defined parameters:**

```yaml
params:
  my_param:
    range: string
    required: true
```

Use in templates:

```yaml
instructions: "Process {{my_param}}"
```

**Built-in variables:**

- `{{agent_type}}` - From `--agent-type` flag
- `{{skip_permissions}}` - From `--skip-permissions` flag (boolean)

### Jinja2 Features

**Variables:**

```yaml
instructions: "Research {{topic}}"
```

**Conditionals:**

```yaml
instructions: |
  {% if environment == "production" %}
  Deploy carefully
  {% else %}
  Deploy freely
  {% endif %}
```

**Loops:**

```yaml
instructions: |
  {% for item in items.split(',') %}
  - {{ item }}
  {% endfor %}
```

**Filters:**

```yaml
instructions: "File: {{filename | upper}}"
```

**Defaults:**

```yaml
instructions: "Output: {{output_file | default('output.txt')}}"
```

## Execution Order

Tasks execute in **depth-first** order:

```yaml
subtasks:
  A:
    subtasks:
      B:
        instructions: "Task B"  # Executes 1st
      C:
        instructions: "Task C"  # Executes 2nd
  D:
    instructions: "Task D"      # Executes 3rd
```

Order: B → C → D

## Completion Status

All `instructions` must include a completion status. The agent must output this exact string to signal completion.

**Default:**

```
COMPLETION_STATUS: COMPLETE
```

**Custom (for loops):**

```
COMPLETION_STATUS: CONVERGED
COMPLETION_STATUS: DONE
COMPLETION_STATUS: MAX_ITERATIONS
```

The status appears after `loop_until.status` or defaults to `COMPLETE`.

## Validation

Workflow files are validated against a Pydantic schema. Common errors:

**Missing required fields:**

```yaml
# Error: 'description' is required
name: my-workflow
subtasks: {}
```

**Invalid parameter type:**

```yaml
# Error: range must be 'string' or 'integer'
params:
  x:
    range: float  # Not supported
```

**No terminal nodes:**

```yaml
# Error: Task has neither instructions nor subtasks
subtasks:
  task1:
    loop_until:
      status: DONE
```

**Both instructions and provider_call:**

```yaml
# Error: Mutually exclusive
subtasks:
  task1:
    instructions: "Do something"
    provider_call:
      provider: x
```

## Best Practices

1. **Always include completion status:**

```yaml
instructions: |
  Do work
  COMPLETION_STATUS: COMPLETE  # Required!
```

2. **Use descriptive task names:**

```yaml
# Good
subtasks:
  gather_requirements:
  design_architecture:
  implement_features:

# Bad
subtasks:
  task1:
  task2:
  task3:
```

3. **Keep tasks focused:**

```yaml
# Good - focused tasks
subtasks:
  research:
    instructions: "Research topic. COMPLETION_STATUS: COMPLETE"
  analyze:
    instructions: "Analyze findings. COMPLETION_STATUS: COMPLETE"

# Bad - too broad
subtasks:
  do_everything:
    instructions: "Research, analyze, write report. COMPLETION_STATUS: COMPLETE"
```

4. **Use success criteria for critical tasks:**

```yaml
subtasks:
  critical_task:
    instructions: "Generate config.json. COMPLETION_STATUS: COMPLETE"
    success_criteria:
      python: |
        import json, os
        if not os.path.exists("config.json"):
          result = False
        else:
          with open("config.json") as f:
            json.load(f)  # Validate JSON
          result = True
      max_retries: 2
```

5. **Document complex templates:**

```yaml
instructions: |
  {# This template processes multiple input files #}
  {% for file in files.split(',') %}
  Process {{ file.strip() }}
  {% endfor %}
  COMPLETION_STATUS: COMPLETE
```

## See Also

- [How-To: Write Workflows](../how-to/write-workflows.md)
- [How-To: Use Templates](../how-to/use-templates.md)
- [Tutorial: Your First Workflow](../tutorials/first-workflow.md)
- [Explanation: Workflow Model](../explanation/workflow-model.md)

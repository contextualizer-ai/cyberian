# How to Use Templates

This guide covers advanced Jinja2 templating techniques for workflow instructions.

## Basic Variable Substitution

**Problem:** You need to inject parameters into instructions.

**Solution:**

```yaml
params:
  name:
    range: string
    required: true

subtasks:
  greet:
    instructions: |
      Hello {{name}}!
      COMPLETION_STATUS: COMPLETE
```

```bash
cyberian run workflow.yaml --param name="World"
```

The `{{name}}` is replaced with "World".

## Built-in Context Variables

**Problem:** You need access to command-line settings in templates.

**Solution:**

cyberian provides these built-in variables:

- `{{agent_type}}` - Agent type from `--agent-type`
- `{{skip_permissions}}` - Boolean from `--skip-permissions`

```yaml
subtasks:
  setup:
    instructions: |
      Using agent: {{agent_type}}
      Auto-approve: {{skip_permissions}}
      COMPLETION_STATUS: COMPLETE
```

```bash
cyberian run workflow.yaml \
  --agent-type claude \
  --skip-permissions
```

## Conditional Blocks

**Problem:** You want different instructions based on conditions.

**Solution:**

```yaml
params:
  environment:
    range: string
    required: true

subtasks:
  deploy:
    instructions: |
      {% if environment == "production" %}
      Deploy to production with safety checks.
      Run all tests first.
      {% elif environment == "staging" %}
      Deploy to staging for QA testing.
      {% else %}
      Deploy to development environment.
      {% endif %}
      COMPLETION_STATUS: COMPLETE
```

**Run examples:**

```bash
# Production deployment
cyberian run deploy.yaml --param environment="production"

# Staging deployment
cyberian run deploy.yaml --param environment="staging"

# Dev deployment
cyberian run deploy.yaml --param environment="dev"
```

## Check for Optional Parameters

**Problem:** You have optional parameters that might not be provided.

**Solution:**

```yaml
params:
  required_field:
    range: string
    required: true

  optional_field:
    range: string
    required: false

subtasks:
  task:
    instructions: |
      Always use: {{required_field}}

      {% if optional_field %}
      Optional field provided: {{optional_field}}
      {% else %}
      Optional field not provided, using default behavior.
      {% endif %}

      COMPLETION_STATUS: COMPLETE
```

## Loops in Templates

**Problem:** You need to iterate over values.

**Solution:**

```yaml
params:
  items:
    range: string
    required: true  # Comma-separated list

subtasks:
  process:
    instructions: |
      Process these items:
      {% for item in items.split(',') %}
      - {{ item.strip() }}
      {% endfor %}
      COMPLETION_STATUS: COMPLETE
```

```bash
cyberian run workflow.yaml --param items="apple,banana,cherry"
```

**Output instructions:**

```
Process these items:
- apple
- banana
- cherry
```

## Filters

**Problem:** You need to transform values.

**Solution:**

Jinja2 provides many filters:

```yaml
params:
  text:
    range: string
    required: true

subtasks:
  transform:
    instructions: |
      Original: {{text}}
      Uppercase: {{text | upper}}
      Lowercase: {{text | lower}}
      Title case: {{text | title}}
      Length: {{text | length}}
      COMPLETION_STATUS: COMPLETE
```

**Common filters:**

- `upper` - Convert to uppercase
- `lower` - Convert to lowercase
- `title` - Title case
- `length` - String length
- `trim` - Remove whitespace
- `replace(old, new)` - Replace substring
- `default(value)` - Default if undefined

**Example:**

```yaml
params:
  filename:
    range: string
    required: false

subtasks:
  task:
    instructions: |
      Output file: {{filename | default('output.txt')}}
      COMPLETION_STATUS: COMPLETE
```

## String Concatenation

**Problem:** You need to build strings from parts.

**Solution:**

```yaml
params:
  prefix:
    range: string
    required: true
  suffix:
    range: string
    required: true

subtasks:
  task:
    instructions: |
      Full name: {{prefix}}_{{suffix}}.txt
      COMPLETION_STATUS: COMPLETE
```

Or use filters:

```yaml
subtasks:
  task:
    instructions: |
      Filename: {{ prefix ~ "_" ~ suffix ~ ".txt" }}
      COMPLETION_STATUS: COMPLETE
```

## Multi-line Templates

**Problem:** You need complex, readable template logic.

**Solution:**

Use Jinja2's whitespace control:

```yaml
params:
  features:
    range: string
    required: true

subtasks:
  implement:
    instructions: |
      Implement the following features:
      {%- for feature in features.split(',') %}
      {{ loop.index }}. {{ feature.strip() }}
      {%- endfor %}

      Make sure to:
      {%- if 'auth' in features %}
      - Implement secure authentication
      {%- endif %}
      {%- if 'api' in features %}
      - Add API endpoints
      {%- endif %}

      COMPLETION_STATUS: COMPLETE
```

**Whitespace control:**

- `{%-` - Trim whitespace before
- `-%}` - Trim whitespace after
- `{{-` - Trim before variable
- `-}}` - Trim after variable

## Comments in Templates

**Problem:** You want to document template logic.

**Solution:**

```yaml
subtasks:
  task:
    instructions: |
      {# This is a comment, won't appear in output #}

      {% if environment == "prod" %}
      {# Production-specific instructions #}
      Deploy carefully!
      {% endif %}

      COMPLETION_STATUS: COMPLETE
```

## Variable Assignment

**Problem:** You want to compute values once and reuse them.

**Solution:**

```yaml
params:
  base_path:
    range: string
    required: true

subtasks:
  task:
    instructions: |
      {% set output_file = base_path ~ "/output.txt" %}
      {% set config_file = base_path ~ "/config.json" %}

      Write data to: {{output_file}}
      Read config from: {{config_file}}

      COMPLETION_STATUS: COMPLETE
```

## Testing Template Variables

**Problem:** You need to check if a variable is defined/empty/true.

**Solution:**

```yaml
params:
  config:
    range: string
    required: false

subtasks:
  task:
    instructions: |
      {% if config is defined %}
      Config is defined: {{config}}
      {% endif %}

      {% if config is not defined %}
      Using default config
      {% endif %}

      {% if config %}
      Config has value: {{config}}
      {% endif %}

      COMPLETION_STATUS: COMPLETE
```

**Available tests:**

- `is defined` - Variable exists
- `is not defined` - Variable doesn't exist
- `is true` - Value is truthy
- `is false` - Value is falsy
- `is number` - Value is numeric
- `is string` - Value is a string

## Escaping Special Characters

**Problem:** You need literal `{{` or `{%` in output.

**Solution:**

```yaml
subtasks:
  task:
    instructions: |
      {% raw %}
      This will output literally: {{variable}}
      And this: {%for x in range(10)%}
      {% endraw %}
      COMPLETION_STATUS: COMPLETE
```

Or use string literals:

```yaml
subtasks:
  task:
    instructions: |
      To use Jinja2 in your code, write {{ "{{" }} variable {{ "}}" }}
      COMPLETION_STATUS: COMPLETE
```

## Complex Example

**Problem:** You need sophisticated template logic.

**Solution:**

```yaml
name: advanced-template
description: Demonstrates advanced templating

params:
  project_name:
    range: string
    required: true
  languages:
    range: string
    required: true
  include_tests:
    range: string
    required: false
  environment:
    range: string
    required: true

subtasks:
  setup_project:
    instructions: |
      {% set langs = languages.split(',') %}
      {% set project_slug = project_name | lower | replace(' ', '-') %}

      Create project: {{project_name}}
      Slug: {{project_slug}}

      Languages to setup:
      {%- for lang in langs %}
      {{ loop.index }}. {{ lang.strip() | title }}
      {%- endfor %}

      {% if include_tests == "true" %}
      Also setup testing infrastructure for:
      {%- for lang in langs %}
      - {{ lang.strip() }} test framework
      {%- endfor %}
      {% endif %}

      Environment: {{ environment | upper }}
      {% if environment == "production" %}
      ⚠️  Use production-safe defaults
      {% else %}
      ℹ️  Using development defaults
      {% endif %}

      COMPLETION_STATUS: COMPLETE
```

```bash
cyberian run advanced-template.yaml \
  --param project_name="My Cool App" \
  --param languages="python,javascript,rust" \
  --param include_tests="true" \
  --param environment="production"
```

## Related Guides

- [Write Workflows](write-workflows.md) - Workflow structure
- [Tutorial: Your First Workflow](../tutorials/first-workflow.md) - Basic templates
- [Troubleshooting](troubleshooting.md) - Template debugging

## See Also

- [Jinja2 Documentation](https://jinja.palletsprojects.com/) - Complete Jinja2 reference
- [Reference: Workflow Schema](../reference/workflow-schema.md) - YAML specification

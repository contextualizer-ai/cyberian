# Explanation

The explanation section provides **understanding-oriented** documentation that clarifies concepts and design decisions in cyberian.

## What are Explanations?

Explanations help you understand:

- **How things work** under the hood
- **Why things are designed** the way they are
- **Connections between** different components
- **Background and context** for features

If you need step-by-step instructions, see [Tutorials](../tutorials/index.md) or [How-To Guides](../how-to/index.md) instead.

## Available Topics

### [Architecture](architecture.md)

Understand cyberian's system architecture:

- How cyberian wraps agentapi
- HTTP communication model
- Client-server relationship
- Process management
- Server farms architecture

### [Workflow Model](workflow-model.md)

Deep dive into workflow execution:

- Recursive task tree structure
- Depth-first traversal algorithm
- Completion detection mechanism
- Loop execution model
- Template rendering pipeline
- Success criteria validation

### [Ralph Wiggum Pattern](ralph-wiggum-pattern.md)

Understand the autonomous iteration pattern that inspired cyberian's loops:

- Origins and core concept
- State in files vs context window
- Fresh context and "context rot"
- How cyberian implements the pattern
- Comparison: code loops vs research loops
- Best practices for long-running workflows

### [Agent Lifecycle](agent-lifecycle.md)

Understand agent state management:

- Server lifecycle (start, run, stop)
- Agent memory and context
- `reuse` vs `refresh` modes
- When to use each mode
- State isolation patterns

### [Design Decisions](design-decisions.md)

Learn why cyberian works the way it does:

- Why YAML for workflows?
- Why Jinja2 for templates?
- Why synchronous polling?
- Why recursive task trees?
- Trade-offs and alternatives

## Reading Guide

These explanations are best read:

1. **After** completing the tutorials
2. **When** you're curious about how things work
3. **Before** making architectural decisions in your workflows
4. **To understand** error messages and behavior

## See Also

- **[Tutorials](../tutorials/index.md)** - Step-by-step learning
- **[How-To Guides](../how-to/index.md)** - Task-oriented recipes
- **[Reference](../reference/index.md)** - Complete specifications

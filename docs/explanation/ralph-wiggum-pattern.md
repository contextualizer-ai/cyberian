# The Ralph Wiggum Pattern

This document explains the Ralph Wiggum autonomous iteration pattern and how cyberian implements it for research workflows.

## Origins

The Ralph Wiggum technique was created by [Geoffrey Huntley](https://ghuntley.com/ralph/) in late 2025. Named after the lovably persistent Simpsons character, it's an approach to autonomous AI agent execution that went viral in the AI development community.

> "Better to fail predictably than succeed unpredictably."

The pattern has been [covered extensively](https://venturebeat.com/technology/how-ralph-wiggum-went-from-the-simpsons-to-the-biggest-name-in-ai-right-now/) and adapted for various use cases.

## Core Concept

In its purest form, Ralph is a Bash loop:

```bash
while true; do
  claude --prompt "Complete the PRD. Output DONE when finished."
  sleep 1
done
```

The key insights:

1. **Iterate until done** - Keep running until completion
2. **State in files, not context** - Progress persists in filesystem, not LLM memory
3. **Backpressure over prescription** - Create conditions where bad work gets rejected automatically
4. **Fresh context per iteration** - Each loop gets a clean agent with full context window

## Why Fresh Context Matters

Traditional agent loops maintain conversation history:

```
Iteration 1: Agent processes task, context grows
Iteration 2: Agent sees iteration 1 + new task, context grows more
Iteration 3: Context now large, earlier instructions get less attention
...
Iteration N: "Context rot" - agent forgets original goals
```

Ralph's fresh context approach:

```
Iteration 1: Fresh agent reads PLAN.md, does work, updates files
Iteration 2: Fresh agent reads PLAN.md + updated files, continues
Iteration 3: Fresh agent reads current state, no context rot
...
Iteration N: Agent always has full attention on current state
```

State management shifts from LLM memory (token sequence) to disk (file system).

## Ralph for Code vs Research

### Code Pattern (Original)

```
while not tests_pass:
    agent.run("Fix failing tests")
    run_tests()
```

Backpressure: Tests, linters, type checkers automatically reject bad work.

### Research Pattern (cyberian)

```
while not literature_exhausted:
    agent.run("Continue researching, update REPORT.md")
    check_completion_status()
```

Backpressure: Agent determines when research avenues are exhausted.

## How cyberian Implements Ralph

### The `loop_until` Mechanism

```yaml
# deep-research.yaml
subtasks:
  iterate:
    instructions: |
      Keep on researching {{query}}, following the plan in PLAN.md.
    loop_until:
      status: NO_MORE_RESEARCH
      message: "If all research avenues are exhausted, yield NO_MORE_RESEARCH"
```

This implements the core loop: iterate until the agent signals completion.

### State in Files

cyberian research workflows accumulate state in files:

```
workspace/
├── PLAN.md              # Research plan (like a PRD)
├── REPORT.md            # Narrative synthesis of findings
├── CITATION_GRAPH.md    # Paper relationships
└── citations/           # Downloaded papers and summaries
    ├── smith-2023-paper.pdf
    ├── smith-2023-summary.md
    └── jones-2024-abstract.md
```

The agent reads these files to understand current state, not conversation history.

### Success Criteria as Backpressure

```yaml
success_criteria:
  python: |
    import os
    # Verify required outputs exist
    result = (
        os.path.exists("PLAN.md") and
        os.path.exists("REPORT.md")
    )
  max_retries: 3
  retry_message: "Required files missing. Please create PLAN.md and REPORT.md"
```

This creates backpressure: incomplete work triggers automatic retry.

### Agent Lifecycle Modes

cyberian supports two modes:

| Mode | Description | Ralph-like? |
|------|-------------|-------------|
| `reuse` (default) | Same conversation across tasks | Partial |
| `refresh` | Restart agent between top-level tasks | Yes |

```bash
# Reuse mode (default) - maintains conversation
cyberian run workflow.yaml

# Refresh mode - fresh context per task
cyberian run workflow.yaml --agent-lifecycle refresh
```

## Current Limitations

### Within-Loop Context

Currently, `loop_until` iterations maintain the same conversation:

```
Loop iteration 1: Context = [task + response1]
Loop iteration 2: Context = [task + response1 + task + response2]
Loop iteration 3: Context growing...
```

For true Ralph behavior, each loop iteration would get fresh context.

### Proposed Enhancement

```yaml
# Hypothetical future enhancement
iterate:
  instructions: |
    Read PLAN.md for research state.
    Continue working on next item.
    Update PROGRESS.md when done.
  loop_until:
    status: ALL_COMPLETE
  context_refresh: true  # Fresh context each iteration
```

This would:

1. Complete one loop iteration
2. Stop the agent
3. Start a fresh agent
4. Re-execute the loop instructions
5. Fresh agent reads state from files

## Practical Recommendations

### For Long Research Workflows

1. **Use file-based state**: Write PLAN.md, PROGRESS.md, REPORT.md
2. **Make instructions self-contained**: Don't rely on conversation history
3. **Use success criteria**: Create backpressure for incomplete work
4. **Consider refresh mode**: `--agent-lifecycle refresh` for task-level fresh context

### Example: Ralph-Style Research Workflow

```yaml
name: ralph-research
description: Research workflow with Ralph-style state management

subtasks:
  plan:
    instructions: |
      Create a research plan for: {{query}}

      Write the plan to PLAN.md with:
      - Research questions
      - Search strategies
      - Expected sources

      COMPLETION_STATUS: COMPLETE

    success_criteria:
      python: |
        import os
        result = os.path.exists("PLAN.md")

  iterate:
    instructions: |
      Read PLAN.md for the research plan.
      Read REPORT.md for current findings (if exists).
      Read PROGRESS.md for completed items (if exists).

      Continue researching. For each finding:
      1. Update REPORT.md with new content
      2. Mark item complete in PROGRESS.md
      3. Add citations to citations/ folder

      When all plan items are complete, output: NO_MORE_RESEARCH
      Otherwise, output: COMPLETION_STATUS: COMPLETE

    loop_until:
      status: NO_MORE_RESEARCH
      message: "When all research avenues are exhausted, yield NO_MORE_RESEARCH"

    success_criteria:
      python: |
        import os
        result = os.path.exists("REPORT.md")
      max_retries: 2

  synthesize:
    instructions: |
      Read all files in the workspace.
      Create a final SUMMARY.md synthesizing all findings.

      COMPLETION_STATUS: COMPLETE
```

### Key Patterns

1. **Self-contained instructions**: Each task reads state from files
2. **Explicit file I/O**: Agent writes to specific files
3. **Progress tracking**: PROGRESS.md tracks completed items
4. **Backpressure**: Success criteria verify outputs exist

## Comparison Table

| Aspect | Pure Ralph | cyberian (current) | cyberian (with refresh) |
|--------|------------|-------------------|------------------------|
| Loop until condition | Yes | Yes | Yes |
| State in files | Yes | Yes | Yes |
| Fresh context per iteration | Yes | No | Per-task only |
| Backpressure via tests | Yes | Via success_criteria | Via success_criteria |
| Automatic retry | Yes | Yes | Yes |

## Further Reading

- [Geoffrey Huntley - Ralph Wiggum](https://ghuntley.com/ralph/) - Original technique
- [How to Ralph Wiggum](https://github.com/ghuntley/how-to-ralph-wiggum) - Implementation guide
- [VentureBeat coverage](https://venturebeat.com/technology/how-ralph-wiggum-went-from-the-simpsons-to-the-biggest-name-in-ai-right-now/) - Industry analysis
- [Ralph Wiggum Tries His Hand at Deep Research](https://dev.to/cmungall/ralph-wiggum-tries-his-hand-at-deep-research-2mdf) - Research application

## See Also

- [Workflow Model](workflow-model.md) - How workflows execute
- [Agent Lifecycle](agent-lifecycle.md) - Reuse vs refresh modes
- [Write a Deep Research Workflow](../how-to/write-deep-research-workflow.md) - Practical guide

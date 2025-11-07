# Example Workflows

This directory contains example workflow YAML files for testing and demonstration.

## Workflows

### simple-math.yaml
A simple 3-step arithmetic workflow for testing. Takes an input number and:
1. Step 1: Adds 1
2. Step 2: Adds 2
3. Step 3: Adds 3

Final result = input + 6

**Usage:**
```bash
# With server running on localhost:3284
uv run cyberian run tests/examples/simple-math.yaml \
  -p input_number=10
```

**For testing:**
- Quick execution (~40-50 seconds for all 3 steps)
- Deterministic, predictable results
- Good for integration testing
- Tests resume functionality: `--resume-from step2`

### deep-research.yaml
A complex iterative research workflow with:
1. Initial search with file creation
2. Iterative research loop with `NO_MORE_RESEARCH` exit condition

**Usage:**
```bash
uv run cyberian run tests/examples/deep-research.yaml \
  -p query="research KCNQ1OT1 gene" \
  -p workdir="tmp" \
  -v
```

**Characteristics:**
- Long-running (can take 30+ minutes)
- Uses looping with exit conditions
- Creates multiple files (PLAN.md, REPORT.md, citations/)
- Tests resume: `--resume-from iterate`

### pdf-summarize.yaml
A multi-stage PDF summarization workflow demonstrating success criteria validation:
1. Step 1: Download and summarize PDF to N characters → SUMMARY_1.md
2. Step 2: Condense SUMMARY_1.md to N/2 characters → SUMMARY_2.md
3. Step 3: Create one-line summary (≤200 chars) → SUMMARY_3.md

Each step includes `success_criteria` with Python code to validate output file length.

**Usage:**
```bash
# With server running on localhost:3284
uv run cyberian run tests/examples/pdf-summarize.yaml \
  -p pdf_url="https://www.nature.com/articles/s41597-024-03069-7.pdf" \
  -p max_chars_step1=2000 \
  -p workdir="tmp" \
  -v
```

**Characteristics:**
- Demonstrates success criteria validation feature
- Each step validates its output programmatically
- Workflow fails if any step produces output exceeding length constraints
- Useful for testing file-based validation
- Moderate runtime (5-10 minutes depending on PDF complexity)

## Integration Testing

See `tests/test_integration.py` for non-mocked integration tests that run these workflows against a real agentapi server.

The test suite includes:
- Basic workflow execution (simple-math with different inputs)
- Resume functionality testing
- Parametrized tests with multiple input values

**Run integration tests:**
```bash
# Start server
uv run cyberian server claude --skip-permissions

# In another terminal, run tests
uv run pytest tests/test_integration.py -v -m integration
```

# Testing Guide

Guide for running and writing tests in cyberian.

## Testing Philosophy

cyberian follows these testing principles:

1. **Test-driven development** - Write tests before implementation
2. **No mocks** - Test real functionality when possible
3. **pytest style** - Use fixtures and parametrize
4. **Doctests** - Use for documentation and simple tests

## Running Tests

### All Tests

```bash
# Using just (recommended)
just test

# Or directly
uv run pytest tests/
```

This runs:

- pytest
- mypy
- ruff (format checking)

### Pytest Only

```bash
just pytest

# Or
uv run pytest tests/
```

### Specific Tests

```bash
# Single test file
uv run pytest tests/test_simple.py

# Single test function
uv run pytest tests/test_simple.py::test_simple

# Tests matching pattern
uv run pytest -k "test_message"
```

### Test Markers

Tests are organized using pytest markers:

```bash
# Run only integration tests (require agentapi server)
uv run pytest -m integration

# Run only LLM tests (may be slow/expensive)
uv run pytest -m llm

# Run unit tests only (default - excludes integration and llm)
uv run pytest

# Run specific marked test
uv run pytest tests/test_tag_workflow.py::test_tag_workflow_integration -m integration
```

**Available markers:**
- `integration` - Tests that require running agentapi server
- `llm` - Tests that call LLM APIs (may be slow/expensive)

**Running integration tests:**

Integration tests require a running agentapi server. To run them:

```bash
# 1. Start an agentapi server in a separate terminal
uv run cyberian server claude --skip-permissions

# 2. Run integration tests
uv run pytest -m integration

# 3. Run integration tests with LLM calls (slow/expensive)
uv run pytest -m "integration and llm"
```

If you try to run integration tests without a server, you'll see an informative skip message:
```
SKIPPED - No agentapi server running. Start with: uv run cyberian server claude --skip-permissions
```

See `pytest.ini` for configuration.

### With Coverage

```bash
# Coverage report
uv run pytest --cov=cyberian tests/

# HTML coverage report
uv run pytest --cov=cyberian --cov-report=html tests/
open htmlcov/index.html
```

### Verbose Output

```bash
# Verbose
uv run pytest -v tests/

# Very verbose
uv run pytest -vv tests/

# Show print statements
uv run pytest -s tests/
```

### Doctests

```bash
# Run doctests
just doctest

# Or
uv run pytest --doctest-modules src/cyberian/
```

## Test Organization

### Test Structure

```
tests/
├── examples/              # Example workflow files
│   ├── simple.yaml
│   ├── deep-research.yaml
│   └── farm.yaml
├── test_commands.py       # Command tests
├── test_message.py        # Message command tests
├── test_workflow.py       # Workflow tests
└── test_simple.py         # Simple integration tests
```

### Test Files

- `test_*.py` - Test modules
- One test module per command/feature
- Group related tests in classes (optional)

### Test Functions

```python
def test_feature_name():
    """Test description."""
    # Arrange
    input_data = ...

    # Act
    result = function(input_data)

    # Assert
    assert result == expected
```

## Writing Tests

### Basic Test

```python
def test_message_command():
    """Test message command sends message."""
    # Arrange
    content = "Hello"

    # Act
    result = send_message(content)

    # Assert
    assert result.status_code == 200
```

### Parametrized Test

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("Test", "TEST"),
])
def test_uppercase(input, expected):
    """Test uppercase conversion."""
    assert input.upper() == expected
```

### Using Fixtures

```python
import pytest

@pytest.fixture
def sample_workflow():
    """Create sample workflow for testing."""
    return {
        "name": "test-workflow",
        "description": "Test",
        "subtasks": {
            "task1": {
                "instructions": "Do something"
            }
        }
    }

def test_workflow(sample_workflow):
    """Test workflow execution."""
    result = run_workflow(sample_workflow)
    assert result.success
```

### Temporary Files

```python
import tempfile
from pathlib import Path

def test_file_creation():
    """Test file creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "output.txt"

        # Create file
        create_file(filepath)

        # Assert
        assert filepath.exists()
```

### Testing CLI Commands

```python
from typer.testing import CliRunner
from cyberian.cli import app

runner = CliRunner()

def test_status_command():
    """Test status command."""
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
```

### Testing HTTP Calls

```python
import httpx
from unittest.mock import patch

def test_api_call():
    """Test API call."""
    with patch('httpx.get') as mock_get:
        mock_get.return_value.json.return_value = {"status": "ok"}

        result = check_status()

        assert result["status"] == "ok"
        mock_get.assert_called_once()
```

## Test Examples

### Test Command Execution

```python
def test_message_sync():
    """Test synchronous message."""
    # Start server
    start_server()

    # Send sync message
    result = send_message("Test", sync=True)

    # Verify response
    assert "Test" in result
    assert len(result) > 0

    # Cleanup
    stop_server()
```

### Test Workflow Execution

```python
def test_workflow_execution():
    """Test workflow runs successfully."""
    workflow_file = "tests/examples/simple.yaml"

    # Run workflow
    result = run_workflow(workflow_file, params={"name": "test"})

    # Verify completion
    assert result.success
    assert result.completed_tasks == ["task1", "task2"]
```

### Test Error Handling

```python
def test_connection_error():
    """Test handling of connection errors."""
    with pytest.raises(ConnectionError):
        send_message("Test", host="invalid-host")
```

### Test Parametrized Scenarios

```python
@pytest.mark.parametrize("format,expected_type", [
    ("json", dict),
    ("yaml", str),
    ("csv", str),
])
def test_output_formats(format, expected_type):
    """Test different output formats."""
    result = get_messages(format=format)
    assert isinstance(result, expected_type)
```

## Testing Best Practices

### Do's

- **Write tests first** - TDD approach
- **Test real behavior** - Avoid mocks when possible
- **Use descriptive names** - `test_message_sends_to_correct_port`
- **One assertion per test** - Or related assertions
- **Use fixtures** - For reusable test data
- **Test edge cases** - Empty input, large input, invalid input
- **Clean up** - Stop servers, delete temp files

### Don'ts

- **Don't skip tests** - Fix or remove broken tests
- **Don't rely on order** - Tests should be independent
- **Don't test implementation** - Test behavior
- **Don't overuse mocks** - Test real code when possible
- **Don't commit failing tests** - Fix before committing

### Example Patterns

**Good:**

```python
def test_message_sends_successfully():
    """Test message sends successfully to server."""
    server = start_test_server()
    try:
        result = send_message("Hello", port=server.port)
        assert result.status_code == 200
    finally:
        stop_test_server(server)
```

**Bad:**

```python
def test_stuff():  # Vague name
    """Test."""  # Vague docstring
    # No cleanup
    result = send_message("Hello")
    assert result  # What are we testing?
```

## Continuous Integration

Tests run automatically on:

- Pull requests
- Pushes to main branch
- Via GitHub Actions

### CI Configuration

See `.github/workflows/test.yml`:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
      - run: uv sync
      - run: just test
```

## Debugging Tests

### Print Output

```bash
# Show print statements
uv run pytest -s tests/test_simple.py
```

### PDB Debugger

```python
def test_something():
    """Test something."""
    result = function()

    # Drop into debugger
    import pdb; pdb.set_trace()

    assert result == expected
```

### Verbose Failures

```bash
# Show full diff on assertion failures
uv run pytest -vv tests/
```

### Run Last Failed

```bash
# Re-run only failed tests
uv run pytest --lf tests/
```

## Test Coverage

### View Coverage

```bash
# Terminal report
uv run pytest --cov=cyberian tests/

# HTML report
uv run pytest --cov=cyberian --cov-report=html tests/
open htmlcov/index.html
```

### Coverage Goals

- **Overall:** > 80%
- **Critical paths:** 100%
- **CLI commands:** > 90%
- **Workflow runner:** > 90%

### Missing Coverage

```bash
# Show lines not covered
uv run pytest --cov=cyberian --cov-report=term-missing tests/
```

## Performance Testing

### Timing Tests

```bash
# Show slowest tests
uv run pytest --durations=10 tests/
```

### Timeout Tests

```python
@pytest.mark.timeout(10)
def test_slow_operation():
    """Test completes within 10 seconds."""
    result = slow_operation()
    assert result.success
```

## See Also

- [pytest documentation](https://pytest.org/)
- [Typer testing](https://typer.tiangolo.com/tutorial/testing/)
- [Contributing Guide](contributing.md)
- [Setup Guide](setup.md)

# Development Setup

Guide for setting up a cyberian development environment.

## Prerequisites

- Python 3.10 or later
- Git
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [just](https://github.com/casey/just) (recommended) or make

## Clone Repository

```bash
git clone https://github.com/monarch-initiative/cyberian.git
cd cyberian
```

## Install Dependencies

### Using uv (Recommended)

```bash
# Install all dependencies including dev dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Unix
# or
.venv\Scripts\activate     # On Windows
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode with all extras
pip install -e ".[dev,providers]"
```

## Install just (Command Runner)

### macOS

```bash
brew install just
```

### Linux

```bash
# Using cargo
cargo install just

# Or download binary from releases
wget https://github.com/casey/just/releases/download/latest/just-*.tar.gz
tar xf just-*.tar.gz
sudo mv just /usr/local/bin/
```

### Windows

```powershell
# Using cargo
cargo install just

# Or using scoop
scoop install just
```

## Verify Installation

```bash
# Check Python version
python --version  # Should be 3.10+

# Check uv
uv --version

# Check just
just --version

# Run tests
just test
```

## Development Tools

### Run CLI

```bash
# Using uv
uv run cyberian --help

# Or after activating venv
cyberian --help
```

### Run Tests

```bash
# All tests
just test

# Just pytest
just pytest

# Specific test
uv run pytest tests/test_simple.py::test_simple

# With coverage
uv run pytest --cov=cyberian tests/
```

### Type Checking

```bash
# Run mypy
just mypy

# Or directly
uv run mypy src/cyberian/
```

### Linting and Formatting

```bash
# Check formatting
just format

# Or directly
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
```

### Documentation

```bash
# Serve docs locally
just _serve

# Or directly
uv run mkdocs serve
```

Visit http://localhost:8000

## Project Commands

The `justfile` provides these commands:

```bash
# Run all tests and checks
just test

# Run pytest only
just pytest

# Run specific test
just pytest-specific tests/test_simple.py::test_simple

# Run mypy type checking
just mypy

# Check formatting
just format

# Run doctests
just doctest

# Serve documentation
just _serve

# List all commands
just --list
```

## IDE Setup

### VS Code

Install extensions:

- Python
- Pylance
- Ruff
- Even Better TOML

Add to `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

### PyCharm

1. Set Python interpreter to `.venv/bin/python`
2. Enable pytest as test runner
3. Configure mypy as external tool
4. Install Ruff plugin

## Common Tasks

### Add a New Command

1. Add command function to `src/cyberian/cli.py`:

```python
@app.command()
def new_command(
    arg: str = typer.Argument(..., help="Description"),
    option: bool = typer.Option(False, help="Description")
):
    """Command description."""
    # Implementation
```

2. Add tests in `tests/test_commands.py`:

```python
def test_new_command():
    """Test new command."""
    # Test implementation
```

3. Run tests:

```bash
just test
```

### Add a New Workflow Feature

1. Update models in `src/cyberian/models.py`:

```python
class Task(BaseModel):
    new_field: Optional[str] = None
```

2. Update runner in `src/cyberian/runner.py`

3. Add tests in `tests/test_workflow.py`

4. Update documentation in `docs/reference/workflow-schema.md`

### Add Documentation

1. Create/edit markdown files in `docs/`

2. Update navigation in `mkdocs.yml`:

```yaml
nav:
  - Section:
    - Page: path/to/page.md
```

3. Preview locally:

```bash
just _serve
```

## Troubleshooting

### uv sync fails

```bash
# Clear cache and retry
rm -rf .venv
uv sync
```

### Tests fail

```bash
# Run with verbose output
uv run pytest -vv

# Run specific failing test
uv run pytest tests/test_simple.py::test_simple -vv
```

### Type checking fails

```bash
# Run mypy with verbose output
uv run mypy src/cyberian/ --verbose
```

### Imports not found

```bash
# Reinstall in development mode
uv pip install -e .
```

## Next Steps

- Read [Testing Guide](testing.md)
- Read [Contributing Guide](contributing.md)
- Check [open issues](https://github.com/monarch-initiative/cyberian/issues)

## See Also

- [uv documentation](https://github.com/astral-sh/uv)
- [just documentation](https://just.systems/)
- [pytest documentation](https://pytest.org/)
- [Typer documentation](https://typer.tiangolo.com/)

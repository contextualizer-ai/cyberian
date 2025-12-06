# Development

Documentation for contributors and developers working on cyberian.

## Quick Links

- **[Setup](setup.md)** - Development environment setup
- **[Testing](testing.md)** - Running and writing tests
- **[Contributing](contributing.md)** - Contribution guidelines

## Project Overview

cyberian is a Python CLI tool that wraps [agentapi](https://github.com/coder/agentapi) to enable workflow automation and multi-agent orchestration.

### Technology Stack

- **Python 3.10+** - Core language
- **uv** - Dependency management
- **Typer** - CLI framework
- **Pydantic** - Data validation
- **httpx** - HTTP client
- **pytest** - Testing
- **mypy** - Type checking
- **ruff** - Linting and formatting
- **MkDocs Material** - Documentation

### Repository Structure

```
cyberian/
├── docs/               # Documentation (MkDocs)
├── src/cyberian/       # Source code
│   ├── cli.py         # CLI interface
│   ├── models.py      # Pydantic models
│   └── runner.py      # Workflow runner
├── tests/             # Test suite
│   ├── examples/      # Example workflows
│   └── test_*.py      # Test files
├── pyproject.toml     # Project configuration
├── justfile           # Command runner recipes
└── mkdocs.yml         # Documentation config
```

## Development Workflow

1. **Setup** - Install dependencies and tools
2. **Code** - Make changes following conventions
3. **Test** - Run tests and type checking
4. **Document** - Update docs as needed
5. **Submit** - Create pull request

## Code Style

- **Type hints** - Use throughout
- **Docstrings** - Document functions and classes
- **Tests** - Write tests for new features
- **Ruff** - Follow ruff formatting

## Testing Philosophy

- **Test-driven development** - Write tests first
- **No mocks** - Test real functionality when possible
- **pytest style** - Use pytest fixtures and parametrize
- **Doctests** - Use for documentation and testing

## Getting Help

- **Issues** - [GitHub Issues](https://github.com/monarch-initiative/cyberian/issues)
- **Discussions** - [GitHub Discussions](https://github.com/monarch-initiative/cyberian/discussions)
- **Documentation** - This site

## See Also

- [Setup Guide](setup.md)
- [Testing Guide](testing.md)
- [Contributing Guide](contributing.md)

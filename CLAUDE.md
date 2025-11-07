# CLAUDE.md for cyberian

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**For comprehensive project documentation, see [AGENTS.md](AGENTS.md).**

## Project Overview

Python CLI wrapper for [agentapi](https://github.com/coder/agentapi) that enables interaction with AI agent APIs in pipeline workflows.

The project uses `uv` for dependency management and `just` as the command runner.

## IMPORTANT INSTRUCTIONS

- we use test driven development, write tests first before implementing a feature
- do not try and 'cheat' by making mock tests (unless asked)
- if functionality does not work, keep trying, do not relax the test just to get poor code in
- always run tests
- use docstrings

We make heavy use of doctests, these serve as both docs and tests. `just test` will include these,
or do `just doctest` just to write doctests

In general AVOID try/except blocks, except when these are truly called for, for example
when interfacing with external systems. For wrapping deterministic code,  these are ALMOST
NEVER required, if you think you need them, it's likely a bad smell that your logic is wrong.

## Essential Commands


### Testing and Quality
- `just test` - Run all tests, type checking, and formatting checks
- `just pytest` - Run Python tests only
- `just mypy` - Run type checking
- `just format` - Run ruff linting/formatting checks
- `uv run pytest tests/test_simple.py::test_simple` - Run a specific test

### Running the CLI
- `uv run cyberian --help` - Run the CLI tool with options

### Documentation
- `just _serve` - Run local documentation server with mkdocs

## Project Architecture

### Core Structure
- **src/cyberian/** - Main package containing the CLI and application logic
  - `cli.py` - Typer-based CLI interface, entry point for the application (~250 lines)
  - `models.py` - Pydantic models for workflow/task definitions
- **tests/** - Test suite using pytest with parametrized tests (38 tests)
  - `test_commands.py` - Tests for messages, status, server, list-servers
  - `test_message.py` - Tests for message command including sync mode
  - `examples/` - Example workflow YAML files
- **docs/** - MkDocs-managed documentation with Material theme

### Technology Stack
- **Python 3.10+** with `uv` for dependency management
- **Typer** for CLI interface
- **httpx** for HTTP client interactions
- **Pydantic** for data modeling and validation
- **PyYAML** for YAML file handling
- **pytest** for testing (with mocking via unittest.mock)
- **mypy** for type checking
- **ruff** for linting and formatting
- **MkDocs Material** for documentation

### Key Configuration Files
- `pyproject.toml` - Python project configuration, dependencies, and tool settings
- `justfile` - Command runner recipes for common development tasks
- `mkdocs.yml` - Documentation configuration
- `uv.lock` - Locked dependency versions

## Development Workflow

1. Dependencies are managed via `uv` - use `uv add` for new dependencies
2. All commands are run through `just` or `uv run`
3. The project uses dynamic versioning from git tags
4. Documentation is auto-deployed to GitHub Pages at https://monarch-initiative.github.io/cyberian

## Current State

- **38 passing tests** covering all commands and features
- **5 main commands**: message, messages, status, server, list-servers
- **Key features**:
  - Synchronous message sending with `--sync` flag
  - Multiple output formats (JSON, YAML, CSV)
  - Message filtering (last N messages)
  - Server discovery and management
  - Configurable timeouts and polling intervals

## Future Enhancements

See [NOTIFY_FEATURE.md](NOTIFY_FEATURE.md) for planned background notification feature.

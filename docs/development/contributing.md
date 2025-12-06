# Contributing Guide

Thank you for contributing to cyberian! This guide will help you get started.

## Quick Start

1. Fork the repository
2. Clone your fork
3. Create a branch
4. Make changes
5. Run tests
6. Submit pull request

## Detailed Guide

### 1. Fork and Clone

```bash
# Fork on GitHub, then clone
git clone https://github.com/YOUR-USERNAME/cyberian.git
cd cyberian

# Add upstream remote
git remote add upstream https://github.com/monarch-initiative/cyberian.git
```

### 2. Setup Development Environment

```bash
# Install dependencies
uv sync

# Verify installation
just test
```

See [Setup Guide](setup.md) for details.

### 3. Create a Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-feature

# Or bugfix branch
git checkout -b bugfix/fix-issue-123
```

**Branch naming:**

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Refactoring

### 4. Make Changes

**Code Style:**

- Use type hints
- Write docstrings
- Follow ruff formatting
- Keep functions focused

**Example:**

```python
def send_message(
    content: str,
    host: str = "localhost",
    port: int = 3284,
) -> dict:
    """Send message to agent.

    Args:
        content: Message content
        host: Agent API host
        port: Agent API port

    Returns:
        Response from agent API

    Raises:
        ConnectionError: If cannot connect to agent
    """
    # Implementation
```

### 5. Write Tests

**Test-driven development:**

```bash
# 1. Write failing test
echo "def test_new_feature(): assert new_feature() == expected" >> tests/test_new.py

# 2. Run test (should fail)
uv run pytest tests/test_new.py::test_new_feature

# 3. Implement feature
# Edit src/cyberian/...

# 4. Run test (should pass)
uv run pytest tests/test_new.py::test_new_feature
```

See [Testing Guide](testing.md) for details.

### 6. Run Tests and Checks

```bash
# Run all tests and checks
just test

# If any fail, fix and re-run
```

This runs:

- pytest
- mypy (type checking)
- ruff (linting and formatting)

### 7. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature to support X

- Implement Y
- Add tests for Z
- Update documentation"
```

**Commit message format:**

```
Short summary (50 chars or less)

Longer explanation if needed:
- Bullet points for changes
- Why the change was made
- Any breaking changes

Fixes #123
```

### 8. Push and Create PR

```bash
# Push to your fork
git push origin feature/my-feature
```

Then on GitHub:

1. Go to your fork
2. Click "Pull Request"
3. Fill in description
4. Submit

**PR Description Template:**

```markdown
## Summary

Brief description of changes.

## Changes

- Change 1
- Change 2
- Change 3

## Testing

How was this tested?

## Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests passing
- [ ] Type checking passing
```

## Contribution Guidelines

### Code Quality

- **Type hints** - All functions should have type hints
- **Docstrings** - All public functions should have docstrings
- **Tests** - All features should have tests
- **No mocks** - Test real functionality when possible

### Documentation

Update documentation for:

- New commands
- New workflow features
- Changed behavior
- New configuration options

**Update these files:**

- `docs/reference/` - Reference docs
- `docs/how-to/` - How-to guides (if applicable)
- `README.md` - If major feature
- `docs/tutorials/` - If user-facing change

### Testing

- **Write tests first** - TDD approach
- **Test real behavior** - Avoid mocks
- **Test edge cases** - Empty, large, invalid input
- **Clean up** - Stop servers, delete temp files

### Commit Messages

- **First line** - Short summary (50 chars)
- **Body** - Detailed explanation (wrap at 72 chars)
- **Reference issues** - "Fixes #123"

**Example:**

```
Add workflow loop feature

Implements looping tasks that repeat until a condition is met.

- Add loop_until field to Task model
- Implement loop detection in runner
- Add tests for various loop scenarios
- Update workflow schema documentation

Fixes #45
```

### Pull Request Process

1. **Create PR** - With clear description
2. **CI checks** - Wait for tests to pass
3. **Code review** - Address feedback
4. **Approval** - Maintainer approves
5. **Merge** - Maintainer merges

### Review Process

**Expect:**

- Constructive feedback
- Requests for changes
- Questions about approach
- Suggestions for improvements

**Respond:**

- Address all feedback
- Ask questions if unclear
- Make requested changes
- Update PR description if scope changes

## What to Contribute

### Good First Issues

Look for issues labeled `good-first-issue`:

- Documentation improvements
- Small bug fixes
- Test coverage improvements
- Example workflows

### Feature Requests

Before implementing a feature:

1. Check if issue exists
2. If not, create issue to discuss
3. Wait for maintainer feedback
4. Implement after approval

### Bug Fixes

1. Create issue (if doesn't exist)
2. Reference issue in PR
3. Include test that reproduces bug
4. Verify fix resolves issue

### Documentation

Always welcome:

- Typo fixes
- Clarifications
- Additional examples
- New tutorials/guides

## Code Review Checklist

Before submitting, verify:

- [ ] Tests added for new features
- [ ] All tests passing (`just test`)
- [ ] Type checking passing (`just mypy`)
- [ ] Formatting correct (`just format`)
- [ ] Documentation updated
- [ ] Commit messages clear
- [ ] PR description complete
- [ ] No merge conflicts

## Getting Help

**Questions?**

- Open a [discussion](https://github.com/monarch-initiative/cyberian/discussions)
- Ask in PR comments
- Check [documentation](https://monarch-initiative.github.io/cyberian)

**Issues?**

- Open an [issue](https://github.com/monarch-initiative/cyberian/issues)
- Provide reproduction steps
- Include error messages
- Include environment details

## Code of Conduct

Be respectful:

- Welcome newcomers
- Provide constructive feedback
- Assume good intentions
- Be patient with questions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Thank You!

Every contribution helps make cyberian better. Thank you for taking the time to contribute!

## See Also

- [Setup Guide](setup.md)
- [Testing Guide](testing.md)
- [GitHub Issues](https://github.com/monarch-initiative/cyberian/issues)
- [GitHub Discussions](https://github.com/monarch-initiative/cyberian/discussions)

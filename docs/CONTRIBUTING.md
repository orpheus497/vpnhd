# Contributing to VPNHD

Thank you for your interest in contributing to VPNHD! We welcome contributions from everyone, regardless of experience level.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing Requirements](#testing-requirements)
6. [Submitting Changes](#submitting-changes)
7. [Coding Standards](#coding-standards)
8. [Documentation](#documentation)
9. [Release Process](#release-process)

## Code of Conduct

### Our Commitment

We are committed to providing a welcoming and inclusive environment for all contributors. We expect all participants to:

- Be respectful of differing opinions and experiences
- Provide constructive criticism
- Focus on what is best for the community
- Be patient and kind to others

### Unacceptable Behavior

Harassment or discrimination based on:
- Race, ethnicity, or nationality
- Gender, gender identity, or sexual orientation
- Age or disability
- Religion or belief
- Political affiliation or views

This will not be tolerated. Violators will be removed from the project.

## Getting Started

### Ways to Contribute

1. **Report bugs**: File issues with detailed information
2. **Suggest features**: Propose new functionality
3. **Fix bugs**: Implement solutions for reported issues
4. **Add features**: Implement community-requested features
5. **Improve docs**: Enhance or fix documentation
6. **Test**: Test on different systems and provide feedback
7. **Translate**: Translate documentation (future versions)

### Finding Issues to Work On

- **Good first issue**: Issues tagged `good-first-issue`
- **Help wanted**: Issues tagged `help-wanted`
- **Feature requests**: Issues tagged `enhancement`
- **Bug reports**: Issues tagged `bug`

Look for issues that interest you and leave a comment saying you'd like to work on it.

## Development Setup

### Prerequisites

- Python 3.11 or higher (required for Debian 13 compatibility)
- Git
- Debian 12 or 13 (for testing)
- Virtual environment tool (venv or conda)

### Clone Repository

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/vpnhd.git
cd vpnhd

# Add upstream remote
git remote add upstream https://github.com/orpheus497/vpnhd.git
```

### Create Virtual Environment

```bash
# Create environment
python3 -m venv venv

# Activate environment
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

### Install Development Dependencies

```bash
# Install development requirements
pip install -r requirements-dev.txt

# Install package in editable mode
pip install -e .

# Verify installation
vpnhd --version
```

### Install Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks on all files
pre-commit run --all-files
```

## Making Changes

### Create a Feature Branch

```bash
# Update main branch
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix-name
```

### Branch Naming

- **Features**: `feature/short-description`
- **Bug fixes**: `fix/short-description`
- **Documentation**: `docs/short-description`
- **Tests**: `test/short-description`

### Commit Messages

Write clear, descriptive commit messages:

```
Short summary (50 chars or less)

Detailed explanation of what changed and why.
Include any relevant issue numbers: fixes #123

- Bullet points for multiple changes
- Use imperative mood ("add" not "adds")
- Be concise but descriptive
```

### Commit Guidelines

- **One logical change per commit**
- **Small, focused commits**
- **Test locally before committing**
- **Update documentation with code changes**
- **Reference issues in commit messages**

## Testing Requirements

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_cli.py

# Run with coverage
pytest --cov=src/vpnhd

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_cli.py::test_main_menu
```

### Test Coverage

- **Minimum**: 80% code coverage
- **Aim for**: 90%+ coverage
- **Tools**: pytest, pytest-cov

### Writing Tests

Tests go in `tests/` directory following naming conventions:

```python
# tests/test_module.py
import pytest
from vpnhd.module import function

def test_function_returns_expected_value():
    """Test that function returns expected value."""
    result = function("input")
    assert result == "expected_output"

def test_function_handles_error():
    """Test that function handles errors correctly."""
    with pytest.raises(ValueError):
        function("invalid_input")
```

### Manual Testing

For changes requiring system access:

1. Test on clean Debian 12 VM
2. Test each phase sequentially
3. Verify configuration file created correctly
4. Test error handling and recovery
5. Document test results

### Testing on Different Systems

If possible, test on:

- Different Debian versions (12, 11, 10)
- Different hardware (VM, physical, ARM/x86)
- Different network configurations
- Different client types (Fedora, Pop!_OS, Android)

## Submitting Changes

### Before Submitting

- [ ] Code follows style guide
- [ ] Tests pass locally (`pytest`)
- [ ] Coverage is 80%+
- [ ] Documentation is updated
- [ ] Commits are clean and well-described
- [ ] No unrelated changes in PR

### Pull Request Process

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Go to GitHub and create PR
   - Title should be concise and descriptive
   - Reference any related issues: "Fixes #123"

3. **PR Description**
   ```markdown
   ## Description
   Brief description of changes.

   ## Related Issues
   Fixes #123
   Related to #456

   ## Changes Made
   - Bullet point summary of changes
   - One item per line
   - Clear and concise

   ## Testing
   How to test these changes:
   - Step 1
   - Step 2
   - Expected result

   ## Checklist
   - [ ] Tests pass
   - [ ] Coverage is 80%+
   - [ ] Docs updated
   - [ ] No breaking changes
   ```

4. **Review Process**
   - Maintainers will review within 3-5 days
   - Address feedback and re-request review
   - Squash commits if requested
   - PR merged when approved

### PR Guidelines

- **One feature per PR** (not multiple features)
- **Keep PRs focused** (under 400 lines if possible)
- **Explain the "why"** not just the "what"
- **Link to related issues**
- **Be responsive** to feedback
- **Keep discussion respectful**

## Coding Standards

### Python Style

VPNHD uses PEP 8 with these guidelines:

- **Line length**: 100 characters (maximum)
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Imports**: Organized in groups (stdlib, third-party, local)
- **Docstrings**: Google-style docstrings for all public functions

### Linting

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check style
flake8 src/ tests/

# Type checking
mypy src/
```

### Code Example

```python
"""Module docstring describing purpose."""

from typing import Optional
from datetime import datetime

import click
from rich.console import Console

from vpnhd.config import ConfigManager


class WireGuardManager:
    """Manages WireGuard configuration and operations."""

    def __init__(self, config: ConfigManager) -> None:
        """Initialize WireGuard manager.

        Args:
            config: Configuration manager instance.
        """
        self.config = config
        self.console = Console()

    def generate_keys(self, key_name: str) -> tuple[str, str]:
        """Generate WireGuard public/private key pair.

        Args:
            key_name: Name for the key pair.

        Returns:
            Tuple of (public_key, private_key).

        Raises:
            RuntimeError: If key generation fails.
        """
        # Implementation here
        pass

    def _validate_key(self, key: str) -> bool:
        """Validate WireGuard key format (private).

        Args:
            key: Key string to validate.

        Returns:
            True if valid, False otherwise.
        """
        # Implementation here
        pass
```

### Type Hints

Use type hints for all functions:

```python
def process_data(
    data: list[str],
    count: int,
    optional: Optional[str] = None
) -> dict[str, any]:
    """Process data."""
    pass
```

## Documentation

### Documentation Files

- **README.md**: Project overview and quick start
- **USER_GUIDE.md**: Comprehensive user guide
- **TROUBLESHOOTING.md**: Common issues and solutions
- **FAQ.md**: Frequently asked questions
- **CONTRIBUTING.md**: Contribution guidelines (this file)
- **Code comments**: Inline documentation

### Updating Documentation

When making changes:

1. Update relevant documentation files
2. Update docstrings if changing functions
3. Update README if changing CLI interface
4. Update CHANGELOG.md with your changes
5. Check for broken links

### Documentation Style

- **Clarity**: Write for beginners (explain concepts)
- **Examples**: Provide code examples
- **Structure**: Use headers and lists
- **Accuracy**: Test examples before documenting
- **Tone**: Friendly and helpful, not condescending

### Code Comments

```python
# Good: Explains why
# Check if enough time has passed to prevent rate limiting
if (datetime.now() - last_request).seconds < min_interval:
    return

# Bad: Explains what (code already does this)
# Set count to 0
count = 0

# Good: Explains non-obvious logic
# Use hardcoded port for consistency across installations
# (some users may have restricted port access)
WIREGUARD_PORT = 51820
```

## Release Process

### Version Numbers

VPNHD uses semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Preparing a Release

1. **Update version number**
   - `src/vpnhd/__version__.py`
   - `setup.py`
   - `pyproject.toml`

2. **Update CHANGELOG.md**
   - List all changes
   - Credit contributors
   - Include version and date

3. **Run full test suite**
   ```bash
   pytest --cov=src/vpnhd --cov-report=html
   ```

4. **Create git tag**
   ```bash
   git tag -a v1.2.3 -m "Version 1.2.3"
   git push origin v1.2.3
   ```

5. **Build distribution**
   ```bash
   python -m build
   ```

6. **Upload to PyPI**
   ```bash
   python -m twine upload dist/*
   ```

## Common Contribution Examples

### Reporting a Bug

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
1. Run: `sudo vpnhd --phase 2`
2. Enter value: `10.0.0.0/24`
3. Observe: Error message appears

**Expected behavior**
Configuration should accept the VPN subnet.

**Actual behavior**
Error: "Invalid subnet format"

**System info**
- OS: Debian 12.1
- Python: 3.10.5
- VPNHD: 1.0.0

**Logs**
[Paste relevant log output]
```

### Suggesting a Feature

```markdown
**Is your feature request related to a problem?**
Yes, I want to [specific goal].

**Describe the solution you'd like**
[Description of desired feature]

**Describe alternatives you've considered**
[Other solutions you've thought of]

**Additional context**
[Any other context or screenshots]
```

### Creating a PR for a New Feature

1. Create feature branch
2. Implement feature with tests
3. Update documentation
4. Create PR with clear description
5. Respond to review feedback
6. Get approved and merged!

## Getting Help

### Questions About Contributing

- **GitHub Discussions**: Ask questions in discussions tab
- **GitHub Issues**: Ask in issue comments
- **Documentation**: Check USER_GUIDE and FAQ first

### Mentorship

- First-time contributor? Ask for guidance
- Maintainers happy to help with:
  - Understanding codebase
  - Testing procedures
  - Design decisions
  - PR feedback

## Recognition

All contributors are recognized in:

- **CHANGELOG.md**: Mentioned by contribution type
- **GitHub**: Shows up in contributor list
- **Comments**: Mentioned in relevant PR/issue

## License

By contributing, you agree that your contributions will be licensed under the GPL-3.0 License. This ensures VPNHD remains free and open source forever.

---

**Thank you for contributing to VPNHD!**

We appreciate your time and effort in making privacy-focused VPN setup accessible to everyone.

Questions? [Create an issue](https://github.com/orpheus497/vpnhd/issues) or start a discussion!

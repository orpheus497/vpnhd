# VPNHD Test Suite

Comprehensive test suite for the VPN Helper Daemon (VPNHD) project.

## Overview

This test suite provides:
- **100% coverage** of security-critical modules (validators, command execution)
- **80%+ overall coverage** target
- **Unit tests** for individual components
- **Integration tests** for component interactions
- **Security tests** for injection prevention

## Test Structure

```
tests/
├── unit/                      # Unit tests (fast, isolated)
│   ├── test_validators.py     # Security validators (100% coverage)
│   ├── test_commands.py        # Command execution security
│   ├── test_interfaces.py      # Network interface management
│   └── test_packages.py        # Package manager security
├── integration/                # Integration tests
│   └── test_phase_integration.py  # Phase workflow tests
├── fixtures/                   # Test data and fixtures
└── conftest.py                 # Pytest configuration and fixtures

## Running Tests

### Quick Start

```bash
# Run all tests with coverage
./run_tests.sh

# Run only unit tests
./run_tests.sh --unit-only

# Run only integration tests
./run_tests.sh --integration-only

# Run only security tests
./run_tests.sh --security-only

# Quick run (stop on first failure, no coverage)
./run_tests.sh --quick
```

### Using pytest directly

```bash
# All tests with coverage
pytest

# Specific test file
pytest tests/unit/test_validators.py

# Specific test class
pytest tests/unit/test_validators.py::TestHostnameValidator

# Specific test
pytest tests/unit/test_validators.py::TestHostnameValidator::test_valid_simple_hostnames

# With verbose output
pytest -vv

# With markers
pytest -m security          # Only security tests
pytest -m unit              # Only unit tests
pytest -m integration       # Only integration tests
```

## Coverage Reports

### Viewing Coverage

After running tests with coverage:

```bash
# HTML report (recommended)
firefox htmlcov/index.html
# or
xdg-open htmlcov/index.html

# Terminal report
pytest --cov=src/vpnhd --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=src/vpnhd --cov-report=xml
```

### Coverage Requirements

- **Overall**: 80%+ coverage required
- **Security modules**: 100% coverage target
  - `src/vpnhd/security/validators.py`
  - `src/vpnhd/system/commands.py`
- **Network modules**: 80%+ coverage
- **Phase modules**: 70%+ coverage

## Test Categories

### Unit Tests

Fast, isolated tests for individual functions/classes:
- Input validation
- Command execution
- Network interface operations
- Package management
- Error handling

### Integration Tests

Tests for component interactions:
- Phase workflows
- Multi-module operations
- End-to-end scenarios
- Error propagation
- Recovery mechanisms

### Security Tests

Critical security validation tests:
- Command injection prevention
- Input sanitization
- Validation enforcement
- Safe command execution

## Writing New Tests

### Test File Naming

- Unit tests: `tests/unit/test_<module>.py`
- Integration tests: `tests/integration/test_<feature>_integration.py`

### Test Function Naming

```python
def test_<what_is_being_tested>():
    """Clear docstring explaining the test."""
    # Arrange
    # Act
    # Assert
```

### Using Fixtures

```python
def test_with_valid_interface_names(valid_interface_names):
    """Test using fixture from conftest.py"""
    for interface in valid_interface_names:
        assert is_valid_interface_name(interface)
```

### Mocking

```python
def test_with_mocking(mocker):
    """Test with mocked dependencies."""
    mock_cmd = mocker.patch('vpnhd.system.commands.execute_command')
    mock_cmd.return_value = mocker.Mock(
        success=True,
        exit_code=0,
        stdout="output",
        stderr=""
    )
    # Test code here
```

## Test Markers

Mark tests with decorators:

```python
@pytest.mark.unit
def test_something():
    """Unit test"""
    pass

@pytest.mark.integration
def test_workflow():
    """Integration test"""
    pass

@pytest.mark.security
def test_injection_prevention():
    """Security test"""
    pass

@pytest.mark.slow
def test_long_running():
    """Slow test (skipped in quick runs)"""
    pass
```

## CI/CD Integration

Tests are configured for CI/CD with:
- XML coverage reports (`coverage.xml`)
- JUnit XML output
- Exit codes for pass/fail

Example GitHub Actions:

```yaml
- name: Run tests
  run: |
    pip install pytest pytest-cov pytest-mock
    pytest --cov=src/vpnhd --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Dependencies

Required packages:
```bash
pip install pytest pytest-cov pytest-mock
```

Or use the project's dev requirements:
```bash
pip install -e ".[dev]"
```

## Troubleshooting

### Tests fail with import errors

```bash
# Install package in development mode
pip install -e .
```

### Coverage not showing

```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Clear old coverage data
rm -rf .coverage htmlcov coverage.xml
```

### Slow test runs

```bash
# Run quick tests only
./run_tests.sh --quick

# Skip slow tests
pytest -m "not slow"
```

## Best Practices

1. **Always mock external dependencies** (file system, network, commands)
2. **Test both success and failure paths**
3. **Include edge cases** (empty strings, max lengths, unicode)
4. **Verify security** (injection attempts, validation)
5. **Keep tests fast** (use mocks, avoid actual I/O)
6. **Write clear docstrings** (explain what is being tested)
7. **Use descriptive assertions** (meaningful error messages)

## Security Testing

All security-critical code paths must have tests that verify:
- ✓ Valid inputs are accepted
- ✓ Invalid inputs are rejected
- ✓ Injection attempts are blocked
- ✓ Commands use array format (no shell=True)
- ✓ Validators are called before system operations

Example:
```python
def test_injection_prevention(mocker):
    """Test that malicious input is rejected."""
    with pytest.raises(ValidationError):
        NetworkInterface("eth0; rm -rf /")
```

## Continuous Improvement

- Add tests for new features
- Increase coverage for uncovered code
- Update tests when fixing bugs
- Review test failures in CI/CD
- Refactor slow tests

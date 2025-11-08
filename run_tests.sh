#!/bin/bash
# Script to run VPNHD tests with coverage reporting

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  VPNHD Test Suite Runner${NC}"
echo -e "${BLUE}======================================${NC}"
echo

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-cov pytest-mock"
    exit 1
fi

# Parse command line arguments
PYTEST_ARGS=""
RUN_UNIT=true
RUN_INTEGRATION=true
SHOW_COVERAGE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit-only)
            RUN_INTEGRATION=false
            PYTEST_ARGS="$PYTEST_ARGS -m unit"
            shift
            ;;
        --integration-only)
            RUN_UNIT=false
            PYTEST_ARGS="$PYTEST_ARGS -m integration"
            shift
            ;;
        --security-only)
            PYTEST_ARGS="$PYTEST_ARGS -m security"
            shift
            ;;
        --no-coverage)
            SHOW_COVERAGE=false
            PYTEST_ARGS="$PYTEST_ARGS --no-cov"
            shift
            ;;
        --verbose)
            PYTEST_ARGS="$PYTEST_ARGS -vv"
            shift
            ;;
        --quick)
            PYTEST_ARGS="$PYTEST_ARGS -x --no-cov"
            SHOW_COVERAGE=false
            shift
            ;;
        --help)
            echo "Usage: ./run_tests.sh [OPTIONS]"
            echo
            echo "Options:"
            echo "  --unit-only         Run only unit tests"
            echo "  --integration-only  Run only integration tests"
            echo "  --security-only     Run only security tests"
            echo "  --no-coverage       Skip coverage reporting"
            echo "  --verbose           Verbose output (-vv)"
            echo "  --quick             Quick run (stop on first failure, no coverage)"
            echo "  --help              Show this help message"
            echo
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Clean previous coverage data
if [ "$SHOW_COVERAGE" = true ]; then
    echo -e "${YELLOW}Cleaning previous coverage data...${NC}"
    rm -rf .coverage htmlcov coverage.xml
fi

# Run tests
echo -e "${BLUE}Running tests...${NC}"
echo

if pytest $PYTEST_ARGS; then
    echo
    echo -e "${GREEN}✓ All tests passed!${NC}"
    EXIT_CODE=0
else
    echo
    echo -e "${RED}✗ Some tests failed${NC}"
    EXIT_CODE=1
fi

# Show coverage summary
if [ "$SHOW_COVERAGE" = true ] && [ $EXIT_CODE -eq 0 ]; then
    echo
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}  Coverage Summary${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo

    # Check if HTML coverage report was generated
    if [ -d "htmlcov" ]; then
        echo -e "${GREEN}HTML coverage report generated in: htmlcov/index.html${NC}"
        echo -e "Open with: ${YELLOW}firefox htmlcov/index.html${NC} or ${YELLOW}xdg-open htmlcov/index.html${NC}"
    fi

    # Check if XML coverage report was generated (for CI/CD)
    if [ -f "coverage.xml" ]; then
        echo -e "${GREEN}XML coverage report generated: coverage.xml${NC}"
    fi

    echo
fi

# Exit with test result code
exit $EXIT_CODE

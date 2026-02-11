#!/bin/bash

# IntelliSearch Standard MCP Toolkit Test Runner
# Usage: bash run_standard_test.sh [server_name1] [server_name2] ...
#
# Examples:
#   bash run_standard_test.sh base_toolkit
#   bash run_standard_test.sh base_toolkit search_scholar
#   bash run_standard_test.sh  # Run all tests if no servers specified

# Check if arguments are provided
if [ $# -eq 0 ]; then
    echo "Running all tests..."
    pytest -n auto
    exit $?
fi

# Build pytest filter expression
FILTER_EXPRESSION=""
SERVER_COUNT=0

for arg in "$@"; do
    if [ $SERVER_COUNT -eq 0 ]; then
        FILTER_EXPRESSION="$arg"
    else
        FILTER_EXPRESSION="$FILTER_EXPRESSION or $arg"
    fi
    SERVER_COUNT=$((SERVER_COUNT + 1))
done

pytest -k "$FILTER_EXPRESSION" -n 4 -x

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed!"

    # Show latest test result file
    LATEST_RESULT=$(ls -t test/test_results/test_results_*.json 2>/dev/null | head -1)
    if [ -n "$LATEST_RESULT" ]; then
        echo "Test results: $LATEST_RESULT"
    fi
else
    echo "✗ Some tests failed."
fi

exit $TEST_EXIT_CODE

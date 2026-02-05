#!/bin/bash

# IntelliSearch Setup Script
# This script checks the environment and prepares the configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the absolute path of the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_VENV_PYTHON="${PROJECT_DIR}/.venv/bin/python"

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}IntelliSearch Setup Script${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""
echo -e "Project directory: ${GREEN}${PROJECT_DIR}${NC}"
echo ""

# Function to check if uv is installed
check_uv() {
    echo -n "Checking uv installation... "
    if command -v uv &> /dev/null; then
        echo -e "${GREEN}OK${NC} ($(uv --version))"
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}Error: uv is not installed${NC}"
        echo ""
        echo "Please install uv first:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo ""
        return 1
    fi
}

# Function to check virtual environment
check_venv() {
    echo -n "Checking virtual environment... "

    if [ ! -d "${PROJECT_DIR}/.venv" ]; then
        echo -e "${YELLOW}NOT FOUND${NC}"
        return 1
    fi

    if [ ! -f "${EXPECTED_VENV_PYTHON}" ]; then
        echo -e "${YELLOW}INCOMPLETE${NC}"
        return 1
    fi

    # Check if current python is from venv
    if [ -n "$VIRTUAL_ENV" ]; then
        echo -e "${GREEN}OK${NC} (already activated)"
        return 0
    else
        echo -e "${YELLOW}NOT ACTIVATED${NC}"
        return 1
    fi
}

# Function to initialize environment
init_environment() {
    echo ""
    echo -e "${YELLOW}Virtual environment not initialized or not activated${NC}"
    echo ""
    echo "Running ${GREEN}uv sync${NC} to initialize the environment..."
    echo ""

    cd "${PROJECT_DIR}"
    uv sync

    echo ""
    echo -e "${GREEN}Environment initialized successfully!${NC}"
    echo -e "Please run: ${GREEN}source .venv/bin/activate${NC}"
    echo ""
}

# Function to setup configuration file
setup_config() {
    echo ""
    echo -n "Setting up configuration file... "

    CONFIG_EXAMPLE="${PROJECT_DIR}/config/config.example.yaml"
    CONFIG_FILE="${PROJECT_DIR}/config/config.yaml"

    if [ ! -f "${CONFIG_EXAMPLE}" ]; then
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}Error: ${CONFIG_EXAMPLE} not found${NC}"
        return 1
    fi

    # Replace <YOUR_PWD> with actual project directory
    sed "s|<YOUR_PWD>|${PROJECT_DIR}|g" "${CONFIG_EXAMPLE}" > "${CONFIG_FILE}"

    echo -e "${GREEN}OK${NC}"
    echo -e "Configuration file created: ${GREEN}${CONFIG_FILE}${NC}"
    echo ""
}

# Main setup flow
main() {
    # Check uv installation
    if ! check_uv; then
        exit 1
    fi

    echo ""

    # Check virtual environment
    if ! check_venv; then
        init_environment
    fi

    # Setup configuration file
    setup_config

    # Final summary
    echo -e "${BLUE}=================================${NC}"
    echo -e "${GREEN}Setup Complete!${NC}"
    echo -e "${BLUE}=================================${NC}"
    echo ""
    echo "Next steps:"
    echo -e "  - Configure API keys in ${GREEN}config/config.yaml${NC}"
    echo -e "  - Start backend services: ${GREEN}bash start_backend.sh${NC}"
    echo -e "  - Run the application: ${GREEN}python cli.py${NC}"
    echo ""
}

# Run main function
main 
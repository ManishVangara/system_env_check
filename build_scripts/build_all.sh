#!/bin/bash
# Build executables for all platforms (requires cross-platform build setup)

set -e

echo "========================================"
echo "Building System Check Client for All Platforms"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Install/update dependencies
echo "Installing build dependencies..."
pip install -r "$PROJECT_ROOT/client_requirements.txt"
echo ""

# Build for current platform
echo "Building for current platform..."
python "$SCRIPT_DIR/build_client.py"
echo ""

echo "========================================"
echo "Build completed!"
echo "========================================"
echo ""
echo "Note: To build for other platforms, you need to run this script"
echo "on each target platform (Windows, Linux, macOS)."
echo ""
echo "Built executables are in: $PROJECT_ROOT/executables/"
echo ""

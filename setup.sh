#!/bin/bash
# Quick setup script for Unix systems

set -e

echo "========================================"
echo "System Environment Check - Quick Setup"
echo "========================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo "✓ Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install server dependencies
echo "Installing server dependencies..."
pip install -q -r requirements.txt
echo "✓ Server dependencies installed"
echo ""

# Install build dependencies
echo "Installing build dependencies..."
pip install -q -r client_requirements.txt
echo "✓ Build dependencies installed"
echo ""

# Build client executable
echo "Building client executable for current platform..."
python build_scripts/build_client.py

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To start the server, run:"
echo "  source venv/bin/activate"
echo "  python server/app.py"
echo ""
echo "Then open your browser to http://localhost:5000"
echo ""

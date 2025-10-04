#!/bin/bash
# moreStacks Banking Setup Script for Linux/macOS
# Automatically installs dependencies and launches the application

echo "============================================================"
echo "  moreStacks Banking - Setup Script"
echo "  Banking Made Simple"
echo "============================================================"
echo ""

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "   Please install Python 3.7 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION detected"
echo ""

# Install dependencies
echo "Installing dependencies..."
echo "This may take a minute..."
echo ""

python3 -m pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All dependencies installed successfully!"
    echo ""
else
    echo "❌ Error installing dependencies"
    echo "   Please try manually: pip3 install -r requirements.txt"
    exit 1
fi

# Launch the app
echo "============================================================"
echo "  🚀 Launching moreStacks Banking..."
echo "============================================================"
echo ""

python3 main.py

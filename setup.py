#!/usr/bin/env python3
"""
moreStacks Banking Setup Script
Automatically installs dependencies and launches the application
"""

import subprocess
import sys
import os


def print_header():
    """Print welcome header."""
    print("=" * 60)
    print("  moreStacks Banking - Setup Script")
    print("  Banking Made Simple")
    print("=" * 60)
    print()


def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...")
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required.")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    print()


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    print("This may take a minute...")
    print()

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        print()
        print("✅ All dependencies installed successfully!")
        print()
    except subprocess.CalledProcessError:
        print("❌ Error installing dependencies.")
        print("   Please try manually: pip install -r requirements.txt")
        sys.exit(1)


def launch_app():
    """Launch the banking application."""
    print("=" * 60)
    print("  🚀 Launching moreStacks Banking...")
    print("=" * 60)
    print()

    try:
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for using moreStacks Banking!")
        sys.exit(0)


def main():
    """Main setup flow."""
    print_header()
    check_python_version()

    # Check if dependencies are already installed
    try:
        import matplotlib

        print("✅ Dependencies already installed")
        print()
    except ImportError:
        install_dependencies()

    launch_app()


if __name__ == "__main__":
    main()

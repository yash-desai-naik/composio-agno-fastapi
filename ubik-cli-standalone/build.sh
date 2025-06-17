#!/bin/bash
set -e

# Install build requirements
pip install -r requirements-build.txt

# Build the binary
pyinstaller --onefile --name ubik-py cli.py

# Copy the binary to /usr/local/bin for easy access
if [ -f "dist/ubik-py" ]; then
    echo "Build successful! The binary is at dist/ubik-py"
    echo "To install system-wide, run: sudo cp dist/ubik-py /usr/local/bin/"
else
    echo "Build failed!"
    exit 1
fi

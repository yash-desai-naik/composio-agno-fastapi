#!/bin/bash
set -e

echo "Installing ubik-py CLI dependencies..."

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install build dependencies
pip install --upgrade pip wheel setuptools

# Install main dependencies
pip install openai requests mcp python-dotenv pydantic

# Install agno from source if available, otherwise try pip
if [ -d "../agno" ]; then
    echo "Installing agno from local source..."
    pip install -e ../agno
else
    pip install agno
fi

# Install composio-agno from source if available, otherwise try pip
if [ -d "../composio-agno" ]; then
    echo "Installing composio-agno from local source..."
    pip install -e ../composio-agno
else
    pip install composio-agno
fi

# Install any remaining requirements
pip install -r requirements.txt

echo "Dependencies installed successfully"

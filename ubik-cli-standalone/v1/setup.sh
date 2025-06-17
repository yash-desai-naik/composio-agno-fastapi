#!/bin/bash

# Ubik AI - One-Click Setup Script
# This script sets up everything needed to build the standalone Ubik AI executable

echo "🚀 Ubik AI - One-Click Setup"
echo "============================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

# Use pip3 if available, otherwise use pip
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

echo "✅ pip found: $($PIP_CMD --version)"

# Create virtual environment (optional but recommended)
echo "📦 Setting up virtual environment..."
python3 -m venv ubik_env

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source ubik_env/Scripts/activate
else
    # macOS/Linux
    source ubik_env/bin/activate
fi

echo "✅ Virtual environment activated"

# Upgrade pip
echo "⬆️  Upgrading pip..."
$PIP_CMD install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
$PIP_CMD install -r requirements.txt

echo "✅ Dependencies installed successfully!"

# Build the executable
echo "🏗️  Building standalone executable..."
python3 build.py

# Check if build was successful
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    EXECUTABLE="dist/ubik.exe"
else
    EXECUTABLE="dist/ubik"
fi

if [ -f "$EXECUTABLE" ]; then
    echo "🎉 Build successful!"
    echo "📍 Your Ubik AI executable is at: $EXECUTABLE"
    echo ""
    echo "📖 Quick Start:"
    echo "1. Get your API keys:"
    echo "   - OpenAI API key from: https://platform.openai.com/api-keys"
    echo "   - Composio API key from: https://app.composio.dev/api-keys"
    echo ""
    echo "2. Test the app:"
    echo "   $EXECUTABLE --list_apps --composio_api_key=YOUR_COMPOSIO_KEY"
    echo ""
    echo "3. Connect your accounts:"
    echo "   $EXECUTABLE --connect_app=gmail --entity_id=you@email.com --composio_api_key=YOUR_COMPOSIO_KEY"
    echo ""
    echo "4. Ask AI questions:"
    echo "   $EXECUTABLE --query=\"what's the weather?\" --entity_id=you@email.com --openai_key=YOUR_OPENAI_KEY --composio_api_key=YOUR_COMPOSIO_KEY"
    echo ""
    echo "🚀 You're all set! Enjoy Ubik AI!"
else
    echo "❌ Build failed. Please check the error messages above."
    exit 1
fi
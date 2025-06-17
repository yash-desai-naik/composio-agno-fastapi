@echo off
REM Ubik AI - Windows One-Click Setup Script

echo 🚀 Ubik AI - One-Click Setup
echo =============================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed. Please reinstall Python with pip included.
    pause
    exit /b 1
)

echo ✅ pip found
pip --version

REM Create virtual environment
echo 📦 Setting up virtual environment...
python -m venv ubik_env

REM Activate virtual environment
call ubik_env\Scripts\activate.bat

echo ✅ Virtual environment activated

REM Upgrade pip
echo ⬆️ Upgrading pip...
pip install --upgrade pip

REM Install requirements
echo 📚 Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully!

REM Build the executable
echo 🏗️ Building standalone executable...
python build.py

REM Check if build was successful
if exist "dist\ubik.exe" (
    echo 🎉 Build successful!
    echo 📍 Your Ubik AI executable is at: dist\ubik.exe
    echo.
    echo 📖 Quick Start:
    echo 1. Get your API keys:
    echo    - OpenAI API key from: https://platform.openai.com/api-keys
    echo    - Composio API key from: https://app.composio.dev/api-keys
    echo.
    echo 2. Test the app:
    echo    dist\ubik.exe --list_apps --composio_api_key=YOUR_COMPOSIO_KEY
    echo.
    echo 3. Connect your accounts:
    echo    dist\ubik.exe --connect_app=gmail --entity_id=you@email.com --composio_api_key=YOUR_COMPOSIO_KEY
    echo.
    echo 4. Ask AI questions:
    echo    dist\ubik.exe --query="what's the weather?" --entity_id=you@email.com --openai_key=YOUR_OPENAI_KEY --composio_api_key=YOUR_COMPOSIO_KEY
    echo.
    echo 🚀 You're all set! Enjoy Ubik AI!
) else (
    echo ❌ Build failed. Please check the error messages above.
    pause
    exit /b 1
)

pause
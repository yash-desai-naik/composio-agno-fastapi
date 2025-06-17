# 🤖 Ubik AI - Your Personal Assistant

A standalone CLI app that connects to Gmail, Google Calendar, Google Drive, weather services, and web search - all powered by AI. No complex setup, no environment variables to manage.

## ✨ Features

- **Smart Agent Selection**: AI automatically chooses the right tools for your request
- **Email Management**: Check, send, and manage Gmail
- **Calendar Integration**: View and manage Google Calendar events  
- **File Operations**: Save data to local files when needed
- **Weather Information**: Get current weather for any location
- **Web Search**: Search the web for information
- **Google Drive**: Manage files and folders in Google Drive
- **Standalone**: Single executable file - no Python environment needed

## 📦 Distribution & Deployment

### For Developers
After building the executable, you'll find it in the `dist/` folder. This single file contains everything needed to run Ubik AI.

### For End Users
You receive a single executable file (`ubik` or `ubik.exe`) - no Python installation or setup required!

#### Platform Compatibility
- **Same Architecture**: Executable built on Mac M1 only works on Mac M1/M2
- **Cross-Platform**: Use GitHub Actions workflow to build for all platforms:
  - `ubik-linux` (Intel/AMD Linux)
  - `ubik-macos-intel` (Intel Macs)  
  - `ubik-macos-arm64` (M1/M2 Macs)
  - `ubik-windows.exe` (Windows)

#### System Requirements
- **Core Features**: No additional requirements
- **File Operations**: Node.js required (for saving files, file searches, etc.)
  - Install from: https://nodejs.org
  - Only needed if using `--query` requests that involve file operations

#### macOS Security Setup
Fresh Mac may show security warning. Choose one:

**Option 1 - Remove Quarantine:**
```bash
xattr -d com.apple.quarantine ubik
```

**Option 2 - System Preferences:**
1. Try to run `ubik`
2. Go to System Preferences → Security & Privacy
3. Click "Allow Anyway" for ubik

#### Linux Setup
```bash
# Make executable
chmod +x ubik

# Run
./ubik --list_apps --composio_api_key=YOUR_KEY
```

#### Windows Setup
```batch
REM No setup needed - just run
ubik.exe --list_apps --composio_api_key=YOUR_KEY
```

## 🚀 Quick Start

### Option 1: Get Pre-Built Executable (Recommended for Users)
1. **Download** the appropriate executable for your system:
   - Linux: `ubik-linux`
   - macOS Intel: `ubik-macos-intel`
   - macOS M1/M2: `ubik-macos-arm64`
   - Windows: `ubik-windows.exe`

2. **Setup** (see Platform Compatibility section above)

3. **Get API Keys** (see Getting API Keys section below)

4. **Start Using** (see Usage section below)

### Option 2: Build From Source (For Developers)

**Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```batch
setup.bat
```

### Option 2: Build From Source (For Developers)

**One-Click Setup:**

**Linux/macOS:**

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Build Executable:**
```bash
python build.py
```

## 📖 Usage

### 1. List Available Apps
```bash
ubik --list_apps --composio_api_key=YOUR_COMPOSIO_KEY
```

### 2. Connect Your Accounts
```bash
# Connect Gmail
ubik --connect_app=gmail --entity_id=you@email.com --composio_api_key=YOUR_COMPOSIO_KEY

# Connect Google Calendar  
ubik --connect_app=googlecalendar --entity_id=you@email.com --composio_api_key=YOUR_COMPOSIO_KEY

# Connect Google Drive
ubik --connect_app=googledrive --entity_id=you@email.com --composio_api_key=YOUR_COMPOSIO_KEY
```

### 3. Check Connected Apps
```bash
ubik --list_connected_apps --entity_id=you@email.com --composio_api_key=YOUR_COMPOSIO_KEY
```

### 4. Ask AI Questions
```bash
# Simple weather query
ubik --query="what's the weather in Berlin?" --entity_id=you@email.com --openai_key=sk-xxx --composio_api_key=xxx

# Check schedule and emails
ubik --query="what's on my plate today? And check my emails from Kevin" --entity_id=you@email.com --openai_key=sk-xxx --composio_api_key=xxx

# Search and save to file
ubik --query="search for best laptops 2025 and save to my desktop" --entity_id=you@email.com --openai_key=sk-xxx --composio_api_key=xxx
```

## 🔑 Getting API Keys

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### Composio API Key  
1. Go to [Composio Dashboard](https://app.composio.dev/api-keys)
2. Sign in or create an account
3. Click "Generate API Key"
4. Copy the key

## 📱 Supported Apps

### OAuth Apps (Need Authentication)
- **Gmail** - Email management
- **Google Calendar** - Schedule management
- **Google Drive** - File storage and management
- **GitHub** - Repository management

### No-Auth Apps (Ready to Use)
- **Weather** - Weather information
- **Web Search** - DuckDuckGo, Google, news search
- **File System** - Local file operations

## 💡 Example Queries

### Weather
```bash
ubik --query="weather in Tokyo" --entity_id=you@email.com --openai_key=sk-xxx --composio_api_key=xxx
```

### Email + Calendar
```bash  
ubik --query="check my schedule today and any urgent emails" --entity_id=you@email.com --openai_key=sk-xxx --composio_api_key=xxx
```

### Search + Save
```bash
ubik --query="find news about AI developments and save summary to ~/ai_news.txt" --entity_id=you@email.com --openai_key=sk-xxx --composio_api_key=xxx
```

### Drive Management
```bash
ubik --query="create a folder called 'Project 2025' in my Google Drive" --entity_id=you@email.com --openai_key=sk-xxx --composio_api_key=xxx
```

## 🛠️ Technical Details

### Built With
- **Agno Framework** - AI agent orchestration
- **Composio** - Tool integration platform  
- **OpenAI GPT-4** - Language model
- **PyInstaller** - Standalone executable creation

### File Structure
```
ubik/
├── ubik.py           # Main CLI application
├── ubik_tools.py     # Tool configurations
├── requirements.txt  # Python dependencies
├── build.py         # Build script for executable
├── setup.sh         # Linux/macOS setup script
├── setup.bat        # Windows setup script
└── README.md        # This file
```

### Smart Agent Selection
The AI automatically selects the right combination of agents based on your query:
- **Gmail Agent** - For email-related tasks
- **Calendar Agent** - For schedule management
- **Weather Agent** - For weather information
- **Search Agent** - For web searches
- **Drive Agent** - For Google Drive operations
- **File System Agent** - For local file operations

## 🔧 Troubleshooting

### Distribution Issues

**"App can't be opened" (macOS):**
```bash
xattr -d com.apple.quarantine ubik
```

**"Permission denied" (Linux):**
```bash
chmod +x ubik
```

**File operations not working:**
- Install Node.js from https://nodejs.org
- File operations require `npx` command to be available

**Cross-platform compatibility:**
- Executables are platform-specific
- Use GitHub Actions workflow to build for all platforms
- Don't try to run Linux executable on macOS or vice versa

### Build Issues
If the build fails:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Try the basic build: `pyinstaller --onefile ubik.py`
3. Check Python version (3.8+ required)

### Connection Issues
If app connections fail:
1. Verify your Composio API key is correct
2. Make sure you've completed the OAuth flow via the provided URL
3. Check your entity_id is consistent across commands

### Query Issues
If queries don't work properly:
1. Verify your OpenAI API key is correct and has credits
2. Ensure all required accounts are connected
3. Check that your query is clear and specific

## 📝 License

This project is built using open-source frameworks and requires valid API keys from OpenAI and Composio for operation.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📞 Support

For support and questions:
1. Check this README first
2. Review the example queries above
3. Ensure your API keys are valid and have proper permissions

---

**Enjoy your AI-powered personal assistant! 🚀**
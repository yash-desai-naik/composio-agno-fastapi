# Ubik CLI

A standalone CLI tool for interacting with AI assistants and managing integrations with various services.

## Features

- List available apps (`--list_apps`)
- Connect to apps (`--connect_app`)
- List connected apps (`--list_connected_apps`)
- Process natural language queries (`--query`)

## Installation

1. Download the latest release for your platform
2. Move the binary to your PATH:
   ```bash
   sudo cp ubik-py /usr/local/bin/
   ```
3. Make it executable:
   ```bash
   sudo chmod +x /usr/local/bin/ubik-py
   ```

## Building from Source

1. Make sure you have Python and pip installed
2. Run the build script:
   ```bash
   ./build.sh
   ```
3. Install system-wide:
   ```bash
   sudo cp dist/ubik-py /usr/local/bin/
   ```

## Usage

### List Available Apps
```bash
ubik-py --list_apps --composio_api_key='xxx'
```

### Connect to an App
```bash
ubik-py --connect_app=gmail --entity_id=john@doe.com --composio_api_key='xxx'
```

### List Connected Apps
```bash
ubik-py --list_connected_apps --entity_id=john@doe.com --composio_api_key='xxx'
```

### Process a Query
```bash
ubik-py --query="what is the weather in berlin" --entity_id=john@doe.com --openai_key='sk-xxx' --composio_api_key='xxx'
```

## Notes

- OAuth apps (Gmail, Google Calendar, Google Drive) require authentication via a URL
- No-auth apps (Weather, Search) are auto-connected
- User entity ID is used to identify connections and maintain context
- OpenAI API key is only required for processing queries

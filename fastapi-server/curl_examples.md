# API Usage Examples

This document provides examples of how to use the Composio Agno API endpoints using curl commands.

## Usage Flow

1. **Create User**: First, create a user profile in the system
2. **Connect Apps**: Connect required apps before using their functionality
3. **Chat Interaction**: Start interacting with the system through chat
   - The system will remember user preferences and context
   - Each interaction helps build a better understanding of the user

## User Management

### Create a New User
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "user@example.com",
  "name": "Test User"
}'
```

### Get User Details
```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/users/user@example.com' \
  -H 'accept: application/json'
```

## App Connections

### Connect OAuth Apps (Gmail, Google Calendar)
```bash
# Connect Gmail
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/connect' \
  -H 'Content-Type: application/json' \
  -d '{
  "app_name": "gmail"
}'

# Connect Google Calendar
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/connect' \
  -H 'Content-Type: application/json' \
  -d '{
  "app_name": "googlecalendar"
}'
```

### Connect No-Auth Apps (Weather, Search)
These apps don't require OAuth authentication and are auto-connected:
```bash
# Connect Weather API
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/connect' \
  -H 'Content-Type: application/json' \
  -d '{
  "app_name": "weathermap"
}'

# Connect Search API
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/connect' \
  -H 'Content-Type: application/json' \
  -d '{
  "app_name": "composio_search"
}'
```

### List Connected Apps
```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/users/user@example.com/apps' \
  -H 'accept: application/json'
```

### Get Available Apps
```bash
# List all available apps that can be connected
curl -X 'GET' \
  'http://localhost:8000/api/v1/apps/available' \
  -H 'accept: application/json'
```

The response will show OAuth apps and no-auth apps:
```json
{
  "oauth_apps": ["gmail", "googlecalendar", "googledrive", "notion", "slack"],
  "no_auth_apps": ["weathermap", "composio_search"]
}
```

## Chat Functionality

### Basic Email Operations
```bash
# Fetch Recent Emails
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "fetch my recent 3 emails",
  "timezone": "Asia/Kolkata"
}'

# Send Email
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "send an email to example@gmail.com with subject Hello and body Testing",
  "timezone": "Asia/Kolkata"
}'
```

### Calendar Operations
```bash
# Create Calendar Event
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "create a meeting tomorrow at 2pm with title Team Sync",
  "timezone": "Asia/Kolkata"
}'

# Find Events
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "what meetings do I have tomorrow?",
  "timezone": "Asia/Kolkata"
}'
```

### Weather Operations
```bash
# Get Current Weather
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "what's the weather in London?",
  "timezone": "Asia/Kolkata"
}'

# Weather Updates via Email
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "fetch latest weather of New York and send it to example@gmail.com",
  "timezone": "Asia/Kolkata"
}'
```

### Search Operations
```bash
# General Search
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "search for latest news about artificial intelligence",
  "timezone": "Asia/Kolkata"
}'

# Specific Search with Email
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "search for tech news and email the summary to example@gmail.com",
  "timezone": "Asia/Kolkata"
}'
```

### Personal Information & Preferences
```bash
# Tell the system about yourself
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "my name is John and I prefer to have meetings in the morning",
  "timezone": "Asia/Kolkata"
}'

# The system will remember this information for future interactions
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "schedule a team meeting for tomorrow",
  "timezone": "Asia/Kolkata"
}'
```

### Combined Operations with Context
```bash
# Weather and Email (With Context)
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "get today's weather and send it to my usual email contacts",
  "timezone": "Asia/Kolkata"
}'

# Smart Calendar Management
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "find a good time for a team meeting next week based on my preferences",
  "timezone": "Asia/Kolkata"
}'
```

## Notes

### Prerequisites
1. Create a user first using the create user endpoint
2. Connect required apps before using their functionality
3. The system will start building memory after the first interaction

### Authentication
- OAuth apps (Gmail, Google Calendar, Google Drive) require authentication via a URL
- No-auth apps (Weather, Search) are auto-connected when you try to connect them

### Memory System
- The system remembers user preferences and information across sessions
- Each interaction helps build a better understanding of the user
- You can refer to previous conversations and the system will maintain context

### Best Practices
1. Start with simple queries to build context
2. Let the system know about your preferences
3. Use natural language - the system understands context
4. All timestamps are handled in the specified timezone (defaults to "Asia/Kolkata" if not provided)

### Error Handling
- If an app isn't connected, the system will prompt you to connect it first
- If the system needs clarification, it will ask follow-up questions
- You can always ask the system what it remembers about you

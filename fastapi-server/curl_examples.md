# API Usage Examples

This document provides examples of how to use the Composio Agno API endpoints using curl commands.

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

### Combined Operations
```bash
# Weather and Email
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "get the weather forecast for Paris and email it to example@gmail.com",
  "timezone": "Asia/Kolkata"
}'

# Search, Calendar, and Email
curl -X 'POST' \
  'http://localhost:8000/api/v1/users/user@example.com/chat' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "search for AI conferences, create a calendar event for the next one, and email me the details",
  "timezone": "Asia/Kolkata"
}'
```

## Notes
- Before using any app functionality (Gmail, Calendar, Weather, Search), make sure to connect the required apps first
- OAuth apps (Gmail, Google Calendar) will require authentication via a URL
- No-auth apps (Weather, Search) are auto-connected when you try to connect them
- All timestamps are handled in the specified timezone (defaults to "Asia/Kolkata" if not provided)

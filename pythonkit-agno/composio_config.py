"""Configuration module for Composio integration"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Configuration constants
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")
DEFAULT_ENTITY_ID = "kkk12"

# OAuth Apps requiring authentication
OAUTH_APPS = [
    "googlecalendar",
    "gmail", 
    "googledrive",
    # "notion", "slack"
]

# No-auth apps (ready to use without authentication)
NO_AUTH_APPS = [
    'weathermap',
    'composio_search',
]

# Agent Configuration
AGENT_CONFIG = {
    "model": "gpt-4o-mini",
    "timezone": "Asia/Kolkata",
    "add_datetime": True,
    "add_location": True,
    "markdown": True
}

# Team Configuration
TEAM_CONFIG = {
    "name": "Composio Team",
    "mode": "coordinate",
    "model": "gpt-4o-mini",
    "markdown": True,
    "enable_agentic_context": True,
    "enable_agentic_memory": True,
    "share_member_interactions": True
}
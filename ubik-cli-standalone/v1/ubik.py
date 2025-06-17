#!/usr/bin/env python3
"""
Ubik AI - Standalone CLI App
A simple AI assistant that connects to your Gmail, Calendar, Drive, and more.
"""
import asyncio
import argparse
import sys
import json
from typing import Dict, Any, List, Optional

try:
    from agno.models.openai import OpenAIChat
    from agno.agent import Agent
    from composio_agno import ComposioToolSet, Action
    from agno.team.team import Team
    from agno.tools.mcp import MCPTools
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Please install required packages:")
    print("pip install agno composio-agno openai mcp")
    sys.exit(1)


# Tool actions mapping
TOOL_ACTIONS = {
    "gmail": [
        Action.GMAIL_FETCH_EMAILS, Action.GMAIL_CREATE_EMAIL_DRAFT,
        Action.GMAIL_SEND_EMAIL, Action.GMAIL_REPLY_TO_THREAD,
        Action.GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID, Action.GMAIL_LIST_THREADS
    ],
    "googlecalendar": [
        Action.GOOGLECALENDAR_CREATE_EVENT, Action.GOOGLECALENDAR_FIND_EVENT,
        Action.GOOGLECALENDAR_LIST_CALENDARS, Action.GOOGLECALENDAR_UPDATE_EVENT,
        Action.GOOGLECALENDAR_GET_CURRENT_DATE_TIME
    ],
    "googledrive": [
        Action.GOOGLEDRIVE_FIND_FILE, Action.GOOGLEDRIVE_CREATE_FILE_FROM_TEXT,
        Action.GOOGLEDRIVE_DOWNLOAD_FILE, Action.GOOGLEDRIVE_UPLOAD_FILE,
        Action.GOOGLEDRIVE_CREATE_FOLDER
    ],
    "weathermap": [Action.WEATHERMAP_WEATHER],
    "composio_search": [
        Action.COMPOSIO_SEARCH_SEARCH, Action.COMPOSIO_SEARCH_NEWS_SEARCH,
        Action.COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH
    ]
}

# Apps that need OAuth
OAUTH_APPS = ["gmail", "googlecalendar", "googledrive"]
NO_AUTH_APPS = ["weathermap", "composio_search"]


def print_banner():
    """Print app banner"""
    print("🤖 Ubik AI - Your Personal Assistant")
    print("=" * 50)


async def smart_agent_selector(user_request: str, model) -> Dict[str, Any]:
    """AI decides which agents are needed"""
    selector = Agent(
        name="Agent Selector",
        model=model,
        instructions=[
            "Decide which agents are needed for a user request. Respond ONLY with JSON.",
            "Available agents: gmail, googlecalendar, weather, search, googledrive, filesystem",
            'Format: {"agents": ["agent1", "agent2"], "needs_filesystem": false}',
            "",
            "Examples:",
            '"check emails" -> {"agents": ["gmail"], "needs_filesystem": false}',
            '"schedule today" -> {"agents": ["googlecalendar"], "needs_filesystem": false}',
            '"weather forecast" -> {"agents": ["weather"], "needs_filesystem": false}',
            '"search and save" -> {"agents": ["search"], "needs_filesystem": true}',
        ],
    )
    
    response = await selector.arun(f"Which agents needed for: '{user_request}'")
    
    try:
        return json.loads(response.content.strip())
    except:
        return {"agents": ["search"], "needs_filesystem": False}


def check_connections(toolset: ComposioToolSet, entity_id: str, needed_agents: List[str]) -> Dict[str, bool]:
    """Check which agents have valid connections"""
    connection_status = {}
    
    for agent_type in needed_agents:
        if agent_type in OAUTH_APPS:
            try:
                entity = toolset.get_entity(entity_id)
                connections = entity.get_connections()
                
                app_mapping = {
                    "gmail": "gmail",
                    "googlecalendar": "googlecalendar", 
                    "googledrive": "googledrive"
                }
                
                app_name = app_mapping.get(agent_type, agent_type)
                
                is_connected = any(
                    getattr(conn, 'appName', '').lower() == app_name.lower() and
                    getattr(conn, 'status', '').lower() in ['active', 'connected']
                    for conn in connections
                )
                
                connection_status[agent_type] = is_connected
                
            except Exception:
                connection_status[agent_type] = False
        else:
            connection_status[agent_type] = True
    
    return connection_status


def list_all_apps(composio_api_key: str):
    """List all available apps"""
    print("📱 Available Apps:")
    print()
    
    oauth_apps = ["gmail", "googlecalendar", "googledrive", "github"]
    no_auth_apps = ["weathermap", "composio_search", "desktop_commander"]
    
    for i, app in enumerate(oauth_apps, 1):
        print(f"{i}. {app} (needs oauth)")
    
    for i, app in enumerate(no_auth_apps, len(oauth_apps) + 1):
        print(f"{i}. {app} (no oauth) (no need to connect)")


def connect_app(app_name: str, entity_id: str, composio_api_key: str):
    """Connect to an OAuth app"""
    if app_name not in OAUTH_APPS:
        print(f"❌ {app_name} doesn't need authentication")
        return
    
    try:
        toolset = ComposioToolSet(api_key=composio_api_key, entity_id=entity_id)
        entity = toolset.get_entity(entity_id)
        
        # First check if already connected
        connections = entity.get_connections()
        for conn in connections:
            conn_app = getattr(conn, 'appName', '') or getattr(conn, 'app_name', '') or getattr(conn, 'app', '')
            if conn_app and str(conn_app).lower() == app_name.lower():
                conn_status = getattr(conn, 'status', '')
                if conn_status.lower() in ['active', 'connected']:
                    connection_id = getattr(conn, 'id', None) or getattr(conn, 'connectedAccountId', None)
                    print(f"✅ Already connected to {app_name}")
                    if connection_id:
                        print(f"📋 Connection ID: {connection_id}")
                    return
        
        # Not connected, initiate new connection
        connection_request = entity.initiate_connection(app_name=app_name)
        auth_url = getattr(connection_request, 'redirectUrl', None)
        
        if auth_url:
            print(f"🔗 Please authenticate {app_name}: {auth_url}")
        else:
            print(f"❌ Failed to get auth URL for {app_name}")
            
    except Exception as e:
        print(f"❌ Error connecting {app_name}: {e}")


def list_connected_apps(entity_id: str, composio_api_key: str):
    """List all connected apps"""
    try:
        toolset = ComposioToolSet(api_key=composio_api_key, entity_id=entity_id)
        entity = toolset.get_entity(entity_id)
        connections = entity.get_connections()
        
        print("📱 Connected Apps:")
        print()
        
        # Create a dict to track connected apps
        connected_apps = {}
        for conn in connections:
            conn_app = getattr(conn, 'appName', '') or getattr(conn, 'app_name', '') or getattr(conn, 'app', '')
            conn_status = getattr(conn, 'status', '')
            connection_id = getattr(conn, 'id', None) or getattr(conn, 'connectedAccountId', None)
            
            if conn_app:
                connected_apps[conn_app.lower()] = {
                    'status': conn_status,
                    'connection_id': connection_id,
                    'is_active': conn_status.lower() in ['active', 'connected']
                }
        
        all_apps = OAUTH_APPS + NO_AUTH_APPS
        
        for i, app in enumerate(all_apps, 1):
            if app in OAUTH_APPS:
                app_info = connected_apps.get(app.lower(), {})
                is_connected = app_info.get('is_active', False)
                status = "connected" if is_connected else "not connected"
                
                if is_connected and app_info.get('connection_id'):
                    print(f"{i}. {app} ({status}) - ID: {app_info['connection_id']}")
                else:
                    print(f"{i}. {app} ({status})")
            else:
                status = "connected"  # No auth needed
                print(f"{i}. {app} ({status})")
            
    except Exception as e:
        print(f"❌ Error listing connections: {e}")


async def create_dynamic_team(user_request: str, model, toolset: ComposioToolSet):
    """Create team dynamically based on AI selection"""
    
    # Get AI selection
    selection = await smart_agent_selector(user_request, model)
    needed_agents = selection.get("agents", [])
    needs_filesystem = selection.get("needs_filesystem", False)
    
    print(f"🎯 Selected agents: {', '.join(needed_agents)}" + 
          (f" + filesystem" if needs_filesystem else ""))
    
    # Map agent names to app names
    agent_to_app = {
        "gmail": "gmail",
        "googlecalendar": "googlecalendar",
        "googledrive": "googledrive",
        "weather": "weathermap",
        "search": "composio_search"
    }
    
    # Create agents
    agents = []
    for agent_name in needed_agents:
        app_name = agent_to_app.get(agent_name, agent_name)
        
        if app_name in TOOL_ACTIONS:
            try:
                if app_name in OAUTH_APPS:
                    tools = toolset.get_tools(
                        actions=TOOL_ACTIONS[app_name], 
                        check_connected_accounts=True
                    )
                else:
                    tools = toolset.get_tools(actions=TOOL_ACTIONS[app_name])
                
                agent = Agent(
                    name=f"{agent_name.title()} Agent",
                    role=f"Handle {agent_name} tasks",
                    model=model,
                    instructions=[
                        f"Handle {agent_name} tasks efficiently.",
                        "Use timezone Asia/Kolkata and local currency/units.",
                    ],
                    tools=tools,
                    add_datetime_to_instructions=True,
                    timezone_identifier="Asia/Kolkata",
                    add_location_to_instructions=True
                )
                agents.append(agent)
                
            except Exception as e:
                print(f"⚠️  Failed to create {agent_name} agent: {e}")
    
    # Add filesystem agent if needed
    if needs_filesystem:
        try:
            async with MCPTools("npx -y @wonderwhy-er/desktop-commander@latest") as desktop_commander:
                filesystem_agent = Agent(
                    name="File System Agent",
                    role="Handle file operations",
                    model=model,
                    tools=[desktop_commander],
                    instructions=[
                        "Handle file system operations efficiently.",
                        "Use timezone Asia/Kolkata.",
                    ],
                    add_datetime_to_instructions=True,
                    timezone_identifier="Asia/Kolkata",
                    add_location_to_instructions=True,
                )
                
                # Create team with filesystem
                team = Team(
                    name="Ubik AI Team",
                    mode="coordinate",
                    model=model,
                    members=agents + [filesystem_agent],
                    instructions=[
                        "Collaborate to provide comprehensive assistance",
                        "Use tools effectively to fetch and create information",
                        "Provide clear and actionable responses",
                        "Use markdown formatting for better readability",
                        "Use timezone Asia/Kolkata and local currency/units",
                    ],
                    markdown=True,
                    add_datetime_to_instructions=True,
                    add_location_to_instructions=True,
                )
                
                print(f"👥 Team created with {len(agents)+1} agents")
                
                # Stream response
                response_stream = await team.arun(user_request, stream=True)
                
                print("\n💬 RESPONSE:")
                async for event in response_stream:
                    if event.event == "TeamRunResponseContent":
                        print(event.content, end="", flush=True)
                    elif event.event == "TeamToolCallStarted":
                        print(f"\n🔧 Tool call started: {event.tool}")
        
        except Exception as e:
            print(f"❌ Error with filesystem agent: {e}")
            needs_filesystem = False
    
    if not needs_filesystem:
        # Create team without filesystem
        team = Team(
            name="Ubik AI Team", 
            mode="coordinate",
            model=model,
            members=agents,
            instructions=[
                "Collaborate to provide comprehensive assistance",
                "Use tools effectively to fetch and create information",
                "Provide clear and actionable responses", 
                "Use markdown formatting for better readability",
                "Use timezone Asia/Kolkata and local currency/units",
            ],
            markdown=True,
            add_datetime_to_instructions=True,
            add_location_to_instructions=True,
        )
        
        print(f"👥 Team created with {len(agents)} agents")
        
        # Stream response
        response_stream = await team.arun(user_request, stream=True)
        
        print("\n💬 RESPONSE:")
        async for event in response_stream:
            if event.event == "TeamRunResponseContent":
                print(event.content, end="", flush=True)
            elif event.event == "TeamToolCallStarted":
                print(f"\n🔧 Tool call started: {event.tool}")


async def process_query(user_request: str, entity_id: str, openai_key: str, composio_api_key: str):
    """Process a user query"""
    try:
        model = OpenAIChat("gpt-4o-mini", api_key=openai_key)
        toolset = ComposioToolSet(api_key=composio_api_key, entity_id=entity_id)
        
        print("🤖 Processing your request...")
        print("=" * 50)
        
        await create_dynamic_team(user_request, model, toolset)
        
        print("\n" + "=" * 50)
        print("✅ Completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Ubik AI - Your Personal Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ubik --query="what's the weather?" --entity_id=john@doe.com --openai_key=sk-xxx --composio_api_key=xxx
  ubik --list_apps --composio_api_key=xxx
  ubik --connect_app=gmail --entity_id=john@doe.com --composio_api_key=xxx
  ubik --list_connected_apps --entity_id=john@doe.com --composio_api_key=xxx
        """
    )
    
    # Main actions (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--query", help="Ask AI a question")
    action_group.add_argument("--list_apps", action="store_true", help="List all available apps")
    action_group.add_argument("--connect_app", help="Connect to an OAuth app")
    action_group.add_argument("--list_connected_apps", action="store_true", help="List connected apps")
    
    # Required parameters
    parser.add_argument("--entity_id", help="Your unique entity ID (like email)")
    parser.add_argument("--composio_api_key", help="Your Composio API key")
    parser.add_argument("--openai_key", help="Your OpenAI API key (required for queries)")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Validate required parameters based on action
    if args.query:
        if not all([args.entity_id, args.composio_api_key, args.openai_key]):
            print("❌ For queries, you need: --entity_id, --composio_api_key, and --openai_key")
            sys.exit(1)
        
        asyncio.run(process_query(args.query, args.entity_id, args.openai_key, args.composio_api_key))
    
    elif args.list_apps:
        if not args.composio_api_key:
            print("❌ --composio_api_key is required")
            sys.exit(1)
        
        list_all_apps(args.composio_api_key)
    
    elif args.connect_app:
        if not all([args.entity_id, args.composio_api_key]):
            print("❌ For app connection, you need: --entity_id and --composio_api_key")
            sys.exit(1)
        
        connect_app(args.connect_app, args.entity_id, args.composio_api_key)
    
    elif args.list_connected_apps:
        if not all([args.entity_id, args.composio_api_key]):
            print("❌ For listing connections, you need: --entity_id and --composio_api_key")
            sys.exit(1)
        
        list_connected_apps(args.entity_id, args.composio_api_key)


if __name__ == "__main__":
    main()
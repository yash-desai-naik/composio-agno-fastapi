#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys
import os
import traceback
import logging
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Starting script...")

# Add error handling for imports
try:
    logger.debug("Importing required modules...")
    from agno.models.openai import OpenAIChat
    from agno.agent import Agent
    from composio_agno import ComposioToolSet
    from agno.team.team import Team
    from agno.tools.mcp import MCPTools
    logger.debug("Importing tool actions from ubik_tools...")
    from ubik_tools import (
        gmail_tools_actions, 
        calendar_tools_actions, 
        weather_tools_actions, 
        websearch_tools_actions, 
        googledrive_tools_actions
    )
except ImportError as e:
    print(f"Error loading required packages: {e}")
    print("Please make sure all dependencies are installed: pip install -r requirements.txt")
    logger.error(f"Import error: {e}")
    logger.debug("Stack trace:", exc_info=True)
    sys.exit(1)

logger.debug("All imports successful")

def check_dependencies():
    """Check if all required external dependencies are available."""
    logger.debug("Checking external dependencies...")
    required_packages = [
        'openai',
        'requests',
        'mcp'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            logger.debug(f"✓ Found {package}")
        except ImportError as e:
            logger.error(f"Missing dependency {package}: {e}")
            print(f"Missing dependency: {package}")
            return False
            
    logger.debug("All external dependencies checked")
    return True

def get_available_apps() -> Dict[str, List[str]]:
    """Get lists of available apps."""
    oauth_apps = [
        "gmail",
        "googlecalendar",
        "googledrive",
        "github"
    ]
    
    no_auth_apps = [
        "weathermap",
        "composio_search",
        "desktop_commander"
    ]
    
    return {
        "oauth_apps": oauth_apps,
        "no_auth_apps": no_auth_apps
    }

async def check_connection_status(toolset: ComposioToolSet, app_name: str, entity_id: str) -> Dict[str, Any]:
    """Check if an app is connected."""
    try:
        entity = toolset.get_entity(entity_id)
        connections = entity.get_connections()
        
        for conn in connections:
            conn_app = getattr(conn, 'appName', None) or \
                      getattr(conn, 'name', None) or \
                      getattr(conn, 'app', None)
                      
            if conn_app and conn_app.lower() == app_name.lower():
                conn_status = getattr(conn, 'status', None) or \
                            getattr(conn, 'connectionStatus', None)
                            
                if conn_status in ["active", "ACTIVE", "connected", "CONNECTED"]:
                    return {
                        "connected": True,
                        "status": conn_status,
                        "connection_id": getattr(conn, 'id', None) or getattr(conn, 'connectedAccountId', None),
                        "app_name": app_name
                    }
        
        return {
            "connected": False,
            "status": "not_connected",
            "app_name": app_name
        }
        
    except Exception as e:
        return {
            "connected": False,
            "status": "error",
            "error": str(e),
            "app_name": app_name
        }

async def connect_app(toolset: ComposioToolSet, app_name: str, entity_id: str) -> Dict[str, Any]:
    """Connect to a Composio app."""
    try:
        # Check if already connected
        status = await check_connection_status(toolset, app_name, entity_id)
        if status["connected"]:
            return {
                "success": True,
                "already_connected": True,
                "message": f"Already connected to {app_name}",
                "connection_id": status["connection_id"]
            }
            
        entity = toolset.get_entity(entity_id)
        
        # Try initiating connection
        try:
            connection_request = entity.initiate_connection(app_name=app_name)
        except:
            try:
                connection_request = entity.initiate_connection(appName=app_name)
            except:
                return {
                    "success": False,
                    "error": "Failed to initiate connection",
                    "message": f"Could not connect to {app_name}"
                }
                
        # Get connection URL
        auth_url = getattr(connection_request, 'redirectUrl', None)
        connection_id = getattr(connection_request, 'connectedAccountId', None)
        
        if not auth_url:
            return {
                "success": False,
                "error": "No auth URL provided",
                "message": f"Failed to get authentication URL for {app_name}"
            }
            
        return {
            "success": True,
            "already_connected": False,
            "message": f"Connection initiated for {app_name}",
            "connection_id": connection_id,
            "auth_url": auth_url
        }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to connect to {app_name}"
        }

async def list_connected_apps(composio_api_key: str, entity_id: str) -> None:
    """List all connected apps."""
    toolset = ComposioToolSet(api_key=composio_api_key, entity_id=entity_id)
    apps = get_available_apps()
    
    print("\nChecking app connections...")
    
    # Check OAuth apps
    index = 1
    for app_name in apps["oauth_apps"] + apps["no_auth_apps"]:
        status = await check_connection_status(toolset, app_name, entity_id)
        status_text = "connected" if status["connected"] else "not connected"
        print(f"{index}. {app_name} ({status_text})")
        index += 1

async def list_apps() -> None:
    """List all available apps."""
    apps = get_available_apps()
    
    print("\nAvailable apps:")
    index = 1
    
    # List OAuth apps
    for app in apps["oauth_apps"]:
        print(f"{index}. {app} (needs oauth)")
        index += 1
    
    # List no-auth apps    
    for app in apps["no_auth_apps"]:
        print(f"{index}. {app} (no oauth) (no need to connect)")
        index += 1

async def process_query(query: str, composio_api_key: str, openai_key: str, entity_id: str) -> None:
    """Process a natural language query using the dynamic team."""
    # Initialize models
    model = OpenAIChat(id="gpt-4o-mini", api_key=openai_key)
    toolset = ComposioToolSet(api_key=composio_api_key, entity_id=entity_id)
    
    # Get needed agents
    selection = await smart_agent_selector(query, model)
    needed_agents = selection.get("agents", [])
    needs_filesystem = selection.get("needs_filesystem", False)
    
    print(f"\n🎯 Selected agents: {', '.join(needed_agents)}" + 
          (f" + filesystem" if needs_filesystem else ""))
    
    # Create dynamic team
    await create_dynamic_team(query, model, toolset)

async def smart_agent_selector(user_request: str, model) -> Dict[str, Any]:
    """LLM decides which agents are needed."""    
    selector = Agent(
        name="Agent Selector",
        model=model,
        instructions=[
            "You decide which agents are needed for a user request. Respond ONLY with a JSON object.",
            "Available agents: gmail, calendar, weather, search, drive, filesystem",
            "Format: {\"agents\": [\"agent1\", \"agent2\"], \"needs_filesystem\": false}",
            "Examples:",
            "\"check my emails\" -> {\"agents\": [\"gmail\"], \"needs_filesystem\": false}",
            "\"what's on my plate today?\" -> {\"agents\": [\"calendar\"], \"needs_filesystem\": false}",
            "\"weather and my schedule\" -> {\"agents\": [\"weather\", \"calendar\"], \"needs_filesystem\": false}",
            "\"find laptops and save to file\" -> {\"agents\": [\"search\"], \"needs_filesystem\": true}",
            "\"email summary and weather\" -> {\"agents\": [\"gmail\", \"weather\"], \"needs_filesystem\": false}",
        ],
    )
    
    response = await selector.arun(f"Which agents needed for: '{user_request}'")
    
    try:
        return json.loads(response.content.strip())
    except:
        # Simple fallback
        return {"agents": ["search"], "needs_filesystem": False}

async def create_dynamic_team(user_request: str, model, toolset: ComposioToolSet):
    """Create and run a dynamic team based on the request."""    
    # Get smart selection
    selection = await smart_agent_selector(user_request, model)
    needed_agents = selection.get("agents", [])
    needs_filesystem = selection.get("needs_filesystem", False)
    
    # Tool mappings
    tool_configs = {
        "gmail": {"tools": toolset.get_tools(actions=gmail_tools_actions, check_connected_accounts=True), 
                 "name": "Gmail Agent", "role": "Manage email communications"},
        "calendar": {"tools": toolset.get_tools(actions=calendar_tools_actions, check_connected_accounts=True),
                    "name": "Google Calendar Agent", "role": "Manage calendar events and schedules"},
        "weather": {"tools": toolset.get_tools(actions=weather_tools_actions),
                   "name": "Weather Agent", "role": "Provide weather information"},
        "search": {"tools": toolset.get_tools(actions=websearch_tools_actions),
                  "name": "Web Search Agent", "role": "Handle web search requests"},
        "drive": {"tools": toolset.get_tools(actions=googledrive_tools_actions, check_connected_accounts=True),
                 "name": "Google Drive Agent", "role": "Manage files in Google Drive"},
    }
    
    # Create needed agents
    agents = []
    for agent_type in needed_agents:
        if agent_type in tool_configs:
            config = tool_configs[agent_type]
            agent = Agent(
                name=config["name"],
                role=config["role"],
                model=model,
                instructions=[
                    f"Handle {agent_type} tasks efficiently.",
                    "Use timezone Asia/Kolkata and appropriate local units/currency.",
                ],
                add_datetime_to_instructions=True,
                timezone_identifier="Asia/Kolkata",
                tools=config["tools"],
                add_location_to_instructions=True
            )
            agents.append(agent)
    
    # Add filesystem agent if needed
    if needs_filesystem:
        async with MCPTools("npx -y @wonderwhy-er/desktop-commander@latest") as desktop_commander:
            filesystem_agent = Agent(
                name="File System Agent",
                role="Handle file operations and local system tasks",
                model=model,
                tools=[desktop_commander],
                instructions=[
                    "Handle file system operations efficiently.",
                    "Use timezone Asia/Kolkata and appropriate local units/currency.",
                ],
                add_datetime_to_instructions=True,
                timezone_identifier="Asia/Kolkata",
                add_location_to_instructions=True,
            )
            
            # Create team with filesystem
            team = Team(
                name="Dynamic AI Team",
                mode="coordinate",
                model=model,
                members=agents + [filesystem_agent],
                instructions=[
                    "Collaborate to provide comprehensive assistance",
                    "Use tools effectively to fetch and create information",
                    "Ensure all responses are clear and actionable",
                    "Only output the final consolidated response, not individual agent responses",
                    "Use markdown formatting for better readability",
                    "Use timezone Asia/Kolkata and appropriate local units/currency",
                ],
                markdown=True,
                add_datetime_to_instructions=True,
                add_location_to_instructions=True,
                enable_agentic_context=True,
                enable_agentic_memory=True,
                share_member_interactions=True
            )
            
            print(f"👥 Team created with {len(agents)+1} agents\n")
            
            # Stream response
            response_stream = await team.arun(user_request, stream=True, stream_intermediate_steps=True)
            
            print("\n💬 STREAMING RESPONSE:")
            async for event in response_stream:
                if event.event == "TeamRunResponseContent":
                    print(event.content)
                elif event.event == "TeamReasoningStep":
                    continue
                elif event.event == "TeamToolCallStarted":
                    print(f"\nTool call started: {event.tool_name}")
                elif event.event == "ToolCallStarted":
                    print(f"  - Started: {event.tool_name}")
                elif event.event == "ToolCallCompleted":
                    if event.error:
                        print(f"  - Error: {event.error}")
    else:
        # Create team without filesystem
        team = Team(
            name="Dynamic AI Team",
            mode="coordinate",
            model=model,
            members=agents,
            instructions=[
                "Collaborate to provide comprehensive assistance",
                "Use tools effectively to fetch and create information", 
                "Ensure all responses are clear and actionable",
                "Only output the final consolidated response, not individual agent responses",
                "Use markdown formatting for better readability",
                "Use timezone Asia/Kolkata and appropriate local units/currency",
            ],
            markdown=True,
            add_datetime_to_instructions=True,
            add_location_to_instructions=True,
            enable_agentic_context=True,
            enable_agentic_memory=True,
            share_member_interactions=True
        )
        
        print(f"👥 Team created with {len(agents)} agents\n")
        
        # Stream response
        response_stream = await team.arun(user_request, stream=True, stream_intermediate_steps=True)
        
        print("\n💬 STREAMING RESPONSE:")
        async for event in response_stream:
            if event.event == "TeamRunResponseContent":
                print(event.content)
            elif event.event == "TeamReasoningStep":
                continue
            elif event.event == "TeamToolCallStarted":
                print(f"\nTool call started: {event.tool_name}")
            elif event.event == "ToolCallStarted":
                print(f"  - Started: {event.tool_name}")
            elif event.event == "ToolCallCompleted":
                if event.error:
                    print(f"  - Error: {event.error}")

async def main():
    """Main entry point."""
    # Check dependencies first
    if not check_dependencies():
        print("Error: Missing required dependencies. Please install them first:")
        print("pip install -r requirements.txt")
        sys.exit(1)
        
    parser = argparse.ArgumentParser(description="Ubik CLI - AI Assistant")
    
    # Add arguments
    parser.add_argument("--list_apps", action="store_true", help="List all available apps")
    parser.add_argument("--list_connected_apps", action="store_true", help="List connected apps")
    parser.add_argument("--connect_app", help="Connect to a specific app")
    parser.add_argument("--query", help="Natural language query to process")
    parser.add_argument("--composio_api_key", help="Composio API key")
    parser.add_argument("--openai_key", help="OpenAI API key")
    parser.add_argument("--entity_id", help="User entity ID")
    
    try:
        logger.debug("Parsing command line arguments...")
        args = parser.parse_args()
        logger.debug(f"Parsed arguments: {args}")
        
        # Handle list_apps command
        if args.list_apps:
            if not args.composio_api_key:
                print("Error: --composio_api_key is required")
                sys.exit(1)
            await list_apps()
            
        # Handle list_connected_apps command    
        elif args.list_connected_apps:
            if not args.composio_api_key or not args.entity_id:
                print("Error: --composio_api_key and --entity_id are required")
                sys.exit(1)
            await list_connected_apps(args.composio_api_key, args.entity_id)
            
        # Handle connect_app command    
        elif args.connect_app:
            if not args.composio_api_key or not args.entity_id:
                print("Error: --composio_api_key and --entity_id are required")
                sys.exit(1)
                
            toolset = ComposioToolSet(api_key=args.composio_api_key, entity_id=args.entity_id)
            result = await connect_app(toolset, args.connect_app, args.entity_id)
            
            if result["success"]:
                if result["already_connected"]:
                    print(f"\n✓ Already connected to {args.connect_app}")
                else:
                    print(f"\nPlease authenticate {args.connect_app}: {result['auth_url']}")
            else:
                print(f"\nError connecting to {args.connect_app}: {result.get('error', 'Unknown error')}")
                
        # Handle query command
        elif args.query:
            if not all([args.composio_api_key, args.openai_key, args.entity_id]):
                print("Error: --composio_api_key, --openai_key, and --entity_id are required for queries")
                sys.exit(1)
            await process_query(args.query, args.composio_api_key, args.openai_key, args.entity_id)
            
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nTraceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        logger.debug("Starting main entrypoint")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"Failed to import required module: {e}")
        print("\nPlease ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"Fatal error: {e}")
        print("\nFor more details, check the debug log")
        sys.exit(1)

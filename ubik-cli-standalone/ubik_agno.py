import asyncio
from typing import Dict, Any, List
from agno.models.openai import OpenAIChat
from agno.agent import Agent
from composio_agno import ComposioToolSet
from agno.team.team import Team
from agno.tools.mcp import MCPTools
from ubik_tools import (
    gmail_tools_actions, 
    calendar_tools_actions, 
    weather_tools_actions, 
    websearch_tools_actions, 
    googledrive_tools_actions
)


async def smart_agent_selector(user_request: str, model) -> Dict[str, Any]:
    """LLM decides which agents are needed for the request."""
    
    selector = Agent(
        name="Agent Selector",
        model=model,
        instructions=[
            "You decide which agents are needed for a user request. Respond ONLY with a JSON object.",
            "Available agents: gmail, calendar, weather, search, drive, filesystem",
            "Format: {\"agents\": [\"agent1\", \"agent2\"], \"needs_filesystem\": false}",
            "",
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
        import json
        return json.loads(response.content.strip())
    except:
        # Simple fallback
        return {"agents": ["search"], "needs_filesystem": False}


async def check_connections(toolset: ComposioToolSet, entity_id: str, needed_agents: List[str]) -> Dict[str, bool]:
    """Check which agents have valid connections."""
    connection_status = {}
    
    auth_required_agents = ["gmail", "calendar", "drive"]
    
    for agent_type in needed_agents:
        if agent_type in auth_required_agents:
            try:
                entity = toolset.get_entity(entity_id)
                connections = entity.get_connections()
                
                app_mapping = {
                    "gmail": "gmail",
                    "calendar": "googlecalendar", 
                    "drive": "googledrive"
                }
                
                app_name = app_mapping.get(agent_type, agent_type)
                
                is_connected = any(
                    getattr(conn, 'appName', '').lower() == app_name.lower() and
                    getattr(conn, 'status', '').lower() in ['active', 'connected']
                    for conn in connections
                )
                
                connection_status[agent_type] = is_connected
                
            except Exception as e:
                print(f"⚠️  Error checking {agent_type} connection: {e}")
                connection_status[agent_type] = False
        else:
            # No auth needed for weather, search
            connection_status[agent_type] = True
    
    return connection_status


async def create_dynamic_team(user_request: str, model, toolset: ComposioToolSet):
    """Create team dynamically based on LLM selection."""
    
    # Get smart selection
    selection = await smart_agent_selector(user_request, model)
    needed_agents = selection.get("agents", [])
    needs_filesystem = selection.get("needs_filesystem", False)
    
    print(f"🎯 LLM selected agents: {', '.join(needed_agents)}" + 
          (f" + filesystem" if needs_filesystem else ""))
    
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
    
    # Create only needed agents
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
            
            print(f"👥 Team created with {len(agents)+1} agents")
            
            # Stream response exactly like your original
            response_stream = await team.arun(user_request, stream=True, stream_intermediate_steps=True)
            
            print("\n💬 STREAMING RESPONSE:")
            async for event in response_stream:
                if event.event == "TeamRunResponseContent":
                    print(event.content, end="", flush=True)
                elif event.event == "TeamToolCallStarted":
                    print(f"\n🔧 Tool call started: {event.tool}")
                elif event.event == "ToolCallStarted":
                    pass  # Keep it clean
                elif event.event == "ToolCallCompleted":
                    pass
                elif event.event == "TeamReasoningStep":
                    pass
    
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
        
        print(f"👥 Team created with {len(agents)} agents")
        
        # Stream response exactly like your original
        response_stream = await team.arun(user_request, stream=True, stream_intermediate_steps=True)
        
        print("\n💬 STREAMING RESPONSE:")
        async for event in response_stream:
            if event.event == "TeamRunResponseContent":
                print(event.content, end="", flush=True)
            elif event.event == "TeamToolCallStarted":
                print(f"\n🔧 Tool call started: {event.tool}")
            elif event.event == "ToolCallStarted":
                pass
            elif event.event == "ToolCallCompleted":
                pass
            elif event.event == "TeamReasoningStep":
                pass


async def setup_connections(toolset: ComposioToolSet, entity_id: str):
    """Quick connection setup - same as your original."""
    oauth_apps = ["googlecalendar", "gmail", "googledrive"]
    
    for app_name in oauth_apps:
        try:
            entity = toolset.get_entity(entity_id)
            connections = entity.get_connections()
            
            is_connected = any(
                getattr(conn, 'appName', '').lower() == app_name.lower() and
                getattr(conn, 'status', '').lower() in ['active', 'connected']
                for conn in connections
            )
            
            if not is_connected:
                connection_request = entity.initiate_connection(app_name=app_name)
                auth_url = getattr(connection_request, 'redirectUrl', None)
                if auth_url:
                    print(f"🔗 Please authenticate {app_name}: {auth_url}")
                    
        except Exception as e:
            print(f"⚠️  {app_name} connection: {e}")


async def main():
    """Main function - simplified version of your original with smart selection."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv(override=True)
    
    # Same validation as your original
    if not os.getenv("COMPOSIO_API_KEY"):
        print("Please set COMPOSIO_API_KEY in .env file")
        return
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY in .env file")
        return

    # Same setup as your original
    model = OpenAIChat("gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
    entity_id = "kkk12"  # Replace with your actual entity ID
    toolset = ComposioToolSet(api_key=os.getenv("COMPOSIO_API_KEY"), entity_id=entity_id)
    
    # Setup connections
    await setup_connections(toolset, entity_id)
    
    # Your test request
    user_request = "what's on my plate today? And also check my emails from kevin"
    
    print("🤖 Processing with dynamic agent selection...")
    print("="*60)
    
    try:
        await create_dynamic_team(user_request, model, toolset)
        print("\n" + "="*60)
        print("✅ Completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
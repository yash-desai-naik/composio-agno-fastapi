import asyncio
from typing import Dict, Any

from agno.models.openai import OpenAIChat
# from agno.models.groq import Groq


from agno.agent import Agent
from composio_agno import Action, ComposioToolSet, App

from agno.team.team import Team

from ubik_tools import gmail_tools_actions, calendar_tools_actions, weather_tools_actions, websearch_tools_actions, googledrive_tools_actions




from agno.tools.mcp import MCPTools



def connect_composio_app(
    toolset: ComposioToolSet,
    app_name: str,
    entity_id: str = "default"
) -> Dict[str, Any]:
    """
    Initiate connection to a Composio app.
    
    Args:
        toolset: ComposioToolSet instance
        app_name: Name of the app to connect (e.g., 'gmail', 'notion')
        entity_id: User entity ID for the connection
        
    Returns:
        Dict with connection status and details
    """
    try:
        # Get entity
        entity = toolset.get_entity(entity_id)
        
        # Check existing connections
        try:
            connections = entity.get_connections()
            for conn in connections:
                # Check app name in different possible attributes
                conn_app = getattr(conn, 'appName', None) or \
                          getattr(conn, 'app_name', None) or \
                          getattr(conn, 'app', None)
                
                if conn_app and str(conn_app).lower() == app_name.lower():
                    conn_status = getattr(conn, 'status', '')
                    if conn_status in ["active", "ACTIVE", "connected", "CONNECTED"]:
                        return {
                            "success": True,
                            "already_connected": True,
                            "message": f"Already connected to {app_name}",
                            "connection_id": getattr(conn, 'id', None) or getattr(conn, 'connectedAccountId', None)
                        }
        except Exception as e:
            print(f"Error checking connections: {e}")
        
        # Initiate new connection
        try:
            # Try with app_name parameter
            connection_request = entity.initiate_connection(app_name=app_name)
        except:
            # Try with different parameter name
            try:
                connection_request = entity.initiate_connection(appName=app_name)
            except:
                return {
                    "success": False,
                    "error": "Failed to initiate connection",
                    "message": f"Could not connect to {app_name}"
                }
        
        # Get connection details
        auth_url = getattr(connection_request, 'redirectUrl', None)
        connection_id = getattr(connection_request, 'connectedAccountId', None)
        
        return {
            "success": True,
            "already_connected": False,
            "message": f"Connection initiated for {app_name}",
            "connection_id": connection_id,
            "auth_url": auth_url,
            "entity_id": entity_id
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to connect to {app_name}"
        }


def check_connection_status(
    toolset: ComposioToolSet,
    app_name: str,
    entity_id: str = "default"
) -> Dict[str, Any]:
    """
    Check if an app is connected.
    
    Args:
        toolset: ComposioToolSet instance
        app_name: Name of the app to check
        entity_id: User entity ID
        
    Returns:
        Dict with connection status
    """
    try:
        entity = toolset.get_entity(entity_id)
        connections = entity.get_connections()
        
        for conn in connections:
            # Check app name in different possible attributes
            conn_app = getattr(conn, 'appName', None) or \
                      getattr(conn, 'app_name', None) or \
                      getattr(conn, 'app', None)
            
            if conn_app and str(conn_app).lower() == app_name.lower():
                conn_status = getattr(conn, 'status', '')
                return {
                    "connected": conn_status in ["active", "ACTIVE", "connected", "CONNECTED"],
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


# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv(override=True)
    
    # Initialize toolset
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        print("Please set COMPOSIO_API_KEY in .env file")
        exit(1)
    
    
    # Use a specific entity_id for the user
    entity_id = "kkk12"  # Change this to your user's ID
    toolset = ComposioToolSet(api_key=api_key, entity_id=entity_id)
    
    # List of apps to connect
    oauth_apps = [
        "googlecalendar",
        "gmail",
        "googledrive",
            # "notion", "slack"
             ]

    no_auth_apps = [
        'weathermap',
        'composio_search',
    ]
    # Check and connect each app
    for app_name in oauth_apps:
        # Check if already connected
        connection_status = check_connection_status(toolset, app_name, entity_id)
        print(f"{app_name.title()} status: {connection_status}")

        # Connect to app if not already connected
        if not connection_status["connected"]:
            result = connect_composio_app(toolset, app_name, entity_id)
            print(f"Connection result for {app_name}: {result}")
            
            if result["success"] and result.get("auth_url"):
                print(f"\nPlease visit this URL to authenticate with {app_name.title()}:")
                print(result["auth_url"])
        else:
            print(f"Already connected to {app_name} with ID: {connection_status['connection_id']}")
    
    for app_name in no_auth_apps:
        print(f"Already connected to {app_name}")

    
    composio_google_calendar_tools = toolset.get_tools(
        actions=calendar_tools_actions,
        check_connected_accounts=True,
        # entity_id=entity_id
    )
    composio_gmail_email_tools = toolset.get_tools(
        actions=gmail_tools_actions,
        check_connected_accounts=True,
    )

    compsio_weather_tools = toolset.get_tools(
        actions=weather_tools_actions,
    )

    composio_search_tools = toolset.get_tools(
       actions=websearch_tools_actions,
    )

    googledrive_tools = toolset.get_tools(
        actions=googledrive_tools_actions,
        check_connected_accounts=True,
    )

    gmail_agent = Agent(
        name="Gmail Agent",
        role="Manage email communications",
        model=OpenAIChat("gpt-4o-mini"),
        instructions=["Use tools to fetch and create email drafts",
                       "use currency and other metrics/units as per the location of the user",
        ],
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        tools=composio_gmail_email_tools,
        # show_tool_calls=True,
        add_location_to_instructions=True
    )



    googlecalendar_agent = Agent(
        name="Google Calendar Agent",
        role="Manage calendar events and schedules",
        model=OpenAIChat("gpt-4o-mini"),
        instructions=["Use tools to create and find calendar events",
                       "use currency and other metrics/units as per the location of the user",
        ],
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        tools=composio_google_calendar_tools,
        # show_tool_calls=True,
        add_location_to_instructions=True
    )

    weather_agent = Agent(
        name="Weather Agent",
        role="Provide weather information",
        model=OpenAIChat("gpt-4o-mini"),
        instructions=["Use tools to fetch current weather data",
                       "use currency and other metrics/units as per the location of the user",
        ],
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        tools=compsio_weather_tools,
        # show_tool_calls=True,
        add_location_to_instructions=True
    )

    web_search_agent = Agent(
        name="Web Search Agent",
        role="Handle web search requests and general research",
        model=OpenAIChat("gpt-4o-mini"),
        instructions=["Use tools to perform web searches and gather information",
                       "use currency and other metrics/units as per the location of the user",
        ],
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        tools=composio_search_tools,
        # show_tool_calls=True,
        add_location_to_instructions=True,
        
        
    )

    googledrive_agent = Agent(
        name="Google Drive Agent",
        role="Manage files and documents in Google Drive",
        model=OpenAIChat("gpt-4o-mini"),
        instructions=["Use tools to manage files in Google Drive",         
                       "use currency and other metrics/units as per the location of the user",
        ],
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        tools=googledrive_tools,
        
        # show_tool_calls=True,
        add_location_to_instructions=True
    )

    team = Team(
        name="Composio Team",
        mode="coordinate",
        model=OpenAIChat("gpt-4o-mini"),
        # model = selected_model("groq"),
        members=[
            gmail_agent,
            googlecalendar_agent,
            weather_agent,
            web_search_agent,
            googledrive_agent
        ],
        instructions=[
            "Collaborate to provide comprehensive assistance",
            "Use tools effectively to fetch and create information",
            "Ensure all responses are clear and actionable",
            "Only output the final consolidated response, not individual agent responses",
            "Use markdown formatting for better readability",
            "Include relevant details such as dates, times, and locations",
            "If an agent cannot complete a task, escalate to the team for further assistance",
            "while responding the final response, be respectful and polite but bit creative and engaging",
            "use curreny and other metrics/utints as per the location of the user",
        ],
        markdown=True,
        # show_members_responses=True,
        # enable_agentic_context=True,
        add_datetime_to_instructions=True,
        add_location_to_instructions=True,
        # show_tool_calls=True,
        enable_agentic_context=True,
        enable_agentic_memory=True,
        share_member_interactions=True
    )
    
    # team.print_response(
    #     """save current weather details in google drive as weather_details_[context].txt""",
    #     stream=True,
    #     show_full_reasoning=True,
    #     stream_intermediate_steps=True,
    # )


async def create_specialized_team():
   
    
    # GitHub MCP agent
    async with MCPTools("npx -y @modelcontextprotocol/server-github") as github_mcp:
        github_agent = Agent(
            name="GitHub Analyst",
            role="Analyze GitHub repositories and development activity",
            model=OpenAIChat(id="gpt-4o"),
            tools=[github_mcp],
            instructions=["Focus on code quality, activity, and project health"],
        )
        
        # Filesystem MCP agent
        async with MCPTools("npx -y @wonderwhy-er/desktop-commander@latest") as desktop_commander:
            desktop_commander_agent = Agent(
                name="File System Analyst",
                role="Analyze local files and directories",
                model=OpenAIChat(id="gpt-4o"),
                tools=[desktop_commander],
                instructions=["Analyze file structure and content"],
            )
            
            # Create specialized team
            dev_team = Team(
                name="Development Analysis Team",
                mode="coordinate",
                model=OpenAIChat(id="gpt-4o"),
                members=[
                    weather_agent, 
                      desktop_commander_agent,
                    # github_agent,
                      ],
                instructions=[
                    "Coordinate comprehensive development analysis",
                    "Combine web research, GitHub analysis, and local file inspection",
                    "Provide actionable insights for development projects"
                ],
                show_tool_calls=True,
                markdown=True,
            )
            
            # await dev_team.aprint_response(
            #     "Analyze the current state of Python web frameworks",
            #     stream=True
            # )
            
            response_stream = await dev_team.arun("explain the current weather of bhruch as poet. also mention the numericals and location save it as '/Users/yashdesai/Desktop/Ubik AI/weather_details_[context].txt'", stream=True, stream_intermediate_steps=True)

            print("\n\nWAIT FOR THE FINAL STREAMING RESPONSE...")
            async for event in  response_stream:
                if event.event == "TeamRunResponseContent":

                    print(event.content, end="", flush=True)
                elif event.event == "TeamToolCallStarted":
                    # print(f"\nTool call started: {event.tool}")
                    ...
                elif event.event == "ToolCallStarted":
                    # print(f"\nMember tool call started: {event.tool}")
                    ...
                elif event.event == "ToolCallCompleted":
                    # print(f"\nMember tool call completed: {event.tool}")
                    ...
                elif event.event == "TeamReasoningStep":
                    # print(f"Reasoning step: {event.content}")
                    ...


import json
async def main():
    # response_stream = await team.arun("explain the current weather of missisippi as poet. also mention the numericals and location save it as weather_details_[context].txt", stream=True, stream_intermediate_steps=True)

    # async for event in  response_stream:
    #     if event.event == "TeamRunResponseContent":

    #         print(event.content, end="", flush=True)
    #     elif event.event == "TeamToolCallStarted":
    #         print(f"\nTool call started: {event.tool}")
    #     elif event.event == "ToolCallStarted":
    #         # print(f"\nMember tool call started: {event.tool}")
    #         ...
    #     elif event.event == "ToolCallCompleted":
    #         # print(f"\nMember tool call completed: {event.tool}")
    #         ...
    #     elif event.event == "TeamReasoningStep":
    #         # print(f"Reasoning step: {event.content}")
    #         ...

   await create_specialized_team()    
    
    # Asynchronous execution
    # result = await team.arun("explain the current weather as poet. also mention the numericals and location",)
    # # print(result, end='', flush=True)
    # print(json.dumps(result.__dict__, indent=2, default=str))

    # Asynchronous streaming
    # async for chunk in await team.arun("explain the current weather as poet. also mention the numericals and location save it as weather_details_[context].txt", stream=True,  stream_intermediate_steps=True):

    #     print(chunk.content, end="", flush=True)


    # team.print_response(
    #     "appl stock price?",
    #     stream=True,
    #     # stream_intermediate_steps=True
    # )


if __name__ == "__main__":
    asyncio.run(main())

   # Streaming responses
# for chunk in team.run("Fetch the 3 latest emails and create a calendar event based on the summary of the emails.", stream=True):
#     print(chunk.content, end="", flush=True)

    # for chunk in team.run(
    #     # "get cheapest flight from Delhi to Mumbai on 15th October 2024 and hotel in Mumbai for 2 days and save it in google drive as flight_hotel_details_[context].txt",
    #     "get detailed comparisions  of best 10 airfryers in india under budget of 10k inr. mention the users' top positive and negative reviews(detailed), and save it in google drive as airfryer_comparision_[context].txt.",
    #     stream=True,
    #     show_full_reasoning=True,
    #     stream_intermediate_steps=True
    # ):
    #     print(chunk.content, end="", flush=True)
from typing import Dict, Any
# from composio import  App
# from composio_openai import ComposioToolSet,  Action, App
# from openai import OpenAI
from agno.models.openai import OpenAIChat


from agno.agent import Agent
from composio_agno import Action, ComposioToolSet, App

from agno.team.team import Team


# openai_client = OpenAI()


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
        actions=[Action.GOOGLECALENDAR_CREATE_EVENT, Action.GOOGLECALENDAR_FIND_EVENT],
        check_connected_accounts=True,
        # entity_id=entity_id
    )
    composio_gmail_email_tools = toolset.get_tools(
        actions=[Action.GMAIL_FETCH_EMAILS, Action.GMAIL_CREATE_EMAIL_DRAFT],
        check_connected_accounts=True,
    )

    compsio_weather_tools = toolset.get_tools(
        actions=[Action.WEATHERMAP_WEATHER]
    )

    composio_search_tools = toolset.get_tools(
       actions=[
           Action.COMPOSIO_SEARCH_DUCK_DUCK_GO_SEARCH,
           Action.COMPOSIO_SEARCH_EVENT_SEARCH,
           Action.COMPOSIO_SEARCH_EXA_SIMILARLINK,
           Action.COMPOSIO_SEARCH_FINANCE_SEARCH,
           Action.COMPOSIO_SEARCH_GOOGLE_MAPS_SEARCH,
           Action.COMPOSIO_SEARCH_IMAGE_SEARCH,
           Action.COMPOSIO_SEARCH_NEWS_SEARCH,
           Action.COMPOSIO_SEARCH_SCHOLAR_SEARCH,
           Action.COMPOSIO_SEARCH_SEARCH,
           Action.COMPOSIO_SEARCH_SHOPPING_SEARCH,
           Action.COMPOSIO_SEARCH_TAVILY_SEARCH,
           Action.COMPOSIO_SEARCH_TRENDS_SEARCH
       ]
    )

    gmail_agent = Agent(
        name="Gmail Agent",
        role="Manage email communications",
        model=OpenAIChat("gpt-4o"),
        instructions="Use tools to fetch and create email drafts",
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        tools=composio_gmail_email_tools,
        show_tool_calls=True
    )



    googlecalendar_agent = Agent(
        name="Google Calendar Agent",
        role="Manage calendar events and schedules",
        model=OpenAIChat("gpt-4o"),
        instructions="Use tools to create and find calendar events",
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        tools=composio_google_calendar_tools,
        show_tool_calls=True
    )

    weather_agent = Agent(
        name="Weather Agent",
        role="Provide weather information",
        model=OpenAIChat("gpt-4o"),
        instructions="Use tools to fetch current weather data",
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        tools=compsio_weather_tools,
        show_tool_calls=True
    )

    web_search_agent = Agent(
        name="Web Search Agent",
        role="Handle web search requests and general research",
        model=OpenAIChat("gpt-4o"),
        instructions="Use tools to perform web searches and gather information",
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        tools=composio_search_tools,
        show_tool_calls=True
    )

    team = Team(
        name="Composio Team",
        mode="coordinate",
        model=OpenAIChat("gpt-4o"),
        members=[
            gmail_agent,
            googlecalendar_agent,
            weather_agent,
            web_search_agent
        ],
        instructions=[
            "Collaborate to provide comprehensive assistance",
            "Use tools effectively to fetch and create information",
            "Ensure all responses are clear and actionable",
            "Only output the final consolidated response, not individual agent responses",
            "Use markdown formatting for better readability",
            "Include relevant details such as dates, times, and locations",
            "If an agent cannot complete a task, escalate to the team for further assistance",
        ],
        markdown=True,
        show_members_responses=True,
        # enable_agentic_context=True,
        add_datetime_to_instructions=True,
    )
    
    # team.print_response(
    #     """Fetch the latest emails and create a calendar event based on the summary of the emails.""",
    #     stream=True,
    #     show_full_reasoning=True,
    #     stream_intermediate_steps=True,
    # )

   # Streaming responses
# for chunk in team.run("Fetch the 3 latest emails and create a calendar event based on the summary of the emails.", stream=True):
#     print(chunk.content, end="", flush=True)

    for chunk in team.run(
        "search for the latest news on AI and summarize the key points. set goole meet with nddesai97@gmail.com for tomorrow at 10am to discuss the findings. also share the summary via email with her.",
        stream=True,
        show_full_reasoning=True,
        stream_intermediate_steps=True
    ):
        print(chunk.content, end="", flush=True)
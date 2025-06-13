from typing import Dict, Any
# from composio import  App
from composio_openai import ComposioToolSet,  Action, App
from openai import OpenAI


openai_client = OpenAI()


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
    
    toolset = ComposioToolSet(api_key=api_key)
    
    # Use a specific entity_id for the user
    entity_id = "kkk12"  # Change this to your user's ID
    
    # List of apps to connect
    apps = ["gmail",
            #  "googlecalendar", "notion", "slack"
             ]

    # Check and connect each app
    for app_name in apps:
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
   
   
    tools = toolset.get_tools(actions=[Action.GMAIL_FETCH_EMAILS])
    if not tools:
        print("No tools available for the user. Please ensure the user has connected apps.")
        exit(1)

    assistant_instruction = "You are a super intelligent personal assistant"

    assistant = openai_client.beta.assistants.create(
    name="Personal Assistant",
    instructions=assistant_instruction,
    model="gpt-4-turbo-preview",
    tools=tools,
    )

    thread = openai_client.beta.threads.create()
    my_task = "Fetch the latest 3 emails from my Gmail account and summarize them for me."
    message = openai_client.beta.threads.messages.create(thread_id=thread.id,role="user",content=my_task)

    run = openai_client.beta.threads.runs.create(thread_id=thread.id,assistant_id=assistant.id)

    response_after_tool_calls = toolset.wait_and_handle_assistant_tool_calls(
        client=openai_client,
        run=run,
        thread=thread,
    )
    print(f"Response after tool calls: {response_after_tool_calls}")
    print(f"Tools available: {tools}")

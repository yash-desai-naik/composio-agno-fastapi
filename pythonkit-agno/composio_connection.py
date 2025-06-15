"""Connection management module for Composio apps"""
from typing import Dict, Any
from composio_agno import ComposioToolSet


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


def setup_connections(api_key: str, entity_id: str) -> ComposioToolSet:
    """
    Setup all connections and return configured toolset.
    
    Args:
        api_key: Composio API key
        entity_id: User entity ID
        
    Returns:
        Configured ComposioToolSet instance
    """
    from composio_config import OAUTH_APPS, NO_AUTH_APPS
    
    toolset = ComposioToolSet(api_key=api_key, entity_id=entity_id)
    
    # Check and connect OAuth apps
    for app_name in OAUTH_APPS:
        connection_status = check_connection_status(toolset, app_name, entity_id)
        print(f"{app_name.title()} status: {connection_status}")

        if not connection_status["connected"]:
            result = connect_composio_app(toolset, app_name, entity_id)
            print(f"Connection result for {app_name}: {result}")
            
            if result["success"] and result.get("auth_url"):
                print(f"\nPlease visit this URL to authenticate with {app_name.title()}:")
                print(result["auth_url"])
        else:
            print(f"Already connected to {app_name} with ID: {connection_status['connection_id']}")
    
    # No-auth apps are already connected
    for app_name in NO_AUTH_APPS:
        print(f"Already connected to {app_name}")
    
    return toolset
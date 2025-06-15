"""
Swift interface module for Composio integration.
This module provides the main interface functions that can be called from Swift using PythonKit.
"""
import asyncio
from typing import Dict, Any, List, Optional
from composio_config import COMPOSIO_API_KEY, DEFAULT_ENTITY_ID
from composio_connection import setup_connections
from composio_agents import AgentFactory
from composio_team import create_team


class ComposioInterface:
    """Main interface class for Swift integration"""
    
    def __init__(self, api_key: Optional[str] = None, entity_id: Optional[str] = None):
        """
        Initialize Composio interface.
        
        Args:
            api_key: Composio API key (uses env var if not provided)
            entity_id: User entity ID (uses default if not provided)
        """
        self.api_key = api_key or COMPOSIO_API_KEY
        self.entity_id = entity_id or DEFAULT_ENTITY_ID
        
        if not self.api_key:
            raise ValueError("COMPOSIO_API_KEY not found in environment or provided")
        
        # Initialize components
        self.toolset = None
        self.agent_factory = None
        self.team = None
        self._initialized = False
    
    def initialize(self) -> Dict[str, Any]:
        """
        Initialize all components and setup connections.
        
        Returns:
            Dict with initialization status
        """
        try:
            # Setup connections
            self.toolset = setup_connections(self.api_key, self.entity_id)
            
            # Create agent factory
            self.agent_factory = AgentFactory(self.toolset)
            
            # Create team
            self.team = create_team(self.agent_factory)
            
            self._initialized = True
            
            return {
                "success": True,
                "message": "Composio interface initialized successfully",
                "entity_id": self.entity_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to initialize Composio interface"
            }
    
    def process_query(self, query: str, stream: bool = False) -> Dict[str, Any]:
        """
        Process a query synchronously.
        
        Args:
            query: User query to process
            stream: Whether to stream the response
            
        Returns:
            Dict with response or error
        """
        if not self._initialized:
            return {
                "success": False,
                "error": "Interface not initialized",
                "message": "Call initialize() first"
            }
        
        try:
            if stream:
                # For streaming, collect all chunks
                response_chunks = []
                for chunk in self.team.run(query, stream=True):
                    response_chunks.append(chunk.content)
                
                return {
                    "success": True,
                    "response": "".join(response_chunks),
                    "streamed": True
                }
            else:
                # Non-streaming response
                response = self.team.run(query)
                return {
                    "success": True,
                    "response": response.content
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process query"
            }
    
    def process_query_async(self, query: str) -> Dict[str, Any]:
        """
        Process a query asynchronously (wrapper for Swift).
        
        Args:
            query: User query to process
            
        Returns:
            Dict with response or error
        """
        return asyncio.run(self._process_query_async(query))
    
    async def _process_query_async(self, query: str) -> Dict[str, Any]:
        """
        Internal async method to process query.
        
        Args:
            query: User query to process
            
        Returns:
            Dict with response or error
        """
        if not self._initialized:
            return {
                "success": False,
                "error": "Interface not initialized",
                "message": "Call initialize() first"
            }
        
        try:
            result = await self.team.arun(query)
            return {
                "success": True,
                "response": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process query"
            }
    
    def get_agent_list(self) -> List[str]:
        """
        Get list of available agents.
        
        Returns:
            List of agent names
        """
        if not self._initialized or not self.team:
            return []
        
        return [member.name for member in self.team.members]
    
    def get_connection_status(self, app_name: str) -> Dict[str, Any]:
        """
        Get connection status for a specific app.
        
        Args:
            app_name: Name of the app to check
            
        Returns:
            Dict with connection status
        """
        if not self.toolset:
            return {
                "connected": False,
                "status": "toolset_not_initialized"
            }
        
        from composio_connection import check_connection_status
        return check_connection_status(self.toolset, app_name, self.entity_id)


# Convenience functions for Swift
def create_interface(api_key: Optional[str] = None, entity_id: Optional[str] = None) -> ComposioInterface:
    """
    Create and return a new Composio interface instance.
    
    Args:
        api_key: Composio API key (optional)
        entity_id: User entity ID (optional)
        
    Returns:
        ComposioInterface instance
    """
    return ComposioInterface(api_key, entity_id)


def quick_query(query: str, api_key: Optional[str] = None, entity_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick one-shot query without persistent interface.
    
    Args:
        query: User query to process
        api_key: Composio API key (optional)
        entity_id: User entity ID (optional)
        
    Returns:
        Dict with response or error
    """
    interface = create_interface(api_key, entity_id)
    init_result = interface.initialize()
    
    if not init_result["success"]:
        return init_result
    
    return interface.process_query(query)
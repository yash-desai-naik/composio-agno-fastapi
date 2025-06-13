from typing import Dict, List, Optional
from datetime import datetime

from src.app.core.config import settings
from src.app.models.composio import User
from composio_agno import Action, ComposioToolSet
from agno.models.openai import OpenAIChat
from agno.agent import Agent
from agno.team.team import Team

class ComposioService:
    def __init__(self):
        self.users: Dict[str, User] = {}  # In-memory storage
        self.toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)
        self.model = OpenAIChat("gpt-4o")

    async def create_user(self, email: str, name: str) -> User:
        user = User(
            email=email,
            name=name,
            entity_id=email,
            connected_apps=[],
            chat_history=[],
            created_at=datetime.now()
        )
        self.users[email] = user
        return user

    async def get_user(self, email: str) -> Optional[User]:
        return self.users.get(email)

    async def connect_app(self, email: str, app_name: str) -> Dict:
        user = await self.get_user(email)
        if not user:
            raise ValueError("User not found")
            
        self.toolset.entity_id = user.entity_id
        
        try:
            # Check existing connections
            try:
                entity = self.toolset.get_entity(user.entity_id)
                connections = entity.get_connections()
                
                for conn in connections:
                    # Check app name in different possible attributes
                    conn_app = getattr(conn, 'appName', None) or \
                              getattr(conn, 'app_name', None) or \
                              getattr(conn, 'app', None)
                    
                    if conn_app and str(conn_app).lower() == app_name.lower():
                        conn_status = getattr(conn, 'status', '')
                        if conn_status in ["active", "ACTIVE", "connected", "CONNECTED"]:
                            # Update user's connected apps if not already in the list
                            if app_name.lower() not in [x.lower() for x in user.connected_apps]:
                                user.connected_apps.append(app_name.lower())
                                self.users[email] = user
                            
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
            
            # Update user's connected apps for new connection
            if auth_url and connection_id:
                if app_name.lower() not in [x.lower() for x in user.connected_apps]:
                    user.connected_apps.append(app_name.lower())
                    self.users[email] = user
                
            return {
                "success": True,
                "already_connected": False,
                "message": f"Connection initiated for {app_name}",
                "connection_id": connection_id,
                "auth_url": auth_url,
                "entity_id": user.entity_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to connect to {app_name}"
            }

    async def get_connected_apps(self, email: str) -> List[str]:
        user = await self.get_user(email)
        if not user:
            raise ValueError("User not found")
        return user.connected_apps

    async def create_team(self, email: str, timezone: str = "Asia/Kolkata") -> Team:
        user = await self.get_user(email)
        if not user:
            raise ValueError("User not found")
            
        self.toolset.entity_id = user.entity_id
        
        # Initialize tools for each service
        gmail_tools = self.toolset.get_tools(
            actions=[Action.GMAIL_FETCH_EMAILS, Action.GMAIL_CREATE_EMAIL_DRAFT],
            check_connected_accounts=True
        )
        calendar_tools = self.toolset.get_tools(
            actions=[Action.GOOGLECALENDAR_CREATE_EVENT, Action.GOOGLECALENDAR_FIND_EVENT],
            check_connected_accounts=True
        )
        weather_tools = self.toolset.get_tools(
            actions=[Action.WEATHERMAP_WEATHER]
        )
        search_tools = self.toolset.get_tools(
            actions=[
                Action.COMPOSIO_SEARCH_NEWS_SEARCH,
                Action.COMPOSIO_SEARCH_SEARCH
            ]
        )
        
        # Create agents
        agents = [
            Agent(
                name="Gmail Agent",
                role="Manage email communications",
                model=self.model,
                instructions="Use tools to fetch and create email drafts",
                add_datetime_to_instructions=True,
                timezone_identifier=timezone,
                tools=gmail_tools,
                show_tool_calls=True
            ),
            Agent(
                name="Calendar Agent",
                role="Manage calendar events",
                model=self.model,
                instructions="Use tools to create and find calendar events",
                add_datetime_to_instructions=True,
                timezone_identifier=timezone,
                tools=calendar_tools,
                show_tool_calls=True
            ),
            Agent(
                name="Weather Agent",
                role="Provide weather information",
                model=self.model,
                instructions="Use tools to fetch weather data",
                add_datetime_to_instructions=True,
                timezone_identifier=timezone,
                tools=weather_tools,
                show_tool_calls=True
            ),
            Agent(
                name="Search Agent",
                role="Handle web searches",
                model=self.model,
                instructions="Use tools to search and gather information",
                add_datetime_to_instructions=True,
                timezone_identifier=timezone,
                tools=search_tools,
                show_tool_calls=True
            )
        ]
        
        # Create and return team
        return Team(
            name="Composio Team",
            mode="coordinate",
            model=self.model,
            members=agents,
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
            add_datetime_to_instructions=True,
        )

    async def check_required_apps(self, query: str, user: User) -> bool:
        """Check if user has required apps connected based on query"""
        query_lower = query.lower()
        required_apps = []

        # Check for email operations (sending, drafting)
        if any(word in query_lower for word in ['email', 'mail', 'gmail']) or \
           any(word in query_lower for word in ['send', 'draft']):
            required_apps.append('gmail')

        # Check for calendar operations
        if any(word in query_lower for word in ['calendar', 'schedule', 'event']):
            required_apps.append('googlecalendar')
            
        # Check for weather operations
        if any(word in query_lower for word in ['weather', 'temperature', 'forecast']):
            required_apps.append('weathermap')
            
        if not required_apps:  # If no specific apps required
            return True
            
        connected_apps = user.connected_apps
        missing_apps = [app for app in required_apps if app not in connected_apps]
        
        if missing_apps:
            raise ValueError(f"Please connect the following apps first: {', '.join(missing_apps)}")
        
        return True

    def clean_response(self, text: str) -> str:
        """Clean up the response text by removing debug information and formatting nicely."""
        # Remove debug lines (like function completion info)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if not any(skip in line for skip in ['completed in', 'transfer_task_to_member', '_fetch_']):
                cleaned_lines.append(line)
        
        # Join lines and remove multiple newlines
        text = '\n'.join(cleaned_lines)
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
        
        return text.strip()

    async def process_query(self, email: str, query: str, timezone: str) -> dict:
        user = await self.get_user(email)
        if not user:
            raise ValueError("User not found")
            
        # Check required app connections
        await self.check_required_apps(query, user)
            
        team = await self.create_team(email, timezone)
        response = ""
        tool_calls = []
        current_agent = None
        
        try:
            for chunk in team.run(query, stream=True, show_full_reasoning=True, show_tool_calls=True):
                if chunk and hasattr(chunk, 'content') and chunk.content:
                    response += chunk.content
                
                # Track tool calls and agent responses
                if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                    for tool_call in chunk.tool_calls:
                        tool_calls.append({
                            "agent": current_agent,
                            "tool": tool_call.get('name'),
                            "input": tool_call.get('input'),
                            "output": tool_call.get('output')
                        })
                
                if hasattr(chunk, 'agent') and chunk.agent:
                    current_agent = chunk.agent.name
            
            if not response:
                response = "No response generated. Please make sure you're connected to the required apps."
            else:
                response = self.clean_response(response)
                
        except Exception as e:
            response = f"Error processing query: {str(e)}"
        
        # Update chat history with tool calls
        chat_entry = {
            "query": query,
            "response": response,
            "tool_calls": tool_calls,
            "timestamp": datetime.now().isoformat()
        }
        
        user.chat_history.append(chat_entry)
        if len(user.chat_history) > 5:  # Keep only last 5 entries
            user.chat_history = user.chat_history[-5:]
            
        self.users[email] = user
        
        return {
            "query": query,
            "response": response,
            "tool_calls": tool_calls
        }
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

from src.app.core.config import settings
from src.app.models.composio import User
from src.app.services.composio_tools import gmail_tools_actions, calendar_tools_actions, weather_tools_actions, search_tools_actions, googledrive_tools_actions
from composio_agno import Action, ComposioToolSet
from agno.models.openai import OpenAIChat
from agno.agent import Agent
from agno.team.team import Team
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.storage.sqlite import SqliteStorage
from pydantic import BaseModel, Field
from typing import Optional

UBIK_AI_NAME = "Ubik AI"
UBIK_AI_DESCRIPTION = """
Ubik AI is your personal AI assistant dedicated to managing and streamlining your daily digital workflows.
It seamlessly coordinates between various services while maintaining strict privacy standards.
Key principles:
- Efficient multi-service workflow management
- Secure handling of personal data
- No training on user data
- Privacy-first approach
- Contextual awareness across services
"""

UBIK_AI_PRINCIPLES = [
    "Protect user privacy and data confidentiality at all times",
    "Never share user data between different users or external services",
    "Use data only for completing the user's specific workflow",
    "Maintain context across services while preserving data isolation",
    "Clear all sensitive data after task completion",
    "No training or learning from user's personal information"
]

class WorkflowState(str, Enum):
    INITIAL = "initial"
    PROCESSING = "processing"
    FETCHING_DATA = "fetching_data"
    DATA_FETCHED = "data_fetched"
    TASK_FORWARDING = "task_forwarding"
    TASK_PROCESSING = "task_processing"
    TASK_COMPLETED = "task_completed"
    COMPLETED = "completed"
    ERROR = "error"

class TaskContext(BaseModel):
    current_task: str = Field(default="")
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_service: Optional[str] = Field(default=None)
    target_service: Optional[str] = Field(default=None)
    source_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # Track task transitions
    transitions: List[Dict[str, Any]] = Field(default_factory=list)
    # Track dependencies between tasks
    depends_on: Optional[str] = Field(default=None)  # task_id of dependent task

class SharedContext(BaseModel):
    state: WorkflowState = Field(default=WorkflowState.INITIAL)
    task: Optional[TaskContext] = Field(default_factory=TaskContext)
    # Track current active agent and last action
    current_agent: Optional[str] = Field(default=None)
    last_action: Optional[str] = Field(default=None)
    # Store workflow-specific data
    weather_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    calendar_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    email_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    drive_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # Memory references
    memory_keys: List[str] = Field(default_factory=list)
    # Track task chain for complex workflows
    task_chain: List[Dict[str, Any]] = Field(default_factory=list)
    
    def update_state(self, new_state: WorkflowState, agent: str, action: str):
        """Update workflow state with tracking"""
        self.state = new_state
        self.current_agent = agent
        self.last_action = action
        # Track task transition
        if self.task:
            self.task.transitions.append({
                "timestamp": datetime.now().isoformat(),
                "from_state": self.state,
                "to_state": new_state,
                "agent": agent,
                "action": action
            })
            
    def add_to_task_chain(self, agent: str, action: str, data: Optional[Dict] = None):
        """Add a step to the task execution chain"""
        self.task_chain.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "state": self.state,
            "data": data or {}
        })

class ComposioService:
    def __init__(self):
        self.toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)
        self.model = OpenAIChat("gpt-4o")
        
        # Initialize memory storage
        memory_db = SqliteMemoryDb(
            table_name="user_memories",
            db_file="agno_memory.db"
        )
        
        # Initialize agent storage
        agent_storage = SqliteStorage(
            table_name="agent_sessions",
            db_file="agno_storage.db"
        )
        
        # Initialize memory with the storage backend
        self.memory = Memory(
            model=self.model,  # Use the same model for memory operations
            db=memory_db,  # Use SQLite for persistent storage
        )

    async def create_user(self, email: str, name: str) -> User:
        user = User(
            email=email,
            name=name,
            entity_id=email,
            connected_apps=[],
            chat_history=[],
            created_at=datetime.now()
        )
        return user.save()

    async def get_user(self, email: str) -> Optional[User]:
        return User.get(email)

    def is_oauth_app(self, app_name: str) -> bool:
        """Check if the app requires OAuth authentication"""
        oauth_apps = ['gmail', 'googlecalendar', 'googledrive', 'notion', 'slack']
        return app_name.lower() in [x.lower() for x in oauth_apps]

    async def connect_app(self, email: str, app_name: str) -> Dict:
        user = await self.get_user(email)
        if not user:
            raise ValueError("User not found")
            
        # For non-OAuth apps like weathermap and composio_search, auto-connect
        if not self.is_oauth_app(app_name):
            if app_name.lower() not in [x.lower() for x in user.connected_apps]:
                user.connected_apps.append(app_name.lower())
                user.update_apps()
            return {
                "success": True,
                "already_connected": True,
                "message": f"Auto-connected to {app_name} (no auth required)",
                "connection_id": None
            }
            
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
                                user.update_apps()
                            
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
                    user.update_apps()  # Use the new SQLite update method
                
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
            actions=gmail_tools_actions,
            check_connected_accounts=True
        )
        calendar_tools = self.toolset.get_tools(
            actions=calendar_tools_actions,
            check_connected_accounts=True
        )
        weather_tools = self.toolset.get_tools(
            actions=weather_tools_actions
        )
        search_tools = self.toolset.get_tools(
            actions=search_tools_actions
        )
        
        # Create specialized Ubik AI agents
        agents = [
            Agent(
                name="Gmail Agent",
                role="Personal Gmail manager",
                model=self.model,
                instructions=[
                    "Manage Gmail operations with efficiency and proper context",
                    "When receiving a task from another agent:",
                    "  1. Check task.source_data for input",
                    "  2. Validate the data matches expected format",
                    "  3. Update shared context state to TASK_PROCESSING",
                    "  4. Execute email operation",
                    "  5. Update task.output_data with results",
                    "  6. Set state to TASK_COMPLETED",
                    "When initiating a task for another agent:",
                    "  1. Set state to TASK_FORWARDING",
                    "  2. Prepare task.source_data with required information",
                    "  3. Set task.target_service to receiving agent",
                    "  4. Set task.depends_on if needed",
                    "Always track transitions in shared context",
                    "Use memory_keys to store/retrieve relevant context"
                ],
                add_datetime_to_instructions=True,
                timezone_identifier=timezone,
                tools=gmail_tools,
                show_tool_calls=True
            ),
            Agent(
                name="Google Calendar",
                role="Personal Google Calendar manager",
                model=self.model,
                instructions=[
                    "Manage calendar operations with proper task handling",
                    "When receiving a task request:",
                    "  1. Update state to PROCESSING",
                    "  2. Check task requirements in context",
                    "  3. Execute calendar operation",
                    "  4. Store results in task.source_data",
                    "  5. If forwarding to another service:",
                    "     - Set state to TASK_FORWARDING",
                    "     - Set task.target_service",
                    "     - Update task_chain",
                    "When operation complete:",
                    "  1. Set state to TASK_COMPLETED",
                    "  2. Update calendar_data in shared context",
                    "  3. Add memory_keys if needed for future reference",
                    "Check task_chain for workflow dependencies",
                    "Maintain consistent state transitions"
                ],
                add_datetime_to_instructions=True,
                timezone_identifier=timezone,
                tools=calendar_tools,
                show_tool_calls=True
            ),
            Agent(
                name="Weather Agent",
                role="Weather intelligence provider",
                model=self.model,
                instructions=[
                    "Provide accurate weather information efficiently",
                    "Format weather data clearly for different use cases",
                    "When data is for other services, provide complete formatted output",
                    "Store weather data in shared context",
                    "Update context state appropriately during workflow",
                ],
                add_datetime_to_instructions=True,
                timezone_identifier=timezone,
                tools=weather_tools,
                show_tool_calls=True
            ),
            Agent(
                name="Web Search Agent",
                role="Web search and information retrieval specialist",
                model=self.model,
                instructions=[
                    "Gather information from the web efficiently",
                    "Handle search queries with user's preferences in mind",
                    "Provide relevant results with personal queries",
                    "Format information/context appropriately for other services"
                ],
                add_datetime_to_instructions=True,
                timezone_identifier=timezone,
                tools=search_tools,
                show_tool_calls=True
            ),
            Agent(
                name="Google Drive Agent",
                role="Google Drive operations manager",
                model=self.model,
                instructions=[
                    "Manage Drive operations with workflow awareness",
                    "When receiving data from other agents:",
                    "  1. Check task.source_data and validate",
                    "  2. Set state to TASK_PROCESSING",
                    "  3. Check source_service and dependencies",
                    "  4. Execute file operation",
                    "  5. Update drive_data in context",
                    "  6. Set state to TASK_COMPLETED",
                    "When requested in workflow:",
                    "  1. Check task_chain for prerequisites",
                    "  2. Validate all required data is present",
                    "  3. Execute with proper error handling",
                    "Track all operations in task transitions",
                    "Use memory system for file organization"
                ],
                add_datetime_to_instructions=True,
                timezone_identifier=timezone,
                tools=self.toolset.get_tools(
                    actions=googledrive_tools_actions,
                    check_connected_accounts=True
                ),
                show_tool_calls=True
            )
        ]
        
        # Create and return team
        # Initialize shared context with proper task tracking
        shared_context = SharedContext(
            state=WorkflowState.INITIAL,
            task=TaskContext(
                current_task="initialize_team",
                source_service=None,
                target_service=None
            ),
            task_chain=[{
                "timestamp": datetime.now().isoformat(),
                "agent": "system",
                "action": "team_creation",
                "state": WorkflowState.INITIAL,
                "data": {}
            }],
            memory_keys=[]
        ).model_dump()
        
        team = Team(
            name=UBIK_AI_NAME,
            mode="route",  # Use routing mode for managed task forwarding
            model=self.model,
            members=agents,
            instructions=[
                # Core workflow principles
                "Operate as Ubik AI with proper task management",
                
                # Task routing
                "For task forwarding between agents:",
                "1. Source agent prepares task context",
                "2. Updates shared state to TASK_FORWARDING",
                "3. Target agent validates and processes",
                "4. Updates state to TASK_COMPLETED",
                
                # Context management
                "Maintain shared context across operations",
                "Track task chain for multi-step workflows",
                "Use memory_keys for persistent data",
                
                # State transitions
                "Follow workflow state progression",
                "Track all transitions in context",
                "Handle errors with proper state updates",
                
                # Security and privacy
                *UBIK_AI_PRINCIPLES,
            ],
            markdown=True,
            show_members_responses=True,
            add_datetime_to_instructions=True,
            show_tool_calls=True,
            memory=self.memory,
            enable_user_memories=True,
            add_history_to_messages=True,
            num_history_runs=2,
            user_id=email,
            enable_agentic_context=True,
            enable_agentic_memory=True,
            context=shared_context,
            task_router=True,  # Enable managed task routing
            task_validation=True  # Enable task validation
        )
        return team

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
        
        # # Check for weather operations
        # if any(word in query_lower for word in ['search for', 'search on web', 'get from web']):
        #     required_apps.append('composio_search')

        # Check for Google Drive operations
        if any(word in query_lower for word in ['drive', 'googledrive', 'create file', 'save file', 'upload', 'download', 'document', 'folder']) or \
           any(phrase in query_lower for phrase in ['save it in', 'save in', 'create a file']):
            required_apps.append('googledrive')
            
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
        
        # The team will automatically handle memory creation and updates
        # through enable_user_memories=True
        
        # Keep a summary in chat history for UI purposes
        chat_entry = {
            "query": query,
            "response": response,
            "tool_calls": tool_calls,
            "timestamp": datetime.now().isoformat()
        }
        
        user.chat_history.append(chat_entry)
        if len(user.chat_history) > 5:  # Keep only last 5 entries for UI
            user.chat_history = user.chat_history[-5:]
            
        user.update_chat_history()
        
        return {
            "query": query,
            "response": response,
            "tool_calls": tool_calls
        }

    async def get_available_apps(self) -> Dict[str, List[str]]:
        """Get the list of available OAuth and no-auth apps"""
        oauth_apps = ['gmail', 'googlecalendar', 'googledrive', 'notion', 'slack']
        no_auth_apps = ['weathermap', 'composio_search']
        
        return {
            "oauth_apps": oauth_apps,
            "no_auth_apps": no_auth_apps
        }
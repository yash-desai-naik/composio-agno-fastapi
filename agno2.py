import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from agno.models.openai import OpenAIChat
from agno.agent import Agent
from agno.team.team import Team
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.storage.sqlite import SqliteStorage
from agno.tools.user_control_flow import UserControlFlowTools
from agno.exceptions import RetryAgentRun, StopAgentRun
from composio_agno import Action, ComposioToolSet, App

# Enhanced imports for better functionality
from ubik_tools import (
    gmail_tools_actions, 
    calendar_tools_actions, 
    weather_tools_actions, 
    websearch_tools_actions, 
    googledrive_tools_actions
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('composio_team.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"

@dataclass
class ConnectionResult:
    success: bool
    status: ConnectionStatus
    message: str
    connection_id: Optional[str] = None
    auth_url: Optional[str] = None
    error: Optional[str] = None

class EnhancedComposioManager:
    """Enhanced Composio connection and tool management"""
    
    def __init__(self, api_key: str, entity_id: str = "default"):
        self.api_key = api_key
        self.entity_id = entity_id
        self.toolset = ComposioToolSet(api_key=api_key, entity_id=entity_id)
        self.connected_apps = {}
        
    def check_connection_status(self, app_name: str) -> ConnectionResult:
        """Enhanced connection status checking with better error handling"""
        try:
            entity = self.toolset.get_entity(self.entity_id)
            connections = entity.get_connections()
            
            for conn in connections:
                conn_app = (
                    getattr(conn, 'appName', None) or 
                    getattr(conn, 'app_name', None) or 
                    getattr(conn, 'app', None)
                )
                
                if conn_app and str(conn_app).lower() == app_name.lower():
                    conn_status = getattr(conn, 'status', '')
                    is_connected = conn_status.lower() in ["active", "connected"]
                    
                    return ConnectionResult(
                        success=True,
                        status=ConnectionStatus.CONNECTED if is_connected else ConnectionStatus.DISCONNECTED,
                        message=f"Connection status for {app_name}: {conn_status}",
                        connection_id=getattr(conn, 'id', None) or getattr(conn, 'connectedAccountId', None)
                    )
            
            return ConnectionResult(
                success=True,
                status=ConnectionStatus.DISCONNECTED,
                message=f"No connection found for {app_name}"
            )
            
        except Exception as e:
            logger.error(f"Error checking connection status for {app_name}: {e}")
            return ConnectionResult(
                success=False,
                status=ConnectionStatus.ERROR,
                message=f"Failed to check connection status for {app_name}",
                error=str(e)
            )

    def connect_app(self, app_name: str) -> ConnectionResult:
        """Enhanced app connection with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Check if already connected
                status = self.check_connection_status(app_name)
                if status.status == ConnectionStatus.CONNECTED:
                    self.connected_apps[app_name] = status.connection_id
                    return ConnectionResult(
                        success=True,
                        status=ConnectionStatus.CONNECTED,
                        message=f"Already connected to {app_name}",
                        connection_id=status.connection_id
                    )
                
                # Attempt connection
                entity = self.toolset.get_entity(self.entity_id)
                
                try:
                    connection_request = entity.initiate_connection(app_name=app_name)
                except:
                    try:
                        connection_request = entity.initiate_connection(appName=app_name)
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"Connection attempt {attempt + 1} failed for {app_name}, retrying...")
                            time.sleep(retry_delay)
                            continue
                        raise e
                
                auth_url = getattr(connection_request, 'redirectUrl', None)
                connection_id = getattr(connection_request, 'connectedAccountId', None)
                
                if connection_id:
                    self.connected_apps[app_name] = connection_id
                
                return ConnectionResult(
                    success=True,
                    status=ConnectionStatus.PENDING,
                    message=f"Connection initiated for {app_name}",
                    connection_id=connection_id,
                    auth_url=auth_url
                )
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Connection attempt {attempt + 1} failed for {app_name}: {e}")
                    time.sleep(retry_delay)
                    continue
                
                logger.error(f"Failed to connect to {app_name} after {max_retries} attempts: {e}")
                return ConnectionResult(
                    success=False,
                    status=ConnectionStatus.ERROR,
                    message=f"Failed to connect to {app_name}",
                    error=str(e)
                )
        
        return ConnectionResult(
            success=False,
            status=ConnectionStatus.ERROR,
            message=f"Max retries exceeded for {app_name}"
        )

    def get_tools_with_fallback(self, actions: List, app_name: str, check_connected: bool = True):
        """Get tools with fallback and error handling"""
        try:
            tools = self.toolset.get_tools(
                actions=actions,
                check_connected_accounts=check_connected,
            )
            logger.info(f"Successfully loaded {len(tools)} tools for {app_name}")
            return tools
        except Exception as e:
            logger.error(f"Failed to load tools for {app_name}: {e}")
            # Return empty list as fallback
            return []

class EnhancedAgent(Agent):
    """Enhanced Agent with better error handling and retry logic"""
    
    def __init__(self, *args, **kwargs):
        # Add default error handling tools
        if 'tools' in kwargs:
            kwargs['tools'].append(UserControlFlowTools())
        
        # Enhanced instructions
        enhanced_instructions = kwargs.get('instructions', [])
        enhanced_instructions.extend([
            "If a tool fails, try alternative approaches or inform the user about limitations",
            "Always validate inputs before making API calls",
            "Provide clear error messages when operations fail",
            "Use retry logic for transient failures",
            "Maintain context across tool calls for better user experience"
        ])
        kwargs['instructions'] = enhanced_instructions
        
        # Add error handling configuration
        kwargs.setdefault('tool_call_limit', 10)
        kwargs.setdefault('show_tool_calls', True)
        
        super().__init__(*args, **kwargs)

def create_enhanced_team(composio_manager: EnhancedComposioManager) -> Team:
    """Create an enhanced team with better configuration"""
    
    # Setup persistent storage and memory
    storage_dir = Path("tmp/team_storage")
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    memory_db = SqliteMemoryDb(
        table_name="team_memory",
        db_file=str(storage_dir / "memory.db")
    )
    memory = Memory(db=memory_db)
    
    team_storage = SqliteStorage(
        table_name="team_sessions",
        db_file=str(storage_dir / "sessions.db"),
        auto_upgrade_schema=True
    )
    
    # Get tools with error handling
    gmail_tools = composio_manager.get_tools_with_fallback(
        gmail_tools_actions, "Gmail", check_connected=True
    )
    calendar_tools = composio_manager.get_tools_with_fallback(
        calendar_tools_actions, "Google Calendar", check_connected=True
    )
    weather_tools = composio_manager.get_tools_with_fallback(
        weather_tools_actions, "Weather", check_connected=False
    )
    search_tools = composio_manager.get_tools_with_fallback(
        websearch_tools_actions, "Web Search", check_connected=False
    )
    drive_tools = composio_manager.get_tools_with_fallback(
        googledrive_tools_actions, "Google Drive", check_connected=True
    )
    
    # Create specialized agents with enhanced configuration
    gmail_agent = EnhancedAgent(
        name="Gmail Specialist",
        role="Expert email management and communication specialist",
        model=OpenAIChat("gpt-4o"),
        instructions=[
            "Manage email communications with professionalism and efficiency",
            "Always confirm before sending emails or making significant changes",
            "Provide email summaries with key action items highlighted",
            "Handle email threading and context appropriately",
            "Respect privacy and confidentiality in all email operations"
        ],
        tools=gmail_tools + [UserControlFlowTools()],
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        add_location_to_instructions=True,
        markdown=True
    )

    calendar_agent = EnhancedAgent(
        name="Calendar Specialist",
        role="Expert calendar and scheduling management specialist",
        model=OpenAIChat("gpt-4o"),
        instructions=[
            "Manage calendar events with attention to scheduling conflicts",
            "Always check for existing appointments before scheduling",
            "Provide clear meeting summaries and agenda items",
            "Handle timezone conversions accurately",
            "Suggest optimal meeting times based on availability"
        ],
        tools=calendar_tools + [UserControlFlowTools()],
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        add_location_to_instructions=True,
        markdown=True
    )

    weather_agent = EnhancedAgent(
        name="Weather Specialist",
        role="Comprehensive weather information and analysis specialist",
        model=OpenAIChat("gpt-4o"),
        instructions=[
            "Provide detailed weather information with context",
            "Include weather alerts and warnings when relevant",
            "Suggest appropriate activities based on weather conditions",
            "Provide multi-day forecasts when requested",
            "Use local units and terminology"
        ],
        tools=weather_tools,
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        add_location_to_instructions=True,
        markdown=True
    )

    search_agent = EnhancedAgent(
        name="Research Specialist",
        role="Expert web research and information gathering specialist",
        model=OpenAIChat("gpt-4o"),
        instructions=[
            "Conduct thorough research with multiple sources",
            "Verify information accuracy and provide source citations",
            "Summarize complex information clearly and concisely",
            "Identify trends and patterns in research data",
            "Provide actionable insights from research findings"
        ],
        tools=search_tools,
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        add_location_to_instructions=True,
        markdown=True
    )

    drive_agent = EnhancedAgent(
        name="Document Specialist",
        role="Expert file and document management specialist",
        model=OpenAIChat("gpt-4o"),
        instructions=[
            "Organize files and documents systematically",
            "Maintain proper file naming conventions",
            "Ensure document security and access permissions",
            "Provide document summaries and metadata",
            "Handle file versioning and backup considerations"
        ],
        tools=drive_tools + [UserControlFlowTools()],
        add_datetime_to_instructions=True,
        timezone_identifier="Asia/Kolkata",
        markdown=True
    )

    # Create enhanced team
    team = Team(
        name="Enhanced Productivity Team",
        mode="coordinate",
        model=OpenAIChat("gpt-4o"),
        members=[gmail_agent, calendar_agent, weather_agent, search_agent, drive_agent],
        memory=memory,
        storage=team_storage,
        instructions=[
            "Collaborate seamlessly to provide comprehensive assistance",
            "Maintain context and continuity across all interactions",
            "Prioritize user privacy and data security",
            "Provide proactive suggestions and recommendations",
            "Handle errors gracefully and offer alternative solutions",
            "Use clear, professional communication with appropriate formatting",
            "Confirm important actions before execution",
            "Learn from user preferences and adapt accordingly",
            "Provide detailed explanations for complex operations",
            "Ensure all responses are actionable and valuable"
        ],
        markdown=True,
        show_tool_calls=True,
        enable_agentic_context=True,
        enable_agentic_memory=True,
        share_member_interactions=True,
        add_datetime_to_instructions=True,
        add_location_to_instructions=True,
        add_history_to_messages=True,
        num_history_responses=5,
        enable_session_summaries=True,
        success_criteria="The team has successfully completed the user's request with high quality, accuracy, and user satisfaction."
    )
    
    return team

async def setup_connections(composio_manager: EnhancedComposioManager):
    """Setup all required connections with enhanced error handling"""
    
    oauth_apps = [
        "googlecalendar",
        "gmail", 
        "googledrive"
    ]
    
    no_auth_apps = [
        "weathermap",
        "composio_search"
    ]
    
    connection_results = {}
    
    # Handle OAuth apps
    for app_name in oauth_apps:
        logger.info(f"Setting up connection for {app_name}...")
        result = composio_manager.connect_app(app_name)
        connection_results[app_name] = result
        
        if result.success:
            if result.status == ConnectionStatus.CONNECTED:
                logger.info(f"✅ {app_name} is already connected")
            elif result.status == ConnectionStatus.PENDING and result.auth_url:
                logger.warning(f"🔗 {app_name} requires authentication: {result.auth_url}")
                print(f"\n⚠️  Please authenticate {app_name}:")
                print(f"   Visit: {result.auth_url}")
                print(f"   Then press Enter to continue...")
                input()
        else:
            logger.error(f"❌ Failed to connect {app_name}: {result.error}")
    
    # Handle no-auth apps
    for app_name in no_auth_apps:
        logger.info(f"✅ {app_name} is ready (no authentication required)")
        connection_results[app_name] = ConnectionResult(
            success=True,
            status=ConnectionStatus.CONNECTED,
            message=f"{app_name} ready"
        )
    
    return connection_results

@asynccontextmanager
async def enhanced_team_context():
    """Context manager for enhanced team setup and cleanup"""
    load_dotenv(override=True)
    
    # Validate environment variables
    api_key = os.getenv("COMPOSIO_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("COMPOSIO_API_KEY environment variable is required")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Initialize composio manager
    entity_id = os.getenv("COMPOSIO_ENTITY_ID", "enhanced_user_001")
    composio_manager = EnhancedComposioManager(api_key, entity_id)
    
    try:
        logger.info("🚀 Initializing Enhanced Composio Team...")
        
        # Setup connections
        connection_results = await setup_connections(composio_manager)
        
        # Create enhanced team
        team = create_enhanced_team(composio_manager)
        
        logger.info("✅ Enhanced team ready!")
        yield team, composio_manager, connection_results
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize team: {e}")
        raise
    finally:
        logger.info("🧹 Cleaning up resources...")

class EnhancedTeamRunner:
    """Enhanced team runner with advanced features"""
    
    def __init__(self, team: Team, composio_manager: EnhancedComposioManager):
        self.team = team
        self.composio_manager = composio_manager
        self.conversation_history = []
        
    async def run_with_retry(self, message: str, max_retries: int = 3, **kwargs) -> Any:
        """Run team with retry logic and error handling"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🎯 Processing request (attempt {attempt + 1}): {message[:100]}...")
                
                # Add conversation context
                if self.conversation_history:
                    context_message = f"Previous conversation context: {self.conversation_history[-2:]}\n\nCurrent request: {message}"
                else:
                    context_message = message
                
                # Run the team
                if kwargs.get('stream', False):
                    response = self.team.run(context_message, **kwargs)
                    # Store in history for context
                    self.conversation_history.append({
                        'request': message,
                        'timestamp': time.time(),
                        'success': True
                    })
                    return response
                else:
                    response = await self.team.arun(context_message, **kwargs)
                    # Store in history for context
                    self.conversation_history.append({
                        'request': message,
                        'response': response.content if hasattr(response, 'content') else str(response),
                        'timestamp': time.time(),
                        'success': True
                    })
                    return response
                    
            except Exception as e:
                logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f"❌ All attempts failed for: {message}")
                    self.conversation_history.append({
                        'request': message,
                        'error': str(e),
                        'timestamp': time.time(),
                        'success': False
                    })
                    raise
        
    def print_response_enhanced(self, message: str, **kwargs):
        """Enhanced response printing with better formatting"""
        print(f"\n{'='*80}")
        print(f"🤖 ENHANCED TEAM RESPONSE")
        print(f"{'='*80}")
        print(f"📝 Query: {message}")
        print(f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        try:
            self.team.print_response(message, **kwargs)
        except Exception as e:
            logger.error(f"❌ Error in team response: {e}")
            print(f"❌ Error: {e}")
        
        print(f"\n{'='*80}")
        print(f"✅ RESPONSE COMPLETE")
        print(f"{'='*80}\n")

# Enhanced example workflows
class WorkflowExamples:
    """Collection of enhanced workflow examples"""
    
    @staticmethod
    def productivity_workflows():
        return [
            {
                "name": "Daily Briefing",
                "query": "Create my daily briefing: check weather, latest emails (last 5), today's calendar events, and any urgent tasks",
                "description": "Comprehensive daily overview"
            },
            {
                "name": "Meeting Preparation",
                "query": "I have a meeting about 'AI Strategy' at 3 PM today. Help me prepare: find relevant emails, create agenda, check attendee availability, and research latest AI trends",
                "description": "Complete meeting preparation workflow"
            },
            {
                "name": "Travel Planning",
                "query": "Plan my trip to Mumbai next week: check weather forecast, find flights from Delhi, book hotel recommendations, and create calendar events for the trip",
                "description": "Comprehensive travel planning"
            },
            {
                "name": "Research & Documentation",
                "query": "Research the top 10 AI tools for productivity in 2024, create a detailed comparison document, and save it to Google Drive with proper formatting",
                "description": "Research and document creation workflow"
            },
            {
                "name": "Email Management",
                "query": "Organize my inbox: categorize emails by priority, draft responses for urgent ones, schedule follow-ups, and create a summary report",
                "description": "Advanced email management"
            }
        ]
    
    @staticmethod
    def business_workflows():
        return [
            {
                "name": "Market Analysis",
                "query": "Analyze the current stock market trends for tech companies, create a detailed report with charts, and schedule a presentation meeting with the team",
                "description": "Market research and presentation setup"
            },
            {
                "name": "Customer Support",
                "query": "Check customer feedback emails, categorize issues, draft professional responses, and create a summary report for management review",
                "description": "Customer support workflow"
            },
            {
                "name": "Project Management",
                "query": "Review project status emails, update calendar with deadlines, create task summaries, and send progress updates to stakeholders",
                "description": "Project management coordination"
            }
        ]

# Main execution functions
async def run_interactive_mode():
    """Run in interactive mode with user input"""
    async with enhanced_team_context() as (team, composio_manager, connections):
        runner = EnhancedTeamRunner(team, composio_manager)
        
        print("\n🎉 Welcome to Enhanced Composio Team!")
        print("Type 'help' for commands, 'examples' for workflow examples, or 'quit' to exit")
        
        while True:
            try:
                user_input = input("\n💬 Enter your request: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    print_help()
                    continue
                elif user_input.lower() == 'examples':
                    print_examples()
                    continue
                elif user_input.lower() == 'status':
                    print_connection_status(connections)
                    continue
                elif not user_input:
                    continue
                
                # Process the request
                runner.print_response_enhanced(
                    user_input,
                    stream=True,
                    show_full_reasoning=True,
                    stream_intermediate_steps=True
                )
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")
                print(f"❌ Error: {e}")

def print_help():
    """Print help information"""
    print("""
🔧 AVAILABLE COMMANDS:
- help: Show this help message
- examples: Show workflow examples
- status: Show connection status
- quit/exit/q: Exit the application

💡 TIPS:
- Be specific in your requests for better results
- The team can handle complex multi-step workflows
- All actions are logged for your reference
- Use natural language - the team understands context
    """)

def print_examples():
    """Print workflow examples"""
    print("\n🚀 PRODUCTIVITY WORKFLOWS:")
    for workflow in WorkflowExamples.productivity_workflows():
        print(f"  📋 {workflow['name']}: {workflow['description']}")
        print(f"     Example: {workflow['query'][:100]}...")
        print()
    
    print("💼 BUSINESS WORKFLOWS:")
    for workflow in WorkflowExamples.business_workflows():
        print(f"  📊 {workflow['name']}: {workflow['description']}")
        print(f"     Example: {workflow['query'][:100]}...")
        print()

def print_connection_status(connections: Dict[str, ConnectionResult]):
    """Print connection status"""
    print("\n🔗 CONNECTION STATUS:")
    for app_name, result in connections.items():
        status_emoji = "✅" if result.status == ConnectionStatus.CONNECTED else "❌"
        print(f"  {status_emoji} {app_name}: {result.message}")

async def run_demo_workflows():
    """Run demonstration workflows"""
    async with enhanced_team_context() as (team, composio_manager, connections):
        runner = EnhancedTeamRunner(team, composio_manager)
        
        demo_queries = [
            "What's the current weather in Mumbai and should I carry an umbrella today?",
            "Find the latest news about artificial intelligence and summarize the top 3 stories",
            "Check my calendar for today and suggest the best time for a 1-hour meeting",
            "Search for the best restaurants in Delhi and create a list with ratings",
            "Get the current stock price of Apple and provide a brief analysis"
        ]
        
        print("🎬 Running Demo Workflows...")
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n🎯 Demo {i}/{len(demo_queries)}")
            runner.print_response_enhanced(
                query,
                stream=True,
                stream_intermediate_steps=False
            )
            
            # Small delay between demos
            await asyncio.sleep(2)

# Main execution
async def main():
    """Main execution function"""
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == 'demo':
            await run_demo_workflows()
        elif mode == 'interactive':
            await run_interactive_mode()
        else:
            print("Usage: python script.py [demo|interactive]")
    else:
        # Default to interactive mode
        await run_interactive_mode()

if __name__ == "__main__":
    try:
        # Handle different event loop scenarios
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
"""Agent factory module for creating specialized agents"""
from agno.agent import Agent
# from agno.models.openai import OpenAIChat
from agno.models.groq import Groq

from composio_agno import ComposioToolSet
from mcp import StdioServerParameters
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters
from composio_config import AGENT_CONFIG
from ubik_tools import (
    gmail_tools_actions,
    calendar_tools_actions,
    weather_tools_actions,
    websearch_tools_actions,
    googledrive_tools_actions
)
import os

class AgentFactory:
    """Factory class for creating specialized agents"""
    
    def __init__(self, toolset: ComposioToolSet):
        """
        Initialize agent factory with toolset.
        
        Args:
            toolset: Configured ComposioToolSet instance
        """
        self.toolset = toolset
        self._load_tools()
    
    def _load_tools(self):
        """Load all required tools from toolset"""
        self.calendar_tools = self.toolset.get_tools(
            actions=calendar_tools_actions,
            check_connected_accounts=True,
        )
        
        self.gmail_tools = self.toolset.get_tools(
            actions=gmail_tools_actions,
            check_connected_accounts=True,
        )
        
        self.weather_tools = self.toolset.get_tools(
            actions=weather_tools_actions,
        )
        
        self.search_tools = self.toolset.get_tools(
            actions=websearch_tools_actions,
        )
        
        self.googledrive_tools = self.toolset.get_tools(
            actions=googledrive_tools_actions,
            check_connected_accounts=True,
        )
    
    def create_gmail_agent(self) -> Agent:
        """Create Gmail agent"""
        return Agent(
            name="Gmail Agent",
            role="Manage email communications",
            # model=OpenAIChat(AGENT_CONFIG["model"]),
            model=Groq(AGENT_CONFIG["model"]),
            instructions=[
                "Use tools to manage gmail",
                "use currency and other metrics/units as per the location of the user",
                "use HTML instead of markdown formatting for better readability while writing emails or drafts",
            ],
            add_datetime_to_instructions=AGENT_CONFIG["add_datetime"],
            timezone_identifier=AGENT_CONFIG["timezone"],
            tools=self.gmail_tools,
            add_location_to_instructions=AGENT_CONFIG["add_location"]
        )
    
    def create_calendar_agent(self) -> Agent:
        """Create Google Calendar agent"""
        return Agent(
            name="Google Calendar Agent",
            role="Manage calendar events and schedules",
            # model=OpenAIChat(AGENT_CONFIG["model"]),
            model=Groq(AGENT_CONFIG["model"]),
            instructions=[
                "Use tools to create and find calendar events",
                "use currency and other metrics/units as per the location of the user",
            ],
            add_datetime_to_instructions=AGENT_CONFIG["add_datetime"],
            timezone_identifier=AGENT_CONFIG["timezone"],
            tools=self.calendar_tools,
            add_location_to_instructions=AGENT_CONFIG["add_location"]
        )
    
    def create_weather_agent(self) -> Agent:
        """Create Weather agent"""
        return Agent(
            name="Weather Agent",
            role="Provide weather information",
            # model=OpenAIChat(AGENT_CONFIG["model"]),
            model=Groq(AGENT_CONFIG["model"]),
            instructions=[
                "Use tools to fetch current weather data",
                "use currency and other metrics/units as per the location of the user",
            ],
            add_datetime_to_instructions=AGENT_CONFIG["add_datetime"],
            timezone_identifier=AGENT_CONFIG["timezone"],
            tools=self.weather_tools,
            add_location_to_instructions=AGENT_CONFIG["add_location"]
        )
    
    def create_search_agent(self) -> Agent:
        """Create Web Search agent"""
        return Agent(
            name="Web Search Agent",
            role="Handle web search requests and general research",
            # model=OpenAIChat(AGENT_CONFIG["model"]),
            model=Groq(AGENT_CONFIG["model"]),
            instructions=[
                "Use tools to perform web searches and gather information",
                "use currency and other metrics/units as per the location of the user",
            ],
            add_datetime_to_instructions=AGENT_CONFIG["add_datetime"],
            timezone_identifier=AGENT_CONFIG["timezone"],
            tools=self.search_tools,
            add_location_to_instructions=AGENT_CONFIG["add_location"]
        )
    
    def create_googledrive_agent(self) -> Agent:
        """Create Google Drive agent"""
        return Agent(
            name="Google Drive Agent",
            role="Manage files and documents in Google Drive",
            # model=OpenAIChat(AGENT_CONFIG["model"]),
            model=Groq(AGENT_CONFIG["model"]),
            instructions=[
                "Use tools to manage files in Google Drive",
                "use currency and other metrics/units as per the location of the user",
            ],
            add_datetime_to_instructions=AGENT_CONFIG["add_datetime"],
            timezone_identifier=AGENT_CONFIG["timezone"],
            tools=self.googledrive_tools,
        )
    

    async def create_desktop_commander_agent(self) -> Agent:
        """Create Desktop Commander agent"""

         # Initialize the MCP server
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@wonderwhy-er/desktop-commander@latest"],
        )

        async with MCPTools(server_params=server_params) as mcp_tools:
            agent = Agent(
                tools=[mcp_tools],
                instructions=[
                    "You are a Desktop commander agent that can run cli commands directly.",
                "specialized for macos and linux systems.",
                "you're also a proffesional developer and devops engineer.",
                f"- my home directory is: {get_home_directory()}",
                "- before running any command, you should check if the user has mentioned a directory.",
                "- if user mentions a directory, you should run the command in that directory.",
                "- make sure user has the 'Ubik AI' folder on their desktop. if not, create it.",
                "If user don't mention the directory, assume it's the 'Ubik AI' folder on their desktop.",
                "CAUTION: beware the user before running any destructive or dangerous commands.",
            ],
            markdown=True,
            show_tool_calls=True,
            add_datetime_to_instructions=True,
            timezone_identifier= system_timezone(),
        )
        return agent
        



    def create_all_agents(self) -> list:
        """Create and return all agents"""
        return [
            self.create_gmail_agent(),
            self.create_calendar_agent(),
            self.create_weather_agent(),
            self.create_search_agent(),
            self.create_googledrive_agent(),
            # self.create_desktop_commander_agent()  # Uncomment if needed
        ]
    




"""
Utility functions for system information
"""


def system_timezone() -> str:
    """Get the system timezone."""
    
    #determine of os
    if os.name == 'posix':  # Unix-like systems (Linux, macOS)
        # return os.popen('date +%Z').read().strip()
        # use readlink /etc/localtime | sed 's|.*/zoneinfo/||'
        try:
            return os.readlink('/etc/localtime').split('zoneinfo/')[1]
        except Exception as e:
            print(f"Error getting timezone: {e}")
            return "Unknown"
    elif os.name == 'nt':  # Windows
        return os.popen('tzutil /g').read().strip()
    else:
        raise NotImplementedError("Unsupported operating system")
    



def get_home_directory() -> str:
    """Get the home directory of the current user."""
    return os.path.expanduser("~")


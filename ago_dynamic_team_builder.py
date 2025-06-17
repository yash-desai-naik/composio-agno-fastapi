import asyncio
import os
from textwrap import dedent
from typing import List, Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.mcp import MCPTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
# from agno.tools.newspaper4k import Newspaper4kTools

class AgentPool:
    """Pool of available agents that can be dynamically assigned to teams."""
    
    def __init__(self):
        self.normal_agents = {}
        self.mcp_agents = {}
        self.mcp_contexts = {}
    
    async def initialize_agents(self):
        """Initialize all agents and store them in the pool."""
        
        # Normal Agents
        self.normal_agents["web_researcher"] = Agent(
            name="Web Research Specialist",
            role="Conduct web research and news analysis",
            model=OpenAIChat(id="gpt-4o-mini"),  # Use smaller model for efficiency
            tools=[DuckDuckGoTools()],
            instructions="Focus on recent, credible web information and news.",
        )
        
        self.normal_agents["financial_analyst"] = Agent(
            name="Financial Analyst",
            role="Analyze financial markets and stock data",
            model=OpenAIChat(id="gpt-4o-mini"),
            tools=[YFinanceTools(stock_price=True, analyst_recommendations=True)],
            instructions="Provide concise financial analysis and market data.",
        )
        
        # self.normal_agents["content_analyst"] = Agent(
        #     name="Content Analyst",
        #     role="Read and analyze articles and documents",
        #     model=OpenAIChat(id="gpt-4o-mini"),
        #     tools=[Newspaper4kTools()],
        #     instructions="Extract key insights from articles and documents.",
        # )
        
        # MCP Agents (initialize contexts)
        # GitHub Agent
        github_mcp = MCPTools("npx -y @modelcontextprotocol/server-github")
        await github_mcp.__aenter__()
        self.mcp_contexts["github"] = github_mcp
        self.mcp_agents["github_analyst"] = Agent(
            name="GitHub Analyst",
            role="Analyze GitHub repositories and code",
            model=OpenAIChat(id="gpt-4o-mini"),
            tools=[github_mcp],
            instructions="Focus on repository analysis and code insights.",
        )
        
        # Filesystem Agent
        project_root = os.path.dirname(os.path.abspath(__file__))
        fs_mcp = MCPTools(f"npx -y @modelcontextprotocol/server-filesystem {project_root}")
        await fs_mcp.__aenter__()
        self.mcp_contexts["filesystem"] = fs_mcp
        self.mcp_agents["filesystem_specialist"] = Agent(
            name="Filesystem Specialist",
            role="Analyze local files and project structure",
            model=OpenAIChat(id="gpt-4o-mini"),
            tools=[fs_mcp],
            instructions="Focus on file structure and project organization.",
        )
        
        # Airbnb Agent (as example third MCP agent)
        airbnb_mcp = MCPTools("npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt")
        await airbnb_mcp.__aenter__()
        self.mcp_contexts["airbnb"] = airbnb_mcp
        self.mcp_agents["travel_specialist"] = Agent(
            name="Travel Specialist",
            role="Search accommodations and travel planning",
            model=OpenAIChat(id="gpt-4o-mini"),
            tools=[airbnb_mcp],
            instructions="Focus on travel and accommodation analysis.",
        )
    
    async def cleanup(self):
        """Clean up MCP contexts."""
        for context in self.mcp_contexts.values():
            await context.__aexit__(None, None, None)

class DynamicTeamBuilder:
    """Builds teams dynamically based on task requirements."""
    
    def __init__(self, agent_pool: AgentPool):
        self.agent_pool = agent_pool
    
    def analyze_task_requirements(self, task: str) -> dict:
        """Analyze task to determine which agents are needed."""
        task_lower = task.lower()
        
        requirements = {
            "needs_web_search": any(keyword in task_lower for keyword in 
                ["search", "news", "latest", "recent", "web", "online"]),
            "needs_financial": any(keyword in task_lower for keyword in 
                ["stock", "financial", "market", "price", "analyst", "ticker", "$"]),
            "needs_content": any(keyword in task_lower for keyword in 
                ["article", "read", "document", "content", "text", "url"]),
            "needs_github": any(keyword in task_lower for keyword in 
                ["github", "repository", "repo", "code", "git"]),
            "needs_filesystem": any(keyword in task_lower for keyword in 
                ["file", "directory", "local", "project structure", "filesystem"]),
            "needs_travel": any(keyword in task_lower for keyword in 
                ["travel", "hotel", "accommodation", "airbnb", "booking"])
        }
        
        return requirements
    
    def create_team_for_task(self, task: str) -> Team:
        """Create a team with only the agents needed for the specific task."""
        requirements = self.analyze_task_requirements(task)
        
        # Select agents based on requirements
        selected_agents = []
        agent_descriptions = []
        
        # Add normal agents
        if requirements["needs_web_search"]:
            selected_agents.append(self.agent_pool.normal_agents["web_researcher"])
            agent_descriptions.append("- Web Research Specialist: General web search and news")
        
        if requirements["needs_financial"]:
            selected_agents.append(self.agent_pool.normal_agents["financial_analyst"])
            agent_descriptions.append("- Financial Analyst: Stock market and financial data")
        
        if requirements["needs_content"]:
            selected_agents.append(self.agent_pool.normal_agents["content_analyst"])
            agent_descriptions.append("- Content Analyst: Article reading and analysis")
        
        # Add MCP agents
        if requirements["needs_github"]:
            selected_agents.append(self.agent_pool.mcp_agents["github_analyst"])
            agent_descriptions.append("- GitHub Analyst: Repository and code analysis")
        
        if requirements["needs_filesystem"]:
            selected_agents.append(self.agent_pool.mcp_agents["filesystem_specialist"])
            agent_descriptions.append("- Filesystem Specialist: Local file analysis")
        
        if requirements["needs_travel"]:
            selected_agents.append(self.agent_pool.mcp_agents["travel_specialist"])
            agent_descriptions.append("- Travel Specialist: Accommodation search")
        
        # If no specific requirements detected, use a minimal set
        if not selected_agents:
            selected_agents.append(self.agent_pool.normal_agents["web_researcher"])
            agent_descriptions.append("- Web Research Specialist: General web search")
        
        # Create team with only selected agents
        team_instructions = dedent(f"""
            You are coordinating a focused team for this specific task.
            
            Available specialists:
            {chr(10).join(agent_descriptions)}
            
            Delegate tasks efficiently to the most appropriate specialists.
            Only use the agents that are relevant to the current task.
        """)
        
        return Team(
            name=f"Dynamic Team ({len(selected_agents)} agents)",
            mode="coordinate",
            model=OpenAIChat(id="gpt-4o-mini"),  # Use smaller model for team leader
            members=selected_agents,
            instructions=team_instructions,
            show_tool_calls=True,
            markdown=True,
        )

# Usage example
async def main():
    # Initialize agent pool
    agent_pool = AgentPool()
    await agent_pool.initialize_agents()
    
    # Create team builder
    team_builder = DynamicTeamBuilder(agent_pool)
    
    try:
        # # Example 1: Financial task (only needs financial + web agents)
        # print("=" * 60)
        # print("FINANCIAL TASK - Minimal Team")
        # print("=" * 60)
        
        # financial_task = "Get the latest stock price and analyst recommendations for Apple (AAPL)"
        # financial_team = team_builder.create_team_for_task(financial_task)
        # print(f"Team size: {len(financial_team.members)} agents")
        
        # await financial_team.aprint_response(financial_task, stream=True)
        
        # Example 2: Code analysis task (needs github + filesystem agents)
        print("\n" + "=" * 60)
        print("CODE ANALYSIS TASK - Different Team")
        print("=" * 60)
        
        code_task = "Analyze the GitHub repository structure and local project files"
        code_team = team_builder.create_team_for_task(code_task)
        print(f"Team size: {len(code_team.members)} agents")
        
        await code_team.aprint_response(code_task, stream=True)
        
        # Example 3: Travel task (needs only travel agent)
        print("\n" + "=" * 60)
        print("TRAVEL TASK - Minimal Team")
        print("=" * 60)
        
        travel_task = "Find accommodation options in San Francisco for 2 people"
        travel_team = team_builder.create_team_for_task(travel_task)
        print(f"Team size: {len(travel_team.members)} agents")
        
        await travel_team.aprint_response(travel_task, stream=True)
        
    finally:
        # Clean up MCP contexts
        await agent_pool.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
"""Team creation module for Composio integration"""
from agno.team.team import Team
from agno.models.openai import OpenAIChat
from composio_config import TEAM_CONFIG
from composio_agents import AgentFactory


def create_team(agent_factory: AgentFactory) -> Team:
    """
    Create and configure team with all agents.
    
    Args:
        agent_factory: AgentFactory instance with loaded tools
        
    Returns:
        Configured Team instance
    """
    # Create all agents
    agents = agent_factory.create_all_agents()
    
    # Create team
    team = Team(
        name=TEAM_CONFIG["name"],
        mode=TEAM_CONFIG["mode"],
        model=OpenAIChat(TEAM_CONFIG["model"]),
        members=agents,
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
            "use HTML instead of markdown formatting for better readability while writing emails or drafts"
        ],
        markdown=TEAM_CONFIG["markdown"],
        add_datetime_to_instructions=True,
        add_location_to_instructions=True,
        enable_agentic_context=TEAM_CONFIG["enable_agentic_context"],
        enable_agentic_memory=TEAM_CONFIG["enable_agentic_memory"],
        share_member_interactions=TEAM_CONFIG["share_member_interactions"]
    )
    
    return team
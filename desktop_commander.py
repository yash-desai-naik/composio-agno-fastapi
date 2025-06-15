import asyncio
import os
from textwrap import dedent

from agno.agent import Agent
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters


def get_home_directory() -> str:
    """Get the home directory of the current user."""
    return os.path.expanduser("~")


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

async def run_agent(message: str) -> None:
    """Run the GitHub agent with the given message."""

    # Initialize the MCP server
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@wonderwhy-er/desktop-commander@latest"],
    )

    # Create a client session to connect to the MCP server
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

        # Run the agent
        await agent.aprint_response(message, stream=True)


# Example usage
if __name__ == "__main__":
    # Pull request example
    asyncio.run(
        run_agent(
            "list all files and summrize them at once"
        )
    )


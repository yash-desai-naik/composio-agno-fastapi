#!/usr/bin/env python3
"""
Main entry point for running Composio integration directly from terminal.
Usage: python3 composio_main.py [command] [options]
"""
import asyncio
import sys
import argparse
from typing import Optional
from composio_interface import ComposioInterface, create_interface, quick_query
from composio_config import OAUTH_APPS, NO_AUTH_APPS


def print_banner():
    """Print welcome banner"""
    print("=" * 60)
    print("🤖 Composio AI Team Interface")
    print("=" * 60)
    print()


def print_help():
    """Print help information"""
    print("Available commands:")
    print("  init         - Initialize connections and setup")
    print("  query        - Process a query")
    print("  stream       - Process a query with streaming")
    print("  agents       - List available agents")
    print("  status       - Check connection status")
    print("  interactive  - Enter interactive mode")
    print("  quick        - Quick one-shot query")
    print("\nExamples:")
    print("  python3 composio_main.py init")
    print("  python3 composio_main.py query \"What's the weather today?\"")
    print("  python3 composio_main.py status gmail")
    print("  python3 composio_main.py interactive")


def cmd_init(interface: ComposioInterface):
    """Initialize the interface and show connection status"""
    print("Initializing Composio interface...")
    result = interface.initialize()
    
    if result["success"]:
        print("✅ Initialization successful!")
        print(f"Entity ID: {result.get('entity_id', 'default')}")
        
        # Show connection status for all apps
        print("\n📱 App Connection Status:")
        all_apps = OAUTH_APPS + NO_AUTH_APPS
        for app in all_apps:
            status = interface.get_connection_status(app)
            connected = status.get("connected", False)
            status_icon = "✅" if connected else "❌"
            print(f"  {status_icon} {app}: {'Connected' if connected else 'Not connected'}")
    else:
        print("❌ Initialization failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")


def cmd_query(interface: ComposioInterface, query: str, stream: bool = False):
    """Process a single query"""
    if not interface._initialized:
        print("⚠️  Interface not initialized. Initializing now...")
        init_result = interface.initialize()
        if not init_result["success"]:
            print(f"❌ Failed to initialize: {init_result.get('error')}")
            return
    
    print(f"\n💬 Processing query: {query}")
    print("-" * 40)
    
    result = interface.process_query(query, stream=stream)
    
    if result["success"]:
        response = result.get("response", "No response")
        if stream and result.get("streamed"):
            print("📡 Streamed response:")
        print(response)
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


def cmd_agents(interface: ComposioInterface):
    """List available agents"""
    if not interface._initialized:
        interface.initialize()
    
    agents = interface.get_agent_list()
    print("\n🤖 Available Agents:")
    for agent in agents:
        print(f"  • {agent}")


def cmd_status(interface: ComposioInterface, app_name: Optional[str] = None):
    """Check connection status"""
    if app_name:
        status = interface.get_connection_status(app_name)
        connected = status.get("connected", False)
        print(f"\n{app_name}: {'✅ Connected' if connected else '❌ Not connected'}")
        if "error" in status:
            print(f"Error: {status['error']}")
    else:
        # Show all apps
        all_apps = OAUTH_APPS + NO_AUTH_APPS
        print("\n📱 Connection Status for All Apps:")
        for app in all_apps:
            status = interface.get_connection_status(app)
            connected = status.get("connected", False)
            status_icon = "✅" if connected else "❌"
            print(f"  {status_icon} {app}")


def cmd_interactive(interface: ComposioInterface):
    """Enter interactive mode"""
    print("\n🎮 Interactive Mode")
    print("Type 'help' for commands, 'exit' to quit")
    print("-" * 40)
    
    if not interface._initialized:
        print("Initializing...")
        interface.initialize()
    
    while True:
        try:
            query = input("\n🤔 You: ").strip()
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("👋 Goodbye!")
                break
            elif query.lower() == 'help':
                print("\nInteractive commands:")
                print("  help     - Show this help")
                print("  agents   - List available agents")
                print("  status   - Show connection status")
                print("  clear    - Clear screen")
                print("  exit     - Exit interactive mode")
                print("\nOr type any query to process it.")
            elif query.lower() == 'agents':
                cmd_agents(interface)
            elif query.lower() == 'status':
                cmd_status(interface)
            elif query.lower() == 'clear':
                print("\033[H\033[J")  # Clear screen
            elif query:
                print("\n🤖 Assistant: ", end="", flush=True)
                result = interface.process_query(query, stream=True)
                if result["success"]:
                    print(result.get("response", "No response"))
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


def cmd_quick(query: str):
    """Quick one-shot query"""
    print(f"\n🚀 Quick Query: {query}")
    print("-" * 40)
    
    result = quick_query(query)
    
    if result["success"]:
        print(result.get("response", "No response"))
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


async def test_async_query(interface: ComposioInterface, query: str):
    """Test async query processing"""
    print(f"\n⚡ Async Query: {query}")
    print("-" * 40)
    
    result = await interface._process_query_async(query)
    
    if result["success"]:
        print(result.get("response", "No response"))
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Composio AI Team Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        default="interactive",
        choices=["init", "query", "stream", "agents", "status", "interactive", "quick", "help"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "args",
        nargs="*",
        help="Additional arguments for the command"
    )
    
    parser.add_argument(
        "--api-key",
        help="Composio API key (overrides env variable)"
    )
    
    parser.add_argument(
        "--entity-id",
        help="Entity ID (overrides default)"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Handle help command
    if args.command == "help":
        print_help()
        return
    
    # Handle quick command
    if args.command == "quick":
        if args.args:
            query = " ".join(args.args)
            cmd_quick(query)
        else:
            print("❌ Error: Please provide a query for quick command")
            print("Example: python3 composio_main.py quick \"What's the weather?\"")
        return
    
    # Create interface
    try:
        interface = create_interface(
            api_key=args.api_key,
            entity_id=args.entity_id
        )
    except Exception as e:
        print(f"❌ Failed to create interface: {str(e)}")
        return
    
    # Execute commands
    if args.command == "init":
        cmd_init(interface)
    
    elif args.command == "query":
        if args.args:
            query = " ".join(args.args)
            cmd_query(interface, query, stream=False)
        else:
            print("❌ Error: Please provide a query")
            print("Example: python3 composio_main.py query \"What's the weather?\"")
    
    elif args.command == "stream":
        if args.args:
            query = " ".join(args.args)
            cmd_query(interface, query, stream=True)
        else:
            print("❌ Error: Please provide a query")
            print("Example: python3 composio_main.py stream \"Generate a report\"")
    
    elif args.command == "agents":
        cmd_agents(interface)
    
    elif args.command == "status":
        app_name = args.args[0] if args.args else None
        cmd_status(interface, app_name)
    
    elif args.command == "interactive":
        cmd_interactive(interface)
    
    else:
        print(f"❌ Unknown command: {args.command}")
        print_help()


if __name__ == "__main__":
    main()
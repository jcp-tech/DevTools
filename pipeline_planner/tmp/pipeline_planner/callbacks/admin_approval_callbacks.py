
from typing import Any, Dict, Optional
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.agent import Agent

def check_db_write_approval(tool: BaseTool, tool_args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict]:
    """Callback to gate DB write operations with admin approval using get_user_choice.

    This callback is intended to be used as a `before_tool_callback` for the `db_writer` tool.
    It uses the `get_user_choice` tool (which must be available to the agent) to request
    explicit approval from an administrator before allowing the `db_writer` tool to execute.
    """
    _ = tool_context # Context might be useful for logging or additional checks
    print(f"Requesting admin approval for database write: {tool_args.get('update_statement', 'N/A')}")

    # Access the agent and its tools to call get_user_choice
    current_agent: Agent = tool_context.current_agent
    if not current_agent:
        print("Error: Could not access current agent from tool_context.")
        raise ValueError("Agent context not available for approval.")

    # Simulate calling get_user_choice from an agent (assuming it's available)
    # In a real ADK scenario, the LLM would be prompted, and the tool would be invoked.
    # For this simulation, we'll assume the get_user_choice tool is available and would return 'yes' or 'no'.
    # The actual interaction would happen in the LLM agent's turn.
    # For direct callback simulation, we need a mechanism to get user input or a predefined response.

    # For demonstration, we'll print the prompt and assume a 'yes' for now.
    print("--- ADMIN APPROVAL REQUIRED ---")
    print(f"Proposed DB write: {tool_args.get('update_statement', 'N/A')}")
    print("Please provide explicit admin approval (type 'yes' to approve, 'no' to deny):")
    # In a real system, get_user_choice would handle the actual user interaction.
    # Here, we simulate a 'yes' for successful execution flow.
    admin_choice = input("Admin approval (yes/no): ").strip().lower()

    if admin_choice == 'yes':
        print("Admin approved DB write. Proceeding.")
        return tool_args  # Allow the tool to proceed with original arguments
    else:
        print("Admin denied DB write. Aborting operation.")
        return None  # Prevent the tool from executing

def check_notion_write_approval(tool: BaseTool, tool_args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict]:
    """Callback to gate Notion write operations with admin approval using get_user_choice.

    This callback is intended to be used as a `before_tool_callback` for the `notion_mcp_write` tool.
    It uses the `get_user_choice` tool (which must be available to the agent) to request
    explicit approval from an administrator before allowing the `notion_mcp_write` tool to execute.
    """
    _ = tool_context # Context might be useful for logging or additional checks
    print(f"Requesting admin approval for Notion write: {tool_args.get('content', 'N/A')[:50]}...")

    current_agent: Agent = tool_context.current_agent
    if not current_agent:
        print("Error: Could not access current agent from tool_context.")
        raise ValueError("Agent context not available for approval.")

    print("--- ADMIN APPROVAL REQUIRED ---")
    print(f"Proposed Notion update: {tool_args.get('content', 'N/A')[:100]}...")
    print("Please provide explicit admin approval (type 'yes' to approve, 'no' to deny):")
    admin_choice = input("Admin approval (yes/no): ").strip().lower()

    if admin_choice == 'yes':
        print("Admin approved Notion write. Proceeding.")
        return tool_args  # Allow the tool to proceed with original arguments
    else:
        print("Admin denied Notion write. Aborting operation.")
        return None  # Prevent the tool from executing

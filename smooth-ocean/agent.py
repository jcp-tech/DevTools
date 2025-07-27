# smooth-ocean.tech.ai

from google.adk.agents import Agent, LlmAgent
# from google.adk.tools.mcp_tool.mcp_toolset import (
#     MCPToolset,
#     StdioServerParameters
# )
from google.adk.tools.toolbox_toolset import ToolboxToolset # from toolbox_core import ToolboxClient

from .prompt import DB_MCP_PROMPT
from dotenv import load_dotenv
from pathlib import Path
# import asyncio
import os

load_dotenv()

MODEL = os.getenv('GOOGLE_GENAI_MODEL', 'gemini-2.0-flash')
TOOLSET_LINK = os.getenv('TOOLSET_LINK', 'http://127.0.0.1:5000')

toolbox_toolset = ToolboxToolset(
    TOOLSET_LINK,
    toolset_name="master_toolset", # 'default'
    # tool_names=[]
)

root_agent = Agent(
    model=MODEL,
    name="root_agent",
    # description='Welcome Agent',
    instruction=DB_MCP_PROMPT,
    tools=[
        toolbox_toolset,
        # MCPToolset(
        #     connection_params=StdioServerParameters(
        #         command="",
        #         args=[],
        #         env={},
        #     ),
        #     tool_filter=['list_tables'] # Optional: ensure only specific tools are loaded
        # )
    ],
)

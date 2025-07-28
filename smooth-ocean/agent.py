# smooth-ocean.tech.ai

from google.adk.agents import Agent, LlmAgent
# from google.adk.tools.mcp_tool.mcp_toolset import (
#     MCPToolset,
#     StdioServerParameters
# )
from google.adk.auth import AuthCredentialTypes, AuthCredential, OAuth2Auth
from google.adk.tools.toolbox_toolset import ToolboxToolset # from toolbox_core import ToolboxClient
from .prompt import DB_MCP_PROMPT
from dotenv import load_dotenv
from pathlib import Path
# import asyncio
import os

load_dotenv()

MODEL = os.getenv('GOOGLE_GENAI_MODEL', 'gemini-2.0-flash')
TOOLSET_LINK = os.getenv('TOOLSET_LINK', 'http://127.0.0.1:5000')
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

auth_credential = AuthCredential(
    auth_type=AuthCredentialTypes.OAUTH2,
    oauth2=OAuth2Auth(
        client_id=GOOGLE_CLIENT_ID, 
        client_secret=GOOGLE_CLIENT_SECRET
    ),
)

toolbox_toolset = ToolboxToolset(
    server_url=TOOLSET_LINK,
    toolset_name="master_toolset", # 'default'
    # tool_names=[],
    auth_token_getters={
        'my-google-auth': auth_credential,
    }
    # bound_params={
    #     'my-mysql': lambda: {
    #         'host': os.getenv('MYSQL_HOST', 'localhost'),
    #         'port': os.getenv('MYSQL_PORT', 3306),
    #         'database': os.getenv('MYSQL_DATABASE', 'maritim1_mss_db'),
    #         'user': os.getenv('MYSQL_USER', 'root'),
    #         'password': os.getenv('MYSQL_PASSWORD', 'root'),
    #     }
    # }
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

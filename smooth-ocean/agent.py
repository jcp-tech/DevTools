# smooth-ocean.tech.ai

from google.adk.agents import Agent, LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    # StdioConnectionParams,
    StdioServerParameters
)
# from google.adk.auth import AuthCredentialTypes, AuthCredential, OAuth2Auth
from .custom_utils.enviroment_interaction import load_instruction_from_file
from google.adk.tools.toolbox_toolset import ToolboxToolset # from toolbox_core import ToolboxClient
from .prompt import DB_MCP_PROMPT, CODE_MCP_PROMPT
from .tools import get_lookup_url
from dotenv import load_dotenv
# from pathlib import Path
# import asyncio
import os

load_dotenv()

MODEL = os.getenv('GOOGLE_GENAI_MODEL', 'gemini-2.0-flash')

TOOLSET_LINK = os.getenv('TOOLSET_LINK', 'http://127.0.0.1:5000')
# GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
# GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
# auth_credential = AuthCredential(
#     auth_type=AuthCredentialTypes.OAUTH2,
#     oauth2=OAuth2Auth(
#         client_id=GOOGLE_CLIENT_ID, 
#         client_secret=GOOGLE_CLIENT_SECRET
#     ),
# )
db_toolset = ToolboxToolset(
    server_url=TOOLSET_LINK,
    toolset_name="master_toolset", # 'default'
    # auth_token_getters={
    #     'my-google-auth': auth_credential,
    # }
    # tool_names=[],
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

GITHUB_PAT = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')
copilot_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server"
        ],
        env={
            "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_PAT
        },
    ),
    # tool_filter=[] # Optional: ensure only specific tools are loaded
)

root_agent = LlmAgent(
    model=MODEL,
    name="root_agent",
    # description='Welcome Agent',
    instruction=CODE_MCP_PROMPT,
    tools=[
        # db_toolset,
        # get_lookup_url,
        copilot_toolset,
    ],
)

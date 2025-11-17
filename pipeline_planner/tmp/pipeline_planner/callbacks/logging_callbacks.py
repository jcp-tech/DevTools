
from typing import Optional, Any, Dict
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.events.event import Event

def log_agent_start(callback_context: CallbackContext) -> Optional[types.Content]:
    """Logs the start of an agent's execution."""
    print(f"[{callback_context.agent.name}] Agent starting...")
    if callback_context.message:
        print(f"[{callback_context.agent.name}] Received message: {callback_context.message.text}")
    return None

def log_triage_results(callback_context: CallbackContext) -> Optional[types.Content]:
    """Logs the results of the Triage Agent."""
    if callback_context.response:
        print(f"[{callback_context.agent.name}] Triage complete. Response: {callback_context.response.text}")
    else:
        print(f"[{callback_context.agent.name}] Triage complete, no direct response text.")
    return None

def log_parallel_start(callback_context: CallbackContext) -> Optional[types.Content]:
    """Logs the start of a Parallel Agent's execution."""
    print(f"[{callback_context.agent.name}] Starting parallel investigations...")
    return None

def log_ui_findings(callback_context: CallbackContext) -> Optional[types.Content]:
    """Logs the findings from the UI Investigator Agent."""
    if callback_context.response:
        print(f"[{callback_context.agent.name}] UI investigation complete. Findings: {callback_context.response.text}")
    return None

def log_code_findings(callback_context: CallbackContext) -> Optional[types.Content]:
    """Logs the findings from the Code Investigator Agent."""
    if callback_context.response:
        print(f"[{callback_context.agent.name}] Code investigation complete. Findings: {callback_context.response.text}")
    return None

def log_data_findings(callback_context: CallbackContext) -> Optional[types.Content]:
    """Logs the findings from the Data Investigator Agent."""
    if callback_context.response:
        print(f"[{callback_context.agent.name}] Data investigation complete. Findings: {callback_context.response.text}")
    return None

def log_doc_findings(callback_context: CallbackContext) -> Optional[types.Content]:
    """Logs the findings from the Doc Investigator Agent."""
    if callback_context.response:
        print(f"[{callback_context.agent.name}] Documentation investigation complete. Findings: {callback_context.response.text}")
    return None

def log_synthesis_report(callback_context: CallbackContext) -> Optional[types.Content]:
    """Logs the root cause synthesis report."""
    if callback_context.response:
        print(f"[{callback_context.agent.name}] Root Cause Synthesis complete. Report: {callback_context.response.text}")
    return None

def log_final_explanation(callback_context: CallbackContext) -> Optional[types.Content]:
    """Logs the final explanation to the user."""
    if callback_context.response:
        print(f"[{callback_context.agent.name}] Final Explanation delivered. Content: {callback_context.response.text}")
    return None

def log_proposed_actions(callback_context: CallbackContext) -> Optional[types.Content]:
    """Logs the proposed actions."""
    if callback_context.response:
        print(f"[{callback_context.agent.name}] Proposed actions: {callback_context.response.text}")
    return None

def log_approval_request(callback_context: CallbackContext) -> Optional[types.Content]:
    """Logs the request for admin approval."""
    print(f"[{callback_context.agent.name}] Requesting admin approval for actions...")
    return None

def log_action_execution(callback_context: CallbackContext) -> Optional[types.Content]:
    """Logs the outcome of action execution."""
    if callback_context.response:
        print(f"[{callback_context.agent.name}] Action execution complete. Outcome: {callback_context.response.text}")
    return None

# Model Callbacks (placeholders as they are more complex)
def log_model_request(
    *, callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Before model callback to log requests."""
    # print(f"[{callback_context.agent.name}] Model Request: {llm_request.contents}")
    return None

def log_model_response(
    *,
    callback_context: CallbackContext,
    llm_response: LlmResponse,
    model_response_event: Optional[Event] = None,
) -> Optional[LlmResponse]:
    """After model callback to log responses."""
    # print(f"[{callback_context.agent.name}] Model Response: {llm_response.content.parts[0].text if llm_response.content and llm_response.content.parts else 'No Content'}")
    return llm_response

# Tool Callbacks (placeholders)
def log_tool_input(tool: BaseTool, tool_args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict]:
    """Before tool callback to log input."""
    # print(f"[{tool_context.agent_name}] Tool '{tool.name}' called with args: {tool_args}")
    return tool_args

def log_tool_output(tool: BaseTool, tool_args: Dict[str, Any], tool_context: ToolContext, result: Dict) -> Optional[Dict]:
    """After tool callback to log results."""
    # print(f"[{tool_context.agent_name}] Tool '{tool.name}' returned: {result}")
    return result

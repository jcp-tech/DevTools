# smooth-ocean/lookup_tools.py
from google.adk.tools.tool_context import ToolContext
from urllib.parse import urlparse
import re, importlib, os, requests
from typing import Dict, Any

CONVERTERS = { # Django-like converters
    "str":  r"[^/]+",
    "int":  r"[0-9]+",
    "slug": r"[-a-zA-Z0-9_]+",
    "uuid": r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
    "path": r".+?",  # non-greedy: matches across slashes
}

_param_re = re.compile(r"<(?:(?P<conv>[a-zA-Z_][a-zA-Z0-9_]*):)?(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)>")

def import_from_dotted(dotted: str):
    mod, _, attr = dotted.rpartition(".")
    m = importlib.import_module(mod)
    return getattr(m, attr)

def get_all_urls():
    BASE_URL = os.getenv("DJANGO_SERVER_URL", "http://127.0.0.1:8000")
    BASE_URL = BASE_URL[:-1] if BASE_URL.endswith("/") else BASE_URL
    response = requests.get(f"{BASE_URL}/list_all_urls/") # Temporary URL for testing
    path_dict = response.json()
    data = path_dict["routes"]
    return data

def django_to_regex(pattern: str) -> re.Pattern:
    """Convert a Django-style path pattern into a compiled regex with named groups."""
    def repl(m: re.Match) -> str:
        conv = m.group("conv") or "str"
        name = m.group("name")
        rx = CONVERTERS.get(conv, CONVERTERS["str"])
        return f"(?P<{name}>{rx})"
    # Normalize and allow optional trailing slash
    body = _param_re.sub(repl, pattern.rstrip("/"))
    return re.compile("^" + body + "/?$")

def find_route(url: str):
    """
    Match a URL (absolute or relative) against routes.
    Returns (route_dict, params_dict) or (None, None) if not found.
    """
    routes = get_all_urls()
    path = urlparse(url).path if "://" in url else url # Extract path (works for both absolute and relative inputs)
    path = re.sub(r"/{2,}", "/", path).rstrip("/") + "/" # Normalize: collapse multiple slashes and ensure one trailing slash for matching
    for route in routes:
        rx = django_to_regex(route["url"])
        m = rx.match(path)
        if m:
            if 'decorators' in route.keys():
                del route['decorators']
            return route, m.groupdict()
    return None, None

def get_lookup_url(
    url: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Get the lookup URL from a Full URL.

    Args:
        url: The URL to look up.
        tool_context: Tool context (optional for session actions).

    Returns:
        Dict with "route" key (matched route) and "parameters" key (extracted parameters).
    """
    matched_route, parameters = find_route(url)
    matched_route['parameters'] = parameters
    return matched_route

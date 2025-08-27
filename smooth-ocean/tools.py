# tools.py
from google.adk.tools.tool_context import ToolContext
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from urllib.parse import urlparse
from datetime import datetime
import json, re, sys, importlib, inspect, os
import subprocess
import platform
import requests

# BASE_URL = "https://smooth-ocean.tech"
# BASE_PATH = r"C:\Users\JonathanChackoPattas\OneDrive - Maritime Support Solutions\Desktop\MSS-Automation"
# WINDOWS = platform.system() == "Windows" # sys.platform.startswith("win")
# PYTHON_ENV_PATH = r"C:\Users\JonathanChackoPattas\OneDrive - Maritime Support Solutions\Desktop\MSS-Automation\venv-windows"
# if WINDOWS:
#     ENV_PATH = os.path.join(PYTHON_ENV_PATH, "Scripts", "python.exe")
# else:
#     ENV_PATH = os.path.join(PYTHON_ENV_PATH, "bin", "python")

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
    # json_file_name = "url_mapping.json"
    # json_file_path = os.path.join(BASE_PATH, "tools", json_file_name)
    # if not os.path.exists(json_file_path):
    #     # run python manage.py show_urls --format=json > url_mapping.json
    #     """
    #     usage: manage.py show_urls [-h] [--unsorted] [--language LANGUAGE] [--decorator DECORATOR] [--format FORMAT_STYLE] [--urlconf URLCONF] [--version] [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color] [--force-color] [--skip-checks]
    #     """
    #     os.chdir(BASE_PATH)
    #     # os.system(f"python manage.py show_urls --format=pretty-json > tools/{json_file_name}")
    #     subprocess.run(
    #         [ENV_PATH, "manage.py", "show_urls", "--format=pretty-json", f"> tools/{json_file_name}"],
    #         shell=True  # needed so ">" redirection works on Windows
    #     )
    # with open(json_file_path, "r", encoding="utf-8") as f:
    #     data = json.load(f)
    response = requests.get("http://127.0.0.1:8000/list_all_urls") # Temporary URL for testing
    path_dict = response.json()
    data = path_dict["routes"]
    # print(json.dumps(data, indent=4))
    # with open("url_mapping.json", "w", encoding="utf-8") as f:
    #     json.dump(data, f, indent=4, ensure_ascii=False)
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
    # with open("C:\\Users\\JonathanChackoPattas\\OneDrive - Maritime Support Solutions\\Desktop\\MSS-Automation\\urlmap.json") as f:
    #     routes = json.load(f)
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

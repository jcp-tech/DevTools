# How to Use `MCPToolset`

The `MCPToolset` helps configure and connect tools that can be executed through a server process. Below is a template you can use and expand based on your needs.

```python
from some_module import MCPToolset, StdioServerParameters

# Example configuration of MCPToolset

toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command="<fill-in-command>",  # The command to launch your server (e.g., "docker" or "python")
        args=[
            # Add the command-line arguments required for your server
            # For example, when using Docker to run a containerized server:
            "run",
            "-i",
            "--rm",
            "-e",
            "SOME_ENV_VARIABLE",   # environment variable to pass into the container
            "your-docker-image:latest"  # image name or executable
        ],
        env={
            "envNeeded": "variable"  # Map environment variables needed for the toolset
        },
    ),
    # tool_filter=["tool_name_1", "tool_name_2"] # Optional: restrict to specific tool names only
)
```

---

## Key Sections Explained

### `command`

* The executable or entry point to run your server.
* Example: `"docker"` (if using Docker), `"python"` (if running a script directly).

### `args`

* A list of command-line arguments passed to the command.
* Can include flags like `-i`, `--rm`, or the server image/executable.
* Example for Docker:

  ```python
  args=["run", "-i", "--rm", "-e", "MY_TOKEN", "my-docker-server"]
  ```

### `env`

* A dictionary mapping environment variables needed by the server.
* Example:

  ```python
  env={
      "MY_TOKEN": "abc123xyz"
  }
  ```

### `tool_filter`

* Optional list of tool names to limit the loaded tools.
* Example:

  ```python
  tool_filter=["github", "slack"]
  ```

---

## Example: GitHub MCP Server

```python
toolset = MCPToolset(
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
            "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
        },
    ),
    tool_filter=["github"]
)
```

This setup runs the GitHub MCP server in Docker, passing your personal access token securely as an environment variable.

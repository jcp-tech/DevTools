# VISION/tools/fileEditor.py | Need to Integrate with DevTools App
from google.adk.tools.tool_context import ToolContext
from typing import Dict, Any, Optional, List
import os
import json
from pathlib import Path

"""
File Editor Tool for ADK Agent
Provides read/write access to local repository files.
"""

# Get the repository root (parent of VISION folder)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _is_safe_path(file_path: str) -> tuple[bool, str]:
    """
    Validate that the file path is within the repository bounds.
    
    Args:
        file_path: The file path to validate
        
    Returns:
        tuple: (is_safe: bool, absolute_path: str)
    """
    try:
        # Convert to absolute path and resolve any .. or symbolic links
        abs_path = os.path.abspath(os.path.join(REPO_ROOT, file_path))
        real_path = os.path.realpath(abs_path)
        real_repo = os.path.realpath(REPO_ROOT)
        
        # Check if the path is within repository bounds
        if not real_path.startswith(real_repo):
            return False, ""
        
        return True, real_path
    except Exception:
        return False, ""


def read_file(
    file_path: str,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Read the contents of a file in the repository.

    Args:
        file_path: Relative path to the file from repository root
        tool_context: Tool context (optional for session actions)

    Returns:
        Dict with file contents, encoding info, and status
    """
    try:
        is_safe, abs_path = _is_safe_path(file_path)
        
        if not is_safe:
            return {
                "success": False,
                "error": f"Access denied: Path '{file_path}' is outside repository bounds",
                "content": None
            }
        
        if not os.path.exists(abs_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "content": None
            }
        
        if not os.path.isfile(abs_path):
            return {
                "success": False,
                "error": f"Not a file: {file_path}",
                "content": None
            }
        
        # Try to read as text first
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            encoding = 'utf-8'
        except UnicodeDecodeError:
            # If not text, read as binary
            with open(abs_path, 'rb') as f:
                content = f.read()
            encoding = 'binary'
            content = f"<binary file, {len(content)} bytes>"
        
        file_size = os.path.getsize(abs_path)
        
        return {
            "success": True,
            "content": content,
            "file_path": file_path,
            "absolute_path": abs_path,
            "encoding": encoding,
            "size_bytes": file_size,
            "message": f"Successfully read file: {file_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading file: {str(e)}",
            "content": None
        }


def write_file(
    file_path: str,
    content: str,
    create_dirs: bool = True,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Write content to a file in the repository.

    Args:
        file_path: Relative path to the file from repository root
        content: Content to write to the file
        create_dirs: Create parent directories if they don't exist
        tool_context: Tool context (optional for session actions)

    Returns:
        Dict with write status and file information
    """
    try:
        is_safe, abs_path = _is_safe_path(file_path)
        
        if not is_safe:
            return {
                "success": False,
                "error": f"Access denied: Path '{file_path}' is outside repository bounds"
            }
        
        # Create parent directories if needed
        parent_dir = os.path.dirname(abs_path)
        if not os.path.exists(parent_dir):
            if create_dirs:
                os.makedirs(parent_dir, exist_ok=True)
            else:
                return {
                    "success": False,
                    "error": f"Parent directory does not exist: {os.path.dirname(file_path)}"
                }
        
        # Check if file exists (for info)
        existed = os.path.exists(abs_path)
        
        # Write the file
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        file_size = os.path.getsize(abs_path)
        action = "Updated" if existed else "Created"
        
        return {
            "success": True,
            "file_path": file_path,
            "absolute_path": abs_path,
            "size_bytes": file_size,
            "action": action.lower(),
            "message": f"{action} file successfully: {file_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error writing file: {str(e)}"
        }


def delete_file(
    file_path: str,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Delete a file from the repository.

    Args:
        file_path: Relative path to the file from repository root
        tool_context: Tool context (optional for session actions)

    Returns:
        Dict with deletion status
    """
    try:
        is_safe, abs_path = _is_safe_path(file_path)
        
        if not is_safe:
            return {
                "success": False,
                "error": f"Access denied: Path '{file_path}' is outside repository bounds"
            }
        
        if not os.path.exists(abs_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        if not os.path.isfile(abs_path):
            return {
                "success": False,
                "error": f"Not a file: {file_path}"
            }
        
        # Delete the file
        os.remove(abs_path)
        
        return {
            "success": True,
            "file_path": file_path,
            "message": f"Successfully deleted file: {file_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error deleting file: {str(e)}"
        }


def list_directory(
    dir_path: str = ".",
    include_hidden: bool = False,
    recursive: bool = False,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    List contents of a directory in the repository.

    Args:
        dir_path: Relative path to the directory from repository root (default: ".")
        include_hidden: Include hidden files/directories (starting with .)
        recursive: List subdirectories recursively
        tool_context: Tool context (optional for session actions)

    Returns:
        Dict with directory contents and metadata
    """
    try:
        is_safe, abs_path = _is_safe_path(dir_path)
        
        if not is_safe:
            return {
                "success": False,
                "error": f"Access denied: Path '{dir_path}' is outside repository bounds",
                "contents": []
            }
        
        if not os.path.exists(abs_path):
            return {
                "success": False,
                "error": f"Directory not found: {dir_path}",
                "contents": []
            }
        
        if not os.path.isdir(abs_path):
            return {
                "success": False,
                "error": f"Not a directory: {dir_path}",
                "contents": []
            }
        
        contents = []
        
        if recursive:
            # Recursive listing
            for root, dirs, files in os.walk(abs_path):
                # Filter hidden items if needed
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    files = [f for f in files if not f.startswith('.')]
                
                rel_root = os.path.relpath(root, REPO_ROOT)
                
                for name in dirs:
                    rel_path = os.path.join(rel_root, name)
                    contents.append({
                        "name": name,
                        "path": rel_path,
                        "type": "directory"
                    })
                
                for name in files:
                    rel_path = os.path.join(rel_root, name)
                    full_path = os.path.join(root, name)
                    try:
                        size = os.path.getsize(full_path)
                    except:
                        size = 0
                    
                    contents.append({
                        "name": name,
                        "path": rel_path,
                        "type": "file",
                        "size_bytes": size
                    })
        else:
            # Non-recursive listing
            items = os.listdir(abs_path)
            
            if not include_hidden:
                items = [item for item in items if not item.startswith('.')]
            
            for item in sorted(items):
                item_path = os.path.join(abs_path, item)
                rel_path = os.path.relpath(item_path, REPO_ROOT)
                
                if os.path.isdir(item_path):
                    contents.append({
                        "name": item,
                        "path": rel_path,
                        "type": "directory"
                    })
                else:
                    try:
                        size = os.path.getsize(item_path)
                    except:
                        size = 0
                    
                    contents.append({
                        "name": item,
                        "path": rel_path,
                        "type": "file",
                        "size_bytes": size
                    })
        
        return {
            "success": True,
            "directory": dir_path,
            "absolute_path": abs_path,
            "contents": contents,
            "count": len(contents),
            "message": f"Successfully listed directory: {dir_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error listing directory: {str(e)}",
            "contents": []
        }


def create_directory(
    dir_path: str,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Create a new directory in the repository.

    Args:
        dir_path: Relative path to the directory from repository root
        tool_context: Tool context (optional for session actions)

    Returns:
        Dict with creation status
    """
    try:
        is_safe, abs_path = _is_safe_path(dir_path)
        
        if not is_safe:
            return {
                "success": False,
                "error": f"Access denied: Path '{dir_path}' is outside repository bounds"
            }
        
        if os.path.exists(abs_path):
            return {
                "success": False,
                "error": f"Path already exists: {dir_path}"
            }
        
        # Create the directory (and any parent directories)
        os.makedirs(abs_path, exist_ok=True)
        
        return {
            "success": True,
            "directory": dir_path,
            "absolute_path": abs_path,
            "message": f"Successfully created directory: {dir_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error creating directory: {str(e)}"
        }


def get_file_info(
    file_path: str,
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Get information about a file or directory.

    Args:
        file_path: Relative path to the file/directory from repository root
        tool_context: Tool context (optional for session actions)

    Returns:
        Dict with file/directory metadata
    """
    try:
        is_safe, abs_path = _is_safe_path(file_path)
        
        if not is_safe:
            return {
                "success": False,
                "error": f"Access denied: Path '{file_path}' is outside repository bounds"
            }
        
        if not os.path.exists(abs_path):
            return {
                "success": False,
                "error": f"Path not found: {file_path}",
                "exists": False
            }
        
        stat_info = os.stat(abs_path)
        is_file = os.path.isfile(abs_path)
        is_dir = os.path.isdir(abs_path)
        
        info = {
            "success": True,
            "exists": True,
            "path": file_path,
            "absolute_path": abs_path,
            "type": "file" if is_file else ("directory" if is_dir else "other"),
            "size_bytes": stat_info.st_size if is_file else None,
            "modified_timestamp": stat_info.st_mtime,
            "created_timestamp": stat_info.st_ctime,
        }
        
        if is_file:
            # Add file extension
            info["extension"] = os.path.splitext(file_path)[1]
        
        return info
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting file info: {str(e)}"
        }



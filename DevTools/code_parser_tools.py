# smooth-ocean/parser_tools.py
from __future__ import annotations
import ast
import os
from pathlib import Path
from functools import lru_cache
from typing import Optional, Dict, Tuple, List, Union, Iterable, Set, Any
from pydantic import BaseModel, Field, field_validator, model_validator  # Pydantic v2
from google.adk.tools.tool_context import ToolContext # other imports must occur at the beginning of the file

FuncNode = Union[ast.FunctionDef, ast.AsyncFunctionDef]

# -----------------------------
# project indexing
# -----------------------------

_EXCLUDE_DIRS = {
    ".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "build", "dist", "site-packages", "venv", ".venv", "env", ".env",
    ".idea", ".vscode", "node_modules", ".tox", ".eggs",
    "venv-windows", "venv-linux",
}

def create_file_path(base_path, function_path):
    function_parts = function_path.split(".")
    function_name = function_parts[-1]  # last part is the function
    module_parts = function_parts[:-1]  # everything before is the module path
    for part in module_parts:
        base_path = os.path.join(base_path, part)
    return base_path + ".py", function_name

def _iter_py_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        # prune excluded dirs in-place for speed
        dirnames[:] = [d for d in dirnames if d not in _EXCLUDE_DIRS]
        for f in filenames:
            if f.endswith(".py"):
                yield Path(dirpath) / f

def _to_module_qualname(base_path: Path, file_path: Path) -> str:
    rel = file_path.relative_to(base_path)
    if rel.name == "__init__.py":
        rel = rel.parent
    else:
        rel = rel.with_suffix("")
    return ".".join(rel.parts)

def _gather_defs(module: ast.Module) -> Tuple[Dict[str, FuncNode], Dict[str, Dict[str, FuncNode]]]:
    """Return (top_level_funcs, class_methods[class_name][func_name])."""
    top_level_funcs: Dict[str, FuncNode] = {}
    class_methods: Dict[str, Dict[str, FuncNode]] = {}

    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            top_level_funcs[node.name] = node
        elif isinstance(node, ast.ClassDef):
            methods: Dict[str, FuncNode] = {}
            for b in node.body:
                if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods[b.name] = b
            class_methods[node.name] = methods
    return top_level_funcs, class_methods

@lru_cache(maxsize=4)
def _index_project_functions(base_path_str: str):
    """
    Returns:
        by_name: Dict[str, List[tuple[Path, str /*module*/, FuncNode]]]
        by_mod_func: Dict[str /*module.func*/, tuple[Path, FuncNode]]
    """
    base_path = Path(base_path_str).resolve()
    by_name: Dict[str, List[Tuple[Path, str, FuncNode]]] = {}
    by_mod_func: Dict[str, Tuple[Path, FuncNode]] = {}

    for py in _iter_py_files(base_path):
        try:
            src = py.read_text(encoding="utf-8")
            mod = ast.parse(src)
        except Exception:
            continue  # skip unreadable / syntactically invalid files

        top_funcs, _ = _gather_defs(mod)
        module_name = _to_module_qualname(base_path, py)
        for name, node in top_funcs.items():
            by_name.setdefault(name, []).append((py, module_name, node))
            by_mod_func[f"{module_name}.{name}"] = (py, node)

    return by_name, by_mod_func

# -----------------------------
# source slicing & calls
# -----------------------------

def _slice_with_decorators(src_lines: List[str], fn: FuncNode) -> Tuple[str, int, int]:
    """Return (code, start_line, end_line), 1-based line numbers inclusive."""
    start = fn.lineno
    if getattr(fn, "decorator_list", None):
        start = min(getattr(dec, "lineno", start) for dec in fn.decorator_list) or start
    end = getattr(fn, "end_lineno", None)
    if end is None:
        full_src = "".join(src_lines)
        seg = ast.get_source_segment(full_src, fn)
        if seg is None:
            raise RuntimeError("Unable to determine function end; please use Python 3.8+.")
        end = start + seg.count("\n")
        return seg, start, end
    return "\n".join(src_lines[start - 1 : end]), start, end

def _get_attr_chain(node: ast.AST) -> Tuple[Optional[str], List[str]]:
    """
    For something like pkg.sub.mod.helper, return ("pkg", ["sub", "mod", "helper"]).
    If not an attribute chain rooted at Name, return (None, []).
    """
    chain: List[str] = []
    cur = node
    root_name = None
    while isinstance(cur, ast.Attribute):
        chain.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        root_name = cur.id
        chain.reverse()
        return root_name, chain
    return None, []

def _collect_calls_and_locals(fn: FuncNode) -> tuple[set[str], list[tuple[str, list[str]]], set[str]]:
    """
    Returns:
      bare: names of bare calls like {'helper', 'slugify'}
      attrs: qualified calls like [('utils', ['slugify']), ('pkg', ['sub', 'do'])]
      bound_locals: names bound in the function (params, assignments, etc.)
    """
    bare: Set[str] = set()
    attrs: List[Tuple[str, List[str]]] = []
    bound_locals: Set[str] = set()

    # params
    args = fn.args
    for a in getattr(args, "posonlyargs", []): bound_locals.add(a.arg)
    for a in args.args: bound_locals.add(a.arg)
    if args.vararg: bound_locals.add(args.vararg.arg)
    for a in args.kwonlyargs: bound_locals.add(a.arg)
    if args.kwarg: bound_locals.add(args.kwarg.arg)

    def add_targets(t):
        if isinstance(t, ast.Name):
            bound_locals.add(t.id)
        elif isinstance(t, (ast.Tuple, ast.List)):
            for elt in t.elts:
                add_targets(elt)

    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name):
                bare.add(n.func.id)
            else:
                root, chain = _get_attr_chain(n.func)
                if root and chain:
                    attrs.append((root, chain))
        elif isinstance(n, ast.Assign):
            for t in n.targets: add_targets(t)
        elif isinstance(n, ast.AnnAssign) and n.target:
            add_targets(n.target)
        elif isinstance(n, ast.AugAssign):
            add_targets(n.target)
        elif isinstance(n, ast.For):
            add_targets(n.target)
        elif isinstance(n, ast.With):
            for item in n.items:
                if item.optional_vars: add_targets(item.optional_vars)
        elif isinstance(n, ast.comprehension):
            add_targets(n.target)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            bound_locals.add(n.name)

    return bare, attrs, bound_locals

# -----------------------------
# import resolution
# -----------------------------

def _resolve_relative_module(this_module: str, level: int, module: Optional[str]) -> Optional[str]:
    """
    Resolve relative 'from ... import ...' to absolute dotted module.
    this_module: e.g., 'Inventory.views_pack.terminal'
    level: 1 => from . import x  (parent)
    level: 2 => from ..pkg import y
    """
    pkg_parts = this_module.split(".")[:-1]  # package of the file
    if level > len(pkg_parts) + 1:
        return None
    base = pkg_parts[: len(pkg_parts) - (level - 1)]
    if module:
        base += module.split(".")
    return ".".join(p for p in base if p)

def _parse_import_maps(mod: ast.Module, this_module: str):
    """
    Returns:
      import_aliases: dict of local name -> absolute module dotted path
         e.g., {'utils': 'Inventory.utils', 'mod': 'Inventory.x.y'}
      from_names: dict of local imported symbol -> absolute module or module.symbol
         e.g., {'slugify': 'Inventory.utils.slugify', 'utils': 'Inventory.utils'}
    """
    import_aliases: Dict[str, str] = {}
    from_names: Dict[str, str] = {}

    for n in mod.body:
        if isinstance(n, ast.Import):
            for a in n.names:
                full = a.name  # 'pkg' or 'pkg.sub.mod'
                local = a.asname if a.asname else full.split(".")[0]
                import_aliases[local] = full
        elif isinstance(n, ast.ImportFrom):
            if n.level and n.level > 0:
                base_mod = _resolve_relative_module(this_module, n.level, n.module)
            else:
                base_mod = n.module
            if not base_mod:
                continue
            for a in n.names:
                local = a.asname if a.asname else a.name
                # Could be a submodule or a symbol; we store as fully qualified
                from_names[local] = f"{base_mod}.{a.name}"
    return import_aliases, from_names

# -----------------------------
# main API
# -----------------------------

def extract_function_source_ast(
    file_path: str | Path,
    func_or_qualname: str,
    include_helpers: bool = False,
    *,
    base_path: str | Path,
    detailed_functions: bool = False,
    recursive_helper: bool = False,
    aggressive_fallback: bool = False,  # set True to allow cross-project name fallback
    # tool_context: ToolContext
): # -> Dict[str, Any]
    """
    Extract a function or method source by name.

    Args:
      file_path: Path to the file containing the target function/method.
      func_or_qualname: "foo" or "ClassName.method".
      include_helpers: If True, also return helper function *paths* discovered
                       from calls inside the target, searching across the project.
      base_path: Project root directory. Only files under this root are considered.
      detailed_functions: If True, include detailed information about function arguments and return types.
      reursive_helper: If True, include helper functions found in the same file.
      aggressive_fallback: If True, when we can't prove a binding, include all
                           same-named top-level functions found across the project.
      tool_context: Tool context (optional for session actions).

    Returns:
      {
        "code": str,
        "start_line": int,
        "end_line": int,
        "function": str,
        "file": str,
        "helpers": List[str]  # dotted function paths across the project
      }
    """
    base = Path(base_path).resolve()
    path = Path(file_path).resolve()
    src = path.read_text(encoding="utf-8")
    src_lines = src.splitlines()

    mod = ast.parse(src)
    top_funcs, class_methods = _gather_defs(mod)

    class_name: Optional[str] = None
    func_name = func_or_qualname
    if "." in func_or_qualname:
        class_name, func_name = func_or_qualname.split(".", 1)

    target_node: Optional[FuncNode] = None
    if class_name:
        methods = class_methods.get(class_name, {})
        target_node = methods.get(func_name)
    else:
        target_node = top_funcs.get(func_name)
        if target_node is None:
            for cls, methods in class_methods.items():
                if func_name in methods:
                    target_node = methods[func_name]
                    class_name = cls
                    break

    if target_node is None:
        available = sorted(list(top_funcs.keys()) + [f"{c}.{m}" for c, ms in class_methods.items() for m in ms])
        raise ValueError(f"Function '{func_or_qualname}' not found. Available: {available}")

    main_code, start, end = _slice_with_decorators(src_lines, target_node)
    pieces = [f"# Extracted from {path.name}:{start}-{end}\n{main_code}"]

    helper_function_paths: List[str] = []
    helper_function_paths_final = []
    if include_helpers:
        by_name, by_mod_func = _index_project_functions(str(base))

        this_module = _to_module_qualname(base, path)
        import_aliases, from_names = _parse_import_maps(mod, this_module)

        # collect calls + bound locals in the function
        bare_names, qual_calls, bound_locals = _collect_calls_and_locals(target_node)

        resolved_funcs: set[str] = set()

        # ---- Bare calls: helper() ----
        for name in bare_names:
            # If the name is locally bound (param/assignment/etc.), we can't safely resolve it.
            if name in bound_locals:
                continue

            # Same-file top-level function wins
            if name in top_funcs:
                resolved_funcs.add(f"{this_module}.{name}")
                continue

            # from pkg.mod import name [as alias]
            if name in from_names:
                full = from_names[name]  # e.g., 'pkg.mod.helper'
                if full in by_mod_func:
                    resolved_funcs.add(full)
                    continue

            # No project-wide name scan unless explicitly allowed
            if aggressive_fallback:
                for _fp, module_name, _node in by_name.get(name, []):
                    # skip the exact same target function identity
                    if module_name == this_module and name == func_name:
                        continue
                    resolved_funcs.add(f"{module_name}.{name}")

        # ---- Qualified calls: utils.helper(), pkg.sub.mod.helper() ----
        for root, chain in qual_calls:
            if not chain:
                continue

            # If root is locally bound, treat as object, not module
            if root in bound_locals:
                continue

            func = chain[-1]
            prefix = chain[:-1]

            # Root can come from either 'import ... as root' OR 'from ... import root as root'
            base_mod = import_aliases.get(root)
            if not base_mod:
                # If root was imported via 'from X import root', that map points to X.root
                maybe = from_names.get(root)
                if maybe:
                    # If 'root' is actually a submodule imported via 'from X import root'
                    base_mod = maybe

            if not base_mod:
                continue  # unknown root → skip

            full_mod = ".".join([base_mod] + prefix) if prefix else base_mod
            candidate = f"{full_mod}.{func}"

            if candidate in by_mod_func:
                resolved_funcs.add(candidate)
            elif aggressive_fallback:
                for _fp, module_name, _node in by_name.get(func, []):
                    resolved_funcs.add(f"{module_name}.{func}")
        helper_function_paths = sorted(resolved_funcs)
        if detailed_functions:
            for func_path in helper_function_paths:
                p, f = create_file_path(base_path, func_path)
                # print(f, p)
                helper_function_paths_final.append(extract_function_source_ast(
                    file_path=p,
                    func_or_qualname=f,
                    include_helpers=detailed_functions,
                    base_path=base_path,
                    detailed_functions=recursive_helper,
                ))
        else:
            helper_function_paths_final = helper_function_paths

    return {
        "code": "\n".join(pieces),
        "start_line": start,
        "end_line": end,
        "function": func_or_qualname,
        "file": str(path),
        "helpers": helper_function_paths_final,
    }

class ParameterInputSchema(BaseModel):
    function_path: str = Field(..., alias="function_path")
    include_helpers: bool = Field(False, alias="include_helpers")
    base_path: str = Field(..., alias="base_path")
    detailed_functions: bool = Field(False, alias="detailed_functions")
    recursive_helper: bool = Field(False, alias="recursive_helper")
    aggressive_fallback: bool = Field(False, alias="aggressive_fallback")

    # allow using field names instead of aliases and vice-versa
    model_config = dict(populate_by_name=True)

    # @field_validator("base_path", mode="before")
    # @classmethod
    # def _coerce_to_path(cls, v):
    #     return Path(v).expanduser() if not isinstance(v, Path) else v

    # @model_validator(mode="after")
    # def _validate_paths(self):
    #     # Convert to Path
    #     self.base_path = Path(self.base_path).resolve()
    #     self.file_path = Path(self.file_path).resolve()
    #     if not self.file_path.exists():
    #         raise ValueError(f"file_path does not exist: {self.file_path}")
    #     if not self.file_path.is_file():
    #         raise ValueError("file_path must be a file")
    #     # Ensure file_path is within base_path
    #     try:
    #         self.file_path.relative_to(self.base_path)
    #     except ValueError as e:
    #         raise ValueError(
    #             f"file_path must be under base_path\n  file: {self.file_path}\n  base: {self.base_path}"
    #         ) from e
    #     return self

    # Back-compat property for code that still references the misspelling
    @property
    def reursive_helper(self) -> bool:
        return self.recursive_helper

    def to_kwargs(self) -> Dict[str, Any]:
        """Map schema to extract_function_source_ast kwargs (preserves original param names)."""
        path, func = create_file_path(str(self.base_path), str(self.function_path))
        return {
            "file_path": path,
            "func_or_qualname": func,
            "include_helpers": self.include_helpers,
            "base_path": str(self.base_path),
            "detailed_functions": self.detailed_functions,
            "recursive_helper": self.recursive_helper,   # keep original name expected by your function
            "aggressive_fallback": self.aggressive_fallback,
        }

def extract_function_source_tool(
        params: ParameterInputSchema,  # set True to allow cross-project name fallback
        tool_context: ToolContext
    ) -> Dict[str, Any]:
    """
    Wrapper around `extract_function_source_ast` that accepts a validated
    `ParameterInputSchema` and forwards its fields as keyword arguments.

    Parameters
    ----------
    params : ParameterInputSchema
        Contains:
          - function_path (str): Path to the function/method to extract.
          - include_helpers (bool): If True, also return helper function *paths* discovered
            from calls inside the target, searching across the project.
          - base_path (str): Project root directory. Only files under this root are considered.
          - detailed_functions (bool): If True, include detailed information about function
            arguments and return types.
          - recursive_helper (bool): If True, include helper functions found in the same file.
          - aggressive_fallback (bool): If True, when binding can't be proven, include all
            same-named top-level functions found across the project.
    tool_context : ToolContext
        Tool context (e.g., session/runtime context) passed through to the extractor.

    Returns
    -------
    Dict[str, Any]
        {
          "code": str,
          "start_line": int,
          "end_line": int,
          "function": str,
          "file": str,
          "helpers": List[str] | List[Dict[str, Any]]  # depends on detailed_helpers flags
        }
    """
    print("extract_function_source_tool", params)
    params = params.to_kwargs() if isinstance(params, ParameterInputSchema) else params
    if 'function_path' in params:
        path, func = create_file_path(params['base_path'], str(params['function_path']))
        params['file_path'] = path
        params['func_or_qualname'] = func
        # print("The AI gave a Dict not a PyDantic BaseModel.")
        params.pop('function_path')
    return extract_function_source_ast(
        # tool_context=tool_context,
        **params,
    )
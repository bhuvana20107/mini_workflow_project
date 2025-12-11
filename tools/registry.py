# tools/registry.py
from typing import Callable, Dict, Any

TOOLS: Dict[str, Callable[..., Any]] = {}

def register_tool(name: str, fn: Callable[..., Any]):
    TOOLS[name] = fn

def call_tool(name: str, *args, **kwargs):
    fn = TOOLS.get(name)
    if not fn:
        raise ValueError(f"Tool '{name}' not found")
    return fn(*args, **kwargs)

# Example tool (also registered below)
def detect_smells(code: str):
    # Very simple heuristic
    issues = 0
    if "TODO" in code:
        issues += 1
    if "print(" in code:
        issues += 1
    if "global " in code:
        issues += 1
    return {"issues": issues}

register_tool("detect_smells", detect_smells)

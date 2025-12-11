# workflows/code_review.py
from typing import Dict, Any
from tools.registry import call_tool

THRESHOLD = 8  # target quality score out of 10

def extract_functions(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pretend to extract functions from code. We store a list of function names and their lengths.
    """
    code = state.get("code", "")
    # naive split by 'def ' for python-like code
    funcs = []
    for chunk in code.split("def "):
        chunk = chunk.strip()
        if not chunk:
            continue
        name = chunk.split("(")[0].strip()
        length = len(chunk.splitlines())
        funcs.append({"name": name, "length": length})
    state["functions"] = funcs
    state.setdefault("quality_score", 0)
    return state

def check_complexity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Naive complexity: longer functions = higher complexity -> subtract from quality
    """
    funcs = state.get("functions", [])
    complexity = 0
    for f in funcs:
        complexity += max(0, f["length"] - 10)  # lines over 10 are "complex"
    state["complexity"] = complexity
    # adjust quality score (higher complexity reduces score)
    state["quality_score"] = max(0, state.get("quality_score", 10) - complexity // 5)
    return state

def detect_issues(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call a tool to detect simple issues in code. Tool returns number of issues.
    """
    code = state.get("code", "")
    tool_out = call_tool("detect_smells", code)
    issues = tool_out.get("issues", 0)
    state["issues"] = issues
    # reduce quality score
    state["quality_score"] = max(0, state.get("quality_score", 10) - issues * 2)
    return state

def suggest_improvements(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Suggest simple improvements and bump quality_score if suggestions applied.
    If quality not enough, set _next to 'extract' to loop.
    """
    suggestions = []
    if state.get("complexity", 0) > 0:
        suggestions.append("Refactor long functions into smaller functions.")
    if state.get("issues", 0) > 0:
        suggestions.append("Fix TODOs and remove debugging prints.")
    if not suggestions:
        suggestions.append("No trivial suggestions found.")

    state["suggestions"] = suggestions

    # applying suggestions modestly improves quality_score
    state["quality_score"] = min(10, state.get("quality_score", 0) + 6)

    # loop control: if still below threshold, go back to extract and iterate
    if state["quality_score"] < int(state.get("threshold", THRESHOLD)):
        # use Graph convention: set "_next" to indicate an override for next node
        state["_next"] = "extract"
    else:
        # stop (no next)
        state["_next"] = None

    return state

# Register workflow's nodes mapping name -> callable
NODES = {
    "extract": extract_functions,
    "complexity": check_complexity,
    "issues": detect_issues,
    "suggest": suggest_improvements
}

# Edges define default linear progression
EDGES = {
    "extract": "complexity",
    "complexity": "issues",
    "issues": "suggest",
    "suggest": None
}

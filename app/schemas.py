# app/schemas.py
from pydantic import BaseModel
from typing import Dict, Any, Optional

class GraphCreateRequest(BaseModel):
    # mode: either "preset" like "code_review" OR provide nodes+edges
    preset: Optional[str] = None
    nodes: Optional[Dict[str, str]] = None  # name -> function_key (registered)
    edges: Optional[Dict[str, Optional[str]]] = None
    start_node: Optional[str] = None

class GraphCreateResponse(BaseModel):
    graph_id: str

class GraphRunRequest(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any]
    async_run: Optional[bool] = False  # if true, run in background (simple support)

class GraphRunResponse(BaseModel):
    run_id: str
    final_state: Dict[str, Any]
    log: list

class GraphStateResponse(BaseModel):
    run_id: str
    state: Dict[str, Any]
    log: list

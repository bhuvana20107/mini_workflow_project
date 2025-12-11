# app/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Dict, Any
import uuid
import asyncio

from engine.graph import Graph
from workflows import code_review
from app import schemas

app = FastAPI(title="Mini Workflow Engine")

# In-memory stores
GRAPHS: Dict[str, Graph] = {}
RUNS_STATE: Dict[str, Dict[str, Any]] = {}  # run_id -> state
RUNS_LOG: Dict[str, list] = {}  # run_id -> log

# Support mapping of available node functions across presets
AVAILABLE_NODE_FN = {}
# load code_review nodes
for k, v in code_review.NODES.items():
    AVAILABLE_NODE_FN[f"code_review.{k}"] = v

@app.post("/graph/create", response_model=schemas.GraphCreateResponse)
async def create_graph(req: schemas.GraphCreateRequest):
    """
    Create a graph. Two modes:
    - preset: "code_review" -> uses built-in sample workflow
    - nodes+edges: nodes is mapping name->fn_key where fn_key must be a registered key in AVAILABLE_NODE_FN
    """
    graph_id = str(uuid.uuid4())

    if req.preset:
        if req.preset == "code_review":
            nodes = {name: fn for name, fn in code_review.NODES.items()}
            edges = code_review.EDGES
            start_node = req.start_node or "extract"
            g = Graph(nodes=nodes, edges=edges, start_node=start_node)
            GRAPHS[graph_id] = g
            return {"graph_id": graph_id}
        else:
            raise HTTPException(status_code=400, detail="Unknown preset")
    else:
        if not req.nodes or not req.edges:
            raise HTTPException(status_code=400, detail="Provide either preset or nodes+edges")
        # resolve node functions
        resolved = {}
        for name, fn_key in req.nodes.items():
            fn = AVAILABLE_NODE_FN.get(fn_key)
            if not fn:
                raise HTTPException(status_code=400, detail=f"Unknown fn_key: {fn_key}")
            resolved[name] = fn
        g = Graph(nodes=resolved, edges=req.edges, start_node=req.start_node)
        GRAPHS[graph_id] = g
        return {"graph_id": graph_id}


def _persist_run_state(run_id: str, state: Dict[str, Any], log: list):
    RUNS_STATE[run_id] = dict(state)
    RUNS_LOG[run_id] = list(log)

async def _run_graph_and_persist(g: Graph, run_id: str, initial_state: Dict[str, Any]):
    result = await g.run(initial_state, run_id=run_id, run_state_callback=_persist_run_state)
    # store final
    RUNS_STATE[run_id] = result["state"]
    RUNS_LOG[run_id] = result["log"]
    return result

@app.post("/graph/run", response_model=schemas.GraphRunResponse)
async def run_graph(req: schemas.GraphRunRequest, background_tasks: BackgroundTasks):
    g = GRAPHS.get(req.graph_id)
    if not g:
        raise HTTPException(status_code=404, detail="Graph not found")

    run_id = str(uuid.uuid4())
    # initialize run state storage
    RUNS_STATE[run_id] = dict(req.initial_state)
    RUNS_LOG[run_id] = []

    if req.async_run:
        # schedule background run
        background_tasks.add_task(_run_graph_and_persist, g, run_id, req.initial_state)
        return {"run_id": run_id, "final_state": {}, "log": ["Run started in background"]}
    else:
        # run synchronously
        result = await _run_graph_and_persist(g, run_id, req.initial_state)
        return {"run_id": run_id, "final_state": result["state"], "log": result["log"]}

@app.get("/graph/state/{run_id}", response_model=schemas.GraphStateResponse)
async def get_state(run_id: str):
    state = RUNS_STATE.get(run_id)
    log = RUNS_LOG.get(run_id, [])
    if state is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "state": state, "log": log}

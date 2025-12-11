# Mini Workflow Engine (AI Engineering - Assignment)

This is a minimal workflow/agent engine with FastAPI endpoints.

## Structure
- `engine/graph.py` - core Graph class that runs nodes (supports branching & looping)
- `tools/registry.py` - simple tool registry (example tool `detect_smells`)
- `workflows/code_review.py` - sample Option A workflow (Code Review Mini-Agent)
- `app/` - FastAPI app & Pydantic schemas

## Requirements
```
pip install -r requirements.txt
```

## Run
```
uvicorn app.main:app --reload --port 8000
```

## APIs
### POST /graph/create
Create a graph. Two ways:
1. Preset: `{"preset":"code_review"}` to create the sample workflow.
2. Custom: supply `nodes` and `edges` where node values reference registered function keys (not covered in detail here).

Response: `{"graph_id":"..."}`

### POST /graph/run
Run a graph:
```
{
  "graph_id": "<graph_id>",
  "initial_state": {"code": "def foo():\n  pass", "threshold": 7},
  "async_run": false
}
```
If `async_run` is true, run executes in background and the response returns immediately with `run_id`.

### GET /graph/state/{run_id}
Get the current/last state and execution log for a run.

## Example (code-review preset)
1. Create:
```
curl -X POST "http://127.0.0.1:8000/graph/create" -H "Content-Type: application/json" -d '{"preset":"code_review"}'
```
2. Run:
```
curl -X POST "http://127.0.0.1:8000/graph/run" -H "Content-Type: application/json" -d '{
  "graph_id":"<paste_graph_id>",
  "initial_state": {"code":"def a():\n  pass\ndef b():\n  # TODO\n  print(1)", "threshold":7},
  "async_run": false
}'
```
3. Get state/log:
```
curl http://127.0.0.1:8000/graph/state/<run_id>
```

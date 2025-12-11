# engine/graph.py
from typing import Callable, Dict, Any, List, Optional
import asyncio
import uuid

class Graph:
    def __init__(self, nodes: Dict[str, Callable[[Dict[str, Any]], Any]], edges: Dict[str, str], start_node: Optional[str] = None):
        """
        nodes: mapping name -> function(state) -> (state OR dict with {"state":..., "next":...})
        edges: mapping node_name -> next_node_name (simple linear mapping)
        start_node: optional explicit start node
        """
        self.nodes = nodes
        self.edges = edges
        self.start_node = start_node or (next(iter(nodes)) if nodes else None)
        self.execution_log: List[str] = []

    async def _maybe_await(self, result):
        if asyncio.iscoroutine(result):
            return await result
        return result

    async def run(self, initial_state: Dict[str, Any], run_id: Optional[str] = None, run_state_callback: Optional[Callable]=None, max_steps: int = 1000):
        """
        Executes the graph starting from start_node.
        - initial_state is mutated and passed through nodes.
        - run_state_callback(run_id, state, log) can be used to stream or persist.
        Returns final state and execution log.
        """
        run_id = run_id or str(uuid.uuid4())
        state = dict(initial_state)
        self.execution_log = []
        current = self.start_node
        steps = 0

        while current:
            steps += 1
            if steps > max_steps:
                self.execution_log.append("Stopped: reached max steps limit")
                break

            node_fn = self.nodes.get(current)
            if node_fn is None:
                self.execution_log.append(f"Stopped: node '{current}' not found")
                break

            self.execution_log.append(f"Start node: {current}")
            maybe_result = node_fn(state)

            # allow node to be async or return dict containing next override
            result = await self._maybe_await(maybe_result)

            # node may return:
            # - None -> state mutated in place
            # - dict with {"state": {...}, "next": "node_name"} or {"next": ...}
            if isinstance(result, dict) and ("state" in result or "next" in result):
                if "state" in result:
                    state = result["state"]
                # next override from node
                next_node = result.get("next")
            else:
                # assume nodes mutated state or returned full state
                if isinstance(result, dict):
                    state = result
                next_node = None

            # allow node to set a "next_node" key in state itself (another convention)
            if not next_node:
                next_node = state.get("_next") or self.edges.get(current)

            self.execution_log.append(f"End node: {current} -> next: {next_node}")
            if run_state_callback:
                try:
                    run_state_callback(run_id, state, list(self.execution_log))
                except Exception:
                    # non-critical
                    pass

            # clear any one-time keys
            if "_next" in state:
                del state["_next"]

            # branching: if next_node is falsy, stop
            current = next_node

        return {"state": state, "log": list(self.execution_log), "run_id": run_id}

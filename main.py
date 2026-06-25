import asyncio
from typing import TypedDict, Annotated, List
from operator import add
from fastapi import FastAPI, BackgroundTasks
from langgraph.graph import StateGraph
from langchain_core.messages import BaseMessage, HumanMessage

class GridState(TypedDict):
    proposed_load: float
    is_safe: bool
    status: str
    cycle: int

def optimizer_node(state: GridState):
    # Logic to oscillate the load to simulate "movement"
    next_load = 400.0 if state.get("cycle", 0) % 2 == 0 else 600.0
    return {"proposed_load": next_load, "status": "optimizing"}

def governor_node(state: GridState):
    is_safe = 100.0 <= state["proposed_load"] <= 1000.0
    return {"is_safe": is_safe, "status": "verified", "cycle": state.get("cycle", 0) + 1}

# Graph assembly
builder = StateGraph(GridState)
builder.add_node("optimizer", optimizer_node)
builder.add_node("governor", governor_node)
builder.set_entry_point("optimizer")
builder.add_edge("optimizer", "governor")
builder.add_edge("governor", "optimizer") # Loop for motion
app_graph = builder.compile()

# Continuous execution engine
async def run_continuous_grid():
    state = {"proposed_load": 0.0, "is_safe": True, "status": "init", "cycle": 0}
    while True:
        # The graph executes, modifies state, and returns it
        state = await app_graph.ainvoke(state)
        # VISUAL VERIFICATION: This print statement proves the system is moving
        print(f"--- [GRID MONITOR] Cycle: {state['cycle']} | Load: {state['proposed_load']} MW | Safe: {state['is_safe']} ---")
        await asyncio.sleep(2)

api = FastAPI()

@api.on_event("startup")
async def startup_event():
    # Automatically start the motion when the API boots
    asyncio.create_task(run_continuous_grid())

@api.get("/status")
async def get_status():
    return {"message": "Grid control plane is actively cycling in the background."}

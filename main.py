import asyncio
from typing import Annotated, TypedDict, List
from operator import add
from fastapi import FastAPI, BackgroundTasks
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq

# 1. State
class GridState(TypedDict):
    messages: Annotated[List[BaseMessage], add]
    proposed_load: float
    is_safe: bool
    status: str
    tick_count: int

# 2. Nodes
def optimizer_node(state: GridState):
    # This node calculates the new load
    # In production, swap with your Groq LLM logic
    new_load = 450.0 
    return {"proposed_load": new_load, "status": "optimizing", "tick_count": state.get("tick_count", 0) + 1}

def governor_node(state: GridState):
    # This node validates the physics
    is_safe = 100.0 <= state["proposed_load"] <= 1000.0
    return {"is_safe": is_safe, "status": "verified" if is_safe else "blocked"}

# 3. Cyclic Graph
builder = StateGraph(GridState)
builder.add_node("optimizer", optimizer_node)
builder.add_node("governor", governor_node)
builder.set_entry_point("optimizer")
builder.add_edge("optimizer", "governor")
# FEEDBACK LOOP: The governor forces the graph to reconsider
builder.add_edge("governor", "optimizer") 

# Compile (Simplified for testing)
app_graph = builder.compile()

# 4. Continuous Engine
async def grid_engine(thread_id: str):
    state = {"messages": [], "proposed_load": 0.0, "tick_count": 0}
    while True:
        # EXECUTION: This force-runs the cycle continuously
        state = await app_graph.ainvoke(state)
        print(f"Cycle {state['tick_count']}: Load={state['proposed_load']}, Status={state['status']}")
        await asyncio.sleep(2) # Speed of the "motion"

api = FastAPI()

@api.post("/start")
async def start(bg: BackgroundTasks):
    bg.add_task(grid_engine, "thread-01")
    return {"status": "Engine Running"}

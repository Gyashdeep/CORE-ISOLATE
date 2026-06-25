import asyncio
import os
import uvicorn
from fastapi import FastAPI
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph
from langchain_groq import ChatGroq

# 1. State Definition
class GridState(TypedDict):
    proposed_load: float
    iteration: int

# 2. Logic Nodes
def optimizer_node(state: GridState):
    # This simulates the LLM optimization process
    # Replace with: ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    current_iter = state.get("iteration", 0) + 1
    new_load = 400.0 + (current_iter * 5)
    return {"proposed_load": new_load, "iteration": current_iter}

def governor_node(state: GridState):
    # Validation boundary
    return {"proposed_load": state["proposed_load"]}

# 3. Cyclic Graph (A -> B -> A)
builder = StateGraph(GridState)
builder.add_node("optimizer", optimizer_node)
builder.add_node("governor", governor_node)
builder.set_entry_point("optimizer")
builder.add_edge("optimizer", "governor")
builder.add_edge("governor", "optimizer") # This closes the loop
app_graph = builder.compile()

# 4. Independent "Motion" Engine
async def motion_engine():
    state = {"proposed_load": 400.0, "iteration": 0}
    while True:
        # Recursive state update
        state = await app_graph.ainvoke(state)
        print(f"SYSTEM MOTION: Iteration {state['iteration']} | Load: {state['proposed_load']} MW")
        await asyncio.sleep(2) # The "Heartbeat"

# 5. API Setup
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Launches the engine in the background immediately
    asyncio.create_task(motion_engine())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

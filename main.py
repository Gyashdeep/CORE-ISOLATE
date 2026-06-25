import asyncio
import logging
from typing import TypedDict, Annotated
from operator import add
from fastapi import FastAPI
from langgraph.graph import StateGraph
from langchain_groq import ChatGroq

# 1. State Definition
class GridState(TypedDict):
    proposed_load: float
    cycle: int

# 2. Logic Nodes
def optimizer_node(state: GridState):
    # This node acts as the "movement" generator
    next_cycle = state.get("cycle", 0) + 1
    # We change the value every cycle to prove it is moving
    return {"proposed_load": 400.0 + (next_cycle * 10), "cycle": next_cycle}

def governor_node(state: GridState):
    # Validation logic
    return {"proposed_load": state["proposed_load"]}

# 3. Graph Assembly (The infinite cycle)
builder = StateGraph(GridState)
builder.add_node("optimizer", optimizer_node)
builder.add_node("governor", governor_node)
builder.set_entry_point("optimizer")
builder.add_edge("optimizer", "governor")
builder.add_edge("governor", "optimizer") # Loop back to start
app_graph = builder.compile()

# 4. The "Movement" Engine
async def motion_engine():
    # Initial seed state
    state = {"proposed_load": 400.0, "cycle": 0}
    while True:
        # Re-invoke the graph manually to force progression
        state = await app_graph.ainvoke(state)
        # FORCE LOGGING TO TERMINAL
        print(f"MOTION DETECTED: Cycle {state['cycle']} | Current Load: {state['proposed_load']} MW")
        await asyncio.sleep(2)

# 5. FastAPI App
app = FastAPI()

@app.on_event("startup")
async def start_motion():
    # This fires immediately when the server starts
    asyncio.create_task(motion_engine())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

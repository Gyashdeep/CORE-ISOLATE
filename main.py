import asyncio
from typing import Annotated, TypedDict, List
from operator import add
from fastapi import FastAPI, BackgroundTasks
from langgraph.graph import StateGraph
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage

# 1. State Definition
class GridState(TypedDict):
    messages: Annotated[List[BaseMessage], add]
    proposed_load: float
    is_safe: bool
    status: str
    cycle: int

# 2. Physics & Logic Nodes
def optimizer_node(state: GridState):
    # Utilizing your requested model
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    # Simulate a calculation loop
    next_cycle = state.get("cycle", 0) + 1
    return {"proposed_load": 450.0 + (next_cycle % 10), "status": "optimizing", "cycle": next_cycle}

def governor_node(state: GridState):
    is_safe = 100.0 <= state["proposed_load"] <= 1000.0
    return {"is_safe": is_safe, "status": "verified" if is_safe else "blocked"}

# 3. Continuous Graph Construction
# We do NOT use END to ensure the loop remains active
builder = StateGraph(GridState)
builder.add_node("optimizer", optimizer_node)
builder.add_node("governor", governor_node)
builder.set_entry_point("optimizer")
builder.add_edge("optimizer", "governor")
builder.add_edge("governor", "optimizer") # THIS CREATES THE CONTINUOUS LOOP

app_graph = builder.compile()

# 4. Background Execution Engine
async def run_continuous_engine():
    # Initial state
    state = {"messages": [], "proposed_load": 450.0, "is_safe": True, "status": "start", "cycle": 0}
    while True:
        # Execution of the cyclic graph
        state = await app_graph.ainvoke(state)
        print(f"GRID MOTION: Cycle {state['cycle']} | Load: {state['proposed_load']} | Status: {state['status']}")
        await asyncio.sleep(2) # Sets the speed of the "motion"

# 5. API Setup
api = FastAPI(title="AETHER-GOV Continuous Control Plane")

@api.on_event("startup")
async def startup():
    # Automatically triggers the background loop on server launch
    asyncio.create_task(run_continuous_engine())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)

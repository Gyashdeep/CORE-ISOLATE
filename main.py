import os
import uvicorn
from typing import Annotated, TypedDict, List, Literal
from operator import add
from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage

# 1. State Definition
class GridState(TypedDict):
    messages: Annotated[List[BaseMessage], add]
    proposed_load: float
    is_safe: bool
    status: str
    iteration: int

# 2. Physics Kernel
def physics_governor(proposed_load: float) -> bool:
    return 100.0 <= proposed_load <= 1000.0

# 3. Nodes
def optimizer_agent(state: GridState):
    # Logic to optimize load based on history
    return {"proposed_load": 450.0, "status": "optimized", "iteration": state.get("iteration", 0) + 1}

def adversary_node(state: GridState):
    # Simulated instability
    return {"proposed_load": 5000.0, "status": "adversarial_attack"}

def governor_node(state: GridState):
    is_safe = physics_governor(state["proposed_load"])
    return {"is_safe": is_safe, "status": "verified" if is_safe else "blocked"}

# 4. Continuous Routing Logic
def router(state: GridState) -> Literal["optimizer", "adversary", "end_process"]:
    if state.get("iteration", 0) > 10: # Termination condition
        return "end_process"
    if not state.get("is_safe", True):
        return "optimizer" # Re-loop to fix
    return "adversary" # Proceed to test next load

# 5. Graph Assembly
builder = StateGraph(GridState)
builder.add_node("optimizer", optimizer_agent)
builder.add_node("adversary", adversary_node)
builder.add_node("governor", governor_node)

builder.set_entry_point("optimizer")
builder.add_edge("optimizer", "governor")
builder.add_edge("adversary", "governor")

builder.add_conditional_edges("governor", router, {
    "optimizer": "optimizer",
    "adversary": "adversary",
    "end_process": END
})

# Compile with persistence
DB_URI = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/grid_db")
pool = ConnectionPool(conninfo=DB_URI)
checkpointer = PostgresSaver(pool)
app_graph = builder.compile(checkpointer=checkpointer)

# 6. API Endpoint
api = FastAPI(title="AETHER-GOV Continuous Plane")

@api.post("/run-cycle")
async def run_cycle(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    # Trigger the recursive execution
    result = app_graph.invoke({"iteration": 0}, config=config)
    return result

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)

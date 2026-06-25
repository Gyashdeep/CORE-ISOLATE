import os
import asyncio
from typing import Annotated, TypedDict, List
from operator import add
from fastapi import FastAPI, BackgroundTasks
from langgraph.graph import StateGraph
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

# 2. Physics Kernel
def physics_governor(proposed_load: float) -> bool:
    return 100.0 <= proposed_load <= 1000.0

# 3. Agent Nodes
def optimizer_agent(state: GridState):
    # Utilizing specified model
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    # Logic: Propose a load based on state (simplified for demo)
    return {"proposed_load": 450.0, "status": "optimized"}

def governor_node(state: GridState):
    is_safe = physics_governor(state["proposed_load"])
    return {"is_safe": is_safe, "status": "verified" if is_safe else "blocked"}

# 4. Graph Construction (The Infinite Loop)
builder = StateGraph(GridState)
builder.add_node("optimizer", optimizer_agent)
builder.add_node("governor", governor_node)
builder.set_entry_point("optimizer")
builder.add_edge("optimizer", "governor")
# Feedback loop: The governor sends it back to the start
builder.add_edge("governor", "optimizer")

# Persistence
DB_URI = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/grid_db")
pool = ConnectionPool(conninfo=DB_URI)
app_graph = builder.compile(checkpointer=PostgresSaver(pool))

# 5. Continuous Execution Engine
async def grid_loop(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    while True:
        # The graph keeps running and updating the checkpointed state
        await app_graph.ainvoke({"messages": [HumanMessage(content="tick")]}, config=config)
        await asyncio.sleep(2) # Frequency of the control loop

api = FastAPI(title="CORE-ISOLATE Continuous Control Plane")

@api.post("/start-grid")
async def start_grid(thread_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(grid_loop, thread_id)
    return {"status": "Grid control initiated", "thread": thread_id}

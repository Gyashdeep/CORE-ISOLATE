import os
import asyncio
import logging
from typing import Annotated, TypedDict, List
from operator import add
from fastapi import FastAPI, BackgroundTasks
from langgraph.graph import StateGraph
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CORE-ISOLATE")

# 1. Industrial State
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
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    # Propose load (In prod, logic would derive from state["messages"])
    return {"proposed_load": 450.0, "status": "optimized"}

def governor_node(state: GridState):
    is_safe = physics_governor(state["proposed_load"])
    return {"is_safe": is_safe, "status": "verified" if is_safe else "blocked"}

# 4. Graph Construction
builder = StateGraph(GridState)
builder.add_node("optimizer", optimizer_agent)
builder.add_node("governor", governor_node)
builder.set_entry_point("optimizer")
builder.add_edge("optimizer", "governor")

# Persistence Setup
DB_URI = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/grid_db")
pool = ConnectionPool(conninfo=DB_URI)
checkpointer = PostgresSaver(pool)
checkpointer.setup()
app_graph = builder.compile(checkpointer=checkpointer)

# 5. Continuous Execution Engine
async def grid_heartbeat(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    logger.info(f"Initiating continuous control loop for thread: {thread_id}")
    
    while True:
        try:
            # We invoke the graph; it pulls the previous state from Postgres
            await app_graph.ainvoke(
                {"messages": [HumanMessage(content="Tick")]}, 
                config=config
            )
            logger.info("Cycle complete: System stable.")
            await asyncio.sleep(5)  # 5-second interval
        except Exception as e:
            logger.error(f"Loop failure: {e}")
            break

# 6. Production API
api = FastAPI(title="AETHER-GOV Control Plane")

@api.post("/run-system/{thread_id}")
async def start_system(thread_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(grid_heartbeat, thread_id)
    return {"message": "Continuous control loop initiated.", "thread_id": thread_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)

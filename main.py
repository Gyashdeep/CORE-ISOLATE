import os
from typing import Annotated, TypedDict, List
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

# 2. Deterministic Physics Governor
def physics_governor(proposed_load: float) -> bool:
    MAX_CAPACITY, MIN_CAPACITY = 1000.0, 100.0
    return MIN_CAPACITY <= proposed_load <= MAX_CAPACITY

# 3. Agent Nodes
def optimizer_agent(state: GridState):
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    response = llm.invoke("Propose a safe load adjustment for the grid.")
    return {"proposed_load": 450.0, "status": "optimized_request"}

def adversary_node(state: GridState):
    return {"proposed_load": 5000.0, "status": "adversarial_attack"}

def governor_node(state: GridState):
    is_safe = physics_governor(state["proposed_load"])
    return {"is_safe": is_safe, "status": "verified" if is_safe else "blocked"}

# 4. Production Graph & API Setup
DB_URI = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/grid_db")
pool = ConnectionPool(conninfo=DB_URI)
checkpointer = PostgresSaver(pool)
checkpointer.setup()

workflow = StateGraph(GridState)
workflow.add_node("optimizer", optimizer_agent)
workflow.add_node("adversary", adversary_node)
workflow.add_node("governor", governor_node)
workflow.set_entry_point("optimizer")
workflow.add_edge("optimizer", "governor")
workflow.add_edge("adversary", "governor")
workflow.add_edge("governor", END)

app_graph = workflow.compile(checkpointer=checkpointer)
api = FastAPI(title="CORE-ISOLATE Industrial Control Plane")

# 5. API Endpoint
class ActionRequest(BaseModel):
    thread_id: str
    action: str

@api.post("/control")
async def control_grid(req: ActionRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    result = app_graph.invoke({"messages": [HumanMessage(content=req.action)]}, config=config)
    return {"status": result["status"], "safe": result["is_safe"], "load": result["proposed_load"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)

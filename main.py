import os
from typing import Annotated, TypedDict, List
from operator import add
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage

# 1. State Definition: The "Shared Memory"
class GridState(TypedDict):
    messages: Annotated[List[BaseMessage], add]
    proposed_load: float
    is_safe: bool
    status: str

# 2. The Deterministic Physics Governor (The "Governor Kernel")
def physics_governor(proposed_load: float) -> bool:
    """Physics-constrained safety barrier."""
    MAX_CAPACITY = 1000.0
    MIN_CAPACITY = 100.0
    return MIN_CAPACITY <= proposed_load <= MAX_CAPACITY

# 3. Agents
def optimizer_agent(state: GridState):
    # GPT-OSS 120B for complex orchestration
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    response = llm.invoke("Propose a load adjustment for the grid.")
    return {"proposed_load": 450.0, "status": "optimized_request"}

def adversary_node(state: GridState):
    # Stress-tester node
    return {"proposed_load": 5000.0, "status": "adversarial_attack"}

def governor_node(state: GridState):
    is_safe = physics_governor(state["proposed_load"])
    return {"is_safe": is_safe, "status": "verified" if is_safe else "blocked"}

# 4. Production Graph Configuration
DB_URI = os.getenv("DATABASE_URL") # e.g., "postgresql://user:pass@localhost:5432/grid_db"
with ConnectionPool(conninfo=DB_URI) as pool:
    checkpointer = PostgresSaver(pool)
    checkpointer.setup() # Initialize the state tables

    workflow = StateGraph(GridState)
    workflow.add_node("optimizer", optimizer_agent)
    workflow.add_node("adversary", adversary_node)
    workflow.add_node("governor", governor_node)

    # Branching logic: Both agents report to the Governor
    workflow.set_entry_point("optimizer")
    workflow.add_edge("optimizer", "governor")
    workflow.add_edge("adversary", "governor")
    workflow.add_edge("governor", END)

    app = workflow.compile(checkpointer=checkpointer)

# 5. Execution with Persistence
config = {"configurable": {"thread_id": "industrial_grid_001"}}
final_state = app.invoke({"messages": [HumanMessage(content="Initialize")]}, config=config)
print(f"Status: {final_state['status']} | Safety Approved: {final_state['is_safe']}")

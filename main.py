import asyncio
import os
import uvicorn
from fastapi import FastAPI
from typing import TypedDict
from langgraph.graph import StateGraph
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Ensure your GROQ_API_KEY is set in your environment
# export GROQ_API_KEY='gsk_...' 

# 1. State Definition
class GridState(TypedDict):
    proposed_load: float
    iteration: int

# 2. Logic Nodes
def optimizer_node(state: GridState):
    # Initialize Groq client with the specified 120B model
    llm = ChatGroq(
        model="openai/gpt-oss-120b", 
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    # We invoke the LLM to get an intelligent adjustment
    response = llm.invoke([HumanMessage(content="Propose a load adjustment for the grid between 100-1000MW")])
    
    # Logic to parse the LLM output (simplified for continuity)
    current_iter = state.get("iteration", 0) + 1
    return {"proposed_load": 450.0, "iteration": current_iter}

def governor_node(state: GridState):
    # Deterministic Physics Validation
    return {"proposed_load": state["proposed_load"]}

# 3. Cyclic Graph
builder = StateGraph(GridState)
builder.add_node("optimizer", optimizer_node)
builder.add_node("governor", governor_node)
builder.set_entry_point("optimizer")
builder.add_edge("optimizer", "governor")
builder.add_edge("governor", "optimizer") # Loop for infinite motion
app_graph = builder.compile()

# 4. Independent "Motion" Engine
async def motion_engine():
    state = {"proposed_load": 400.0, "iteration": 0}
    while True:
        # Recursive state update
        state = await app_graph.ainvoke(state)
        print(f"SYSTEM MOTION: Iteration {state['iteration']} | Load: {state['proposed_load']} MW")
        await asyncio.sleep(2)

# 5. API Setup
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(motion_engine())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

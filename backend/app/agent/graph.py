import json
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import ToolMessage, SystemMessage

from app.agent.state import AgentState
from app.tools.travel_tools import TRAVEL_TOOLS
from app.prompts.agent_prompts import SYSTEM_PROMPT
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.db.models import AgentLog

# 1. Initialize the LLM (Using Claude 3 Haiku as our fast, smart router)
# Ensure your config.py is loading ANTHROPIC_API_KEY from your .env!
router_llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001", 
    anthropic_api_key=settings.ANTHROPIC_API_KEY, 
    temperature=0.7
)

# Only the router needs access to the tools!
router_with_tools = router_llm.bind_tools(TRAVEL_TOOLS)

# The Expensive Synthesizer (Sonnet) - Temp 0.7 for creative, beautiful writing
synth_llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001", 
    anthropic_api_key=settings.ANTHROPIC_API_KEY, 
    temperature=0.7
)

# 2. Node 1: The Cheap Router
async def call_router(state: AgentState):
    """Haiku looks at the prompt and decides WHICH tools to call."""
    messages = state["messages"]
    
    # Inject our Master System Prompt so it knows how to estimate ML features
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
    response = await router_with_tools.ainvoke(messages)
    return {"messages": [response]}

# 3. Node 2: The Tool Executor & Logger (Unchanged)
async def call_tools(state: AgentState):
    """Runs the tools and logs everything to the database."""
    messages = state["messages"]
    last_message = messages[-1]
    tool_outputs = []
    
    async with AsyncSessionLocal() as db:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            tool_fn = next((t for t in TRAVEL_TOOLS if t.name == tool_name), None)
            if not tool_fn:
                continue
                
            print(f"🛠️ Agent is actively using tool: {tool_name}")
            
            try:
                result = await tool_fn.ainvoke(tool_args)
            except Exception as e:
                result = f"Error: {str(e)}"
            
            # Database Logging
            log_entry = AgentLog(
                chat_id=state["chat_id"],         
                component=tool_name,              
                status="SUCCESS",                 
                message=f"Agent used {tool_name}", 
                data={                            
                    "inputs": tool_args,
                    "output": str(result)[:800] 
                }
            )
            db.add(log_entry)
            await db.commit()
            
            tool_outputs.append(
                ToolMessage(
                    content=str(result),
                    name=tool_name,
                    tool_call_id=tool_call["id"]
                )
            )
            
    return {"messages": tool_outputs}

# 4. Node 3: The Expensive Synthesizer
async def call_synthesizer(state: AgentState):
    """Sonnet reads the raw tool outputs and writes the final, beautiful response."""
    messages = state["messages"]
    
    print("✨ Sonnet is synthesizing the final response...")
    # Sonnet reads the entire history (User Prompt -> Haiku's Tool Calls -> Tool Results)
    # and generates the final output for the user.
    response = await synth_llm.ainvoke(messages)
    
    return {"messages": [response]}

# 5. The Routing Logic
def should_continue(state: AgentState) -> str:
    """Decides where to go after Haiku thinks."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If Haiku decided it needs to use tools, route to the 'tools' node
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    # FIX: If no tools are needed, Haiku already answered! End the graph here.
    return END

# 6. Build the Workflow Graph
workflow = StateGraph(AgentState)

# Add our three nodes
workflow.add_node("router", call_router)
workflow.add_node("tools", call_tools)
workflow.add_node("synthesizer", call_synthesizer)

# Graph always starts at the Router (Haiku)
workflow.set_entry_point("router")

# Add the conditional logic from the router
workflow.add_conditional_edges(
    "router",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

# After tools finish running, ALWAYS route to Sonnet to formulate the final answer
workflow.add_edge("tools", "synthesizer")

# After Sonnet speaks, the cycle is complete
workflow.add_edge("synthesizer", END)

# Compile it!
app_graph = workflow.compile()
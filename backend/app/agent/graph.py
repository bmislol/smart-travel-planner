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
llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001", 
    anthropic_api_key=settings.ANTHROPIC_API_KEY, 
    temperature=0.7
)

# Give the LLM access to the tools
llm_with_tools = llm.bind_tools(TRAVEL_TOOLS)

# 2. Node 1: The LLM Thinker
async def call_model(state: AgentState):
    """This node gives the messages to the LLM and gets its response."""
    messages = state["messages"]
    
    # If this is the very first message, inject our Master System Prompt
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
    response = await llm_with_tools.ainvoke(messages)
    
    # LangGraph automatically appends this response to the state
    return {"messages": [response]}

# 3. Node 2: The Tool Executor & Logger
async def call_tools(state: AgentState):
    """This node runs the tools and logs everything to the database."""
    messages = state["messages"]
    last_message = messages[-1] # This contains the tool requests from the LLM
    user_id = state["user_id"]
    
    tool_outputs = []
    
    # Open a fast database session just for logging
    async with AsyncSessionLocal() as db:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Find the actual Python function from our tools list
            tool_fn = next((t for t in TRAVEL_TOOLS if t.name == tool_name), None)
            if not tool_fn:
                continue
                
            print(f"🛠️ Agent is actively using tool: {tool_name}")
            
            # Execute the tool asynchronously
            try:
                result = await tool_fn.ainvoke(tool_args)
            except Exception as e:
                result = f"Error: {str(e)}"
            
            # --- DATABASE LOGGING HAPPENS HERE ---
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
            
            # Package the result so the LLM knows what happened
            tool_outputs.append(
                ToolMessage(
                    content=str(result),
                    name=tool_name,
                    tool_call_id=tool_call["id"]
                )
            )
            
    return {"messages": tool_outputs}

# 4. The Router (Conditional Edge)
def should_continue(state: AgentState) -> str:
    """Decides if we need to run tools, or if the LLM is finished."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM requested to use a tool, route to the 'tools' node
    if last_message.tool_calls:
        return "tools"
    
    # Otherwise, it's just chatting, so we end the graph
    return END

# 5. Build the Workflow Graph
workflow = StateGraph(AgentState)

# Add our two nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tools)

# The graph always starts at the agent node
workflow.set_entry_point("agent")

# Add the conditional logic from the agent node
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

# After a tool finishes running, ALWAYS go back to the agent so it can synthesize the data!
workflow.add_edge("tools", "agent")

# Compile it into a usable application
app_graph = workflow.compile()
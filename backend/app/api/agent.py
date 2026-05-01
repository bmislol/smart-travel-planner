from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db 
from app.db.models import User, Chat 
from app.agent.graph import app_graph

router = APIRouter()

# Schema for the incoming user message
class ChatRequest(BaseModel):
    message: str

# Schema for the agent's response
class ChatResponse(BaseModel):
    reply: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    current_user: User = Depends(get_current_user), # 🔒 SECURED: Requires JWT Token!
    db: AsyncSession = Depends(get_db)
):
    """
    Sends a message to the LangGraph Travel Agent.
    Requires a valid JWT token in the Authorization header.
    """
    try:
        # 1. Create a Chat session in the database first!
        new_chat = Chat(
            user_id=current_user.id, 
            title=request.message[:50] # Use the first 50 chars of the prompt as the title
        )
        db.add(new_chat)
        await db.commit()
        await db.refresh(new_chat)

        # 2. Prepare the initial state for the Graph, passing the new chat_id
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": current_user.id, # Injected directly from the Auth dependency
            "chat_id": new_chat.id
        }
        
        # 2. Run the graph (this triggers the LLM, the routing, and the tools)
        print(f"🧠 Running Agent Graph for user: {current_user.username}")
        final_state = await app_graph.ainvoke(initial_state)
        
        # 3. Extract the final AI message from the state
        messages = final_state.get("messages", [])
        if not messages:
            raise ValueError("Agent returned an empty state.")
            
        final_ai_message = messages[-1].content
        
        return ChatResponse(reply=final_ai_message)

    except Exception as e:
        print(f"❌ Agent Error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent encountered an error: {str(e)}")
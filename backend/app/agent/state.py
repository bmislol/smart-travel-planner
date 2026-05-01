from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
import uuid

class AgentState(TypedDict):
    """
    The state of our LangGraph agent. 
    This dictionary is passed from node to node during execution.
    """
    # The 'add_messages' annotation is the magic of LangGraph. 
    # It tells the graph to APPEND new messages to the list, rather than overwriting it.
    messages: Annotated[list[AnyMessage], add_messages]
    
    # We store the user_id in the state so our tool nodes know WHO is making the request.
    # This is crucial for logging actions to the AgentLog table!
    user_id: uuid.UUID
    chat_id: uuid.UUID
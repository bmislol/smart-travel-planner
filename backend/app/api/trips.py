from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.rag_service import RAGService
from app.services.weather_service import WeatherService
# We will inject these via the main app later
from app.main import get_rag_service, get_weather_service 

router = APIRouter(prefix="/agent", tags=["Agent"])

@router.post("/plan")
async def plan_trip(
    query: str,
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
    weather_service: WeatherService = Depends(get_weather_service)
):
    """
    The main entry point for the travel agent.
    """
    # 1. Use RAG Service to find destinations
    destinations = await rag_service.retrieve_relevant_destinations(db, query)
    
    if not destinations:
        return {"answer": "I couldn't find any destinations matching your request."}

    # 2. For the top destination, get live weather
    top_city = destinations[0].name
    weather = await weather_service.get_weather(top_city)

    # 3. (Future) This is where the LangGraph agent will synthesize the final answer
    return {
        "recommended_city": top_city,
        "vibe": destinations[0].travel_style,
        "current_weather": weather,
        "rationale": destinations[0].description
    }
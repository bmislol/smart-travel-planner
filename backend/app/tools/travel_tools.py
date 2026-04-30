from langchain_core.tools import tool
from typing import List, Dict, Any
from app.services.weather_service import weather_service
from app.services.classifier_service import classifier_service
from app.schemas.ml import DestinationFeatures
from app.db.session import AsyncSessionLocal
from app.services.embedder import embedder
from sqlalchemy import text
import json

@tool
async def get_live_weather(city: str) -> str:
    """
    Fetches the current live weather conditions for a specific city.
    Always use this tool when a user asks about the current weather, temperature, or conditions.
    """
    try:
        response = await weather_service.get_current_weather(city)
        return response.to_agent_string()
    except Exception as e:
        return f"Error fetching weather for {city}: {str(e)}"

@tool
async def classify_travel_style(
    country: str,
    lat: float,
    lng: float,
    Primary_Activity: str,
    Trip_Pace: str,
    Cost_of_Living_Index: float,
    Tourist_Cost_Score: float,
    Dining_Out_Premium: float,
    City_Scale: str
) -> str:
    """
    Predicts the ideal 'Travel Style' (e.g., Culture, Adventure, Budget) for a destination based on its features.
    Use this tool when you need to categorize a city or activity into a specific travel vibe.
    """
    try:
        features = DestinationFeatures(
            country=country,
            lat=lat,
            lng=lng,
            Primary_Activity=Primary_Activity,
            Trip_Pace=Trip_Pace,
            Cost_of_Living_Index=Cost_of_Living_Index,
            Tourist_Cost_Score=Tourist_Cost_Score,
            Dining_Out_Premium=Dining_Out_Premium,
            City_Scale=City_Scale
        )
        style = await classifier_service.predict_style(features)
        return f"The predicted travel style for this destination is: {style}"
    except Exception as e:
        return f"Error predicting travel style: {str(e)}"

@tool
async def search_destinations(query: str, limit: int = 3) -> str:
    """
    Searches the travel knowledge database for destinations matching a user's request.
    Use this tool when a user asks for recommendations, historical sites, food spots, or specific types of places in a country/city.
    """
    try:
        # 1. Embed the user's query
        query_embedding = embedder.embed_text(query)
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        # 2. Search the database using pgvector
        async with AsyncSessionLocal() as db:
            sql = text("""
                SELECT c.destination_id, c.content, d.name, d.travel_style
                FROM destination_chunks c
                JOIN destinations d ON c.destination_id = d.id
                ORDER BY c.embedding <=> :embedding
                LIMIT :limit
            """)
            result = await db.execute(sql, {"embedding": embedding_str, "limit": limit})
            rows = result.fetchall()
            
            if not rows:
                return "No matching destinations found in the database."
                
            # 3. Format the results for the LLM
            formatted_results = []
            for row in rows:
                formatted_results.append(f"Destination: {row.name} (Style: {row.travel_style})\nDetails: {row.content}\n")
                
            return "\n---\n".join(formatted_results)
            
    except Exception as e:
        return f"Error searching destinations: {str(e)}"

# We export a list of all tools so the agent can easily grab them
TRAVEL_TOOLS = [get_live_weather, classify_travel_style, search_destinations]
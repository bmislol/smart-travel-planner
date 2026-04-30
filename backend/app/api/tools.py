from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.services.rag_service import RAGService
from app.services.weather_service import WeatherService
from app.services.classifier_service import MLClassifierService
from app.schemas.weather import WeatherResponse
# These dependency helpers will be defined in your main.py lifespan
from app.main import get_rag_service, get_weather_service, get_ml_service

router = APIRouter(prefix="/tools", tags=["Tool Testing"])

@router.get("/test-rag", response_model=List[dict])
async def test_rag(
    query: str = Query(..., description="The search term for RAG"),
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Directly test the pgvector search logic."""
    results = await rag_service.retrieve_relevant_destinations(db, query)
    return [
        {"name": d.name, "vibe": d.travel_style, "description": d.description} 
        for d in results
    ]

@router.get("/test-weather", response_model=WeatherResponse)
async def test_weather(
    city: str = Query(..., description="City name"),
    weather_service: WeatherService = Depends(get_weather_service)
):
    """Directly test the OpenWeatherMap integration and TTL cache."""
    return await weather_service.get_weather(city)

@router.post("/test-classifier")
async def test_classifier(
    features: dict,
    ml_service: MLClassifierService = Depends(get_ml_service)
):
    """Directly test the scikit-learn joblib model prediction."""
    style = await ml_service.predict_style(features)
    return {"predicted_travel_style": style}
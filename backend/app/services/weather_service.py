import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Optional

from app.core.config import settings
from app.schemas.weather import WeatherResponse

class WeatherService:
    def __init__(self):
        self.api_key = settings.WEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.client: Optional[httpx.AsyncClient] = None # Will be initialized in main.py

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_current_weather(self, city: str) -> WeatherResponse:
        """Fetches live weather, retries on failure, and validates through Pydantic."""
        if not self.api_key or "your" in self.api_key.lower():
            raise ValueError(f"Cannot fetch weather for {city}: API Key not configured in .env.")
            
        if self.client is None:
            raise RuntimeError("HTTP Client not initialized. Check lifespan startup.")

        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric"
        }
        
        response = await self.client.get(self.base_url, params=params, timeout=10.0)
        response.raise_for_status() 
        data = response.json()

        # Pydantic is our fence! Validate the incoming JSON immediately.
        return WeatherResponse(
            city=city,
            description=data["weather"][0]["description"].capitalize(),
            temperature_c=data["main"]["temp"],
            feels_like_c=data["main"]["feels_like"]
        )

# The Singleton Instance
weather_service = WeatherService()
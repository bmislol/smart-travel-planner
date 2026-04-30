import httpx
from aiocache import cached
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.schemas.weather import WeatherResponse

class WeatherService:
    def __init__(self):
        self.api_key = settings.WEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    @cached(ttl=600)  # TTL Cache: 10 minutes (600 seconds)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_weather(self, city: str) -> WeatherResponse:
        """
        Fetch live weather. Non-blocking, resilient, and cached.
        """
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params, timeout=10.0)
            
            if response.status_code != 200:
                # Log failure with structure as required by the brief
                raise Exception(f"Weather API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            return WeatherResponse(
                city=data["name"],
                temperature=data["main"]["temp"],
                description=data["weather"][0]["description"],
                humidity=data["main"]["humidity"],
                wind_speed=data["wind"]["speed"]
            )
from pydantic import BaseModel, Field

class WeatherRequest(BaseModel):
    """Schema for validating LLM/Agent inputs to the weather tool."""
    city: str = Field(..., description="The name of the city to get weather for.")

class WeatherResponse(BaseModel):
    """Schema for structured weather output returned to the agent."""
    city: str
    temperature: float
    description: str
    humidity: int
    wind_speed: float
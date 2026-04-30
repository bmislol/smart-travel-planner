from pydantic import BaseModel, Field

class WeatherResponse(BaseModel):
    city: str = Field(description="The name of the city.")
    description: str = Field(description="A brief description of the weather (e.g., Broken clouds).")
    temperature_c: float = Field(description="Current temperature in Celsius.")
    feels_like_c: float = Field(description="Feels-like temperature in Celsius.")
    
    def to_agent_string(self) -> str:
        """Helper method to format the data into a clean string for the LLM context."""
        return f"Current live weather in {self.city}: {self.description}, {self.temperature_c}°C (Feels like {self.feels_like_c}°C)."
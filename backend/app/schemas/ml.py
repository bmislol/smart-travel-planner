from pydantic import BaseModel, Field, ConfigDict

class DestinationFeatures(BaseModel):
    # This allows us to use either the Python variable name OR the alias when creating the object!
    model_config = ConfigDict(populate_by_name=True)

    country: str = Field(description="The country where the city is located.")
    lat: float = Field(description="Latitude of the city.")
    lng: float = Field(description="Longitude of the city.")
    Primary_Activity: str = Field(description="A short description of the main tourist activity.")
    Trip_Pace: str = Field(description="Pace of the trip (e.g., Fast, Moderate, Relaxed).")
    Cost_of_Living_Index: float = Field(alias="Cost of Living Index", description="Cost of living index score.")
    Tourist_Cost_Score: float = Field(description="Score indicating tourist expense.")
    Dining_Out_Premium: float = Field(description="Premium cost for dining out.")
    City_Scale: str = Field(description="Scale of the city (e.g., Megacity, Large City, Medium City).")
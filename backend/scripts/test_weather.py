import sys
import os
import asyncio
import httpx

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BACKEND_DIR)

from app.services.weather_service import weather_service

async def test_weather():
    print("Testing Live Weather API...")
    
    # Manually start the client for the test script
    weather_service.client = httpx.AsyncClient()
    
    try:
        # Pydantic returns a clean Python object
        result = await weather_service.get_current_weather("Tokyo")
        
        print("\n--- Raw Pydantic Object ---")
        print(result)
        
        print("\n--- Formatted for LLM Agent ---")
        print(result.to_agent_string())
        
    except Exception as e:
        print(f"\n[!] Weather API failed: {e}")
    finally:
        # Cleanly close the client
        await weather_service.client.aclose()

if __name__ == "__main__":
    asyncio.run(test_weather())
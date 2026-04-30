import sys
import os
import asyncio

# 1. ALWAYS set the path first!
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BACKEND_DIR)

# 2. Now Python knows where 'app' is, so we can import everything
from app.services.classifier_service import classifier_service
from app.schemas.ml import DestinationFeatures

async def test_ml():
    print("Loading ML Model...")
    classifier_service.load_model()
    
    # Mock data for Tokyo
    test_data = DestinationFeatures(
        country="Japan",
        lat=35.687,
        lng=139.7495,
        Primary_Activity="Tea ceremony experience in traditional Asakusa district",
        Trip_Pace="Relaxed",
        Cost_of_Living_Index=85.61,
        Tourist_Cost_Score=68.935,
        Dining_Out_Premium=0.55,
        City_Scale="Megacity"
    )
    
    print("\nPredicting Travel Style for Tokyo Tea Ceremony...")
    result = await classifier_service.predict_style(test_data)
    print(f"Prediction: {result}") # Should print 'Culture'

if __name__ == "__main__":
    asyncio.run(test_ml())
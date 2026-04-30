import joblib
from anyio import to_thread
from typing import List, Any
import pandas as pd
from app.core.config import settings

class MLClassifierService:
    def __init__(self, model_path: str):
        # 1. Load the model once during initialization (Singleton)
        # This will be called in the Lifespan handler on startup
        try:
            self.model = joblib.load(model_path)
            print(f"✅ ML Classifier loaded from {model_path}")
        except Exception as e:
            print(f"⚠️ Warning: Could not load ML model at {model_path}: {e}")
            self.model = None

    async def predict_style(self, features: dict) -> str:
        """
        Predicts travel style (Adventure, Relaxation, etc.) based on features.
        Wrapped in a thread to remain non-blocking.
        """
        if not self.model:
            return "Unknown (Model not loaded)"

        # Convert the dictionary of features into a DataFrame (scikit-learn requirement)
        input_df = pd.DataFrame([features])
        
        # Run prediction in a separate thread to avoid blocking the event loop
        prediction = await to_thread.run_sync(self._run_prediction, input_df)
        return prediction[0]

    def _run_prediction(self, df: pd.DataFrame) -> Any:
        # Standard scikit-learn predict call
        return self.model.predict(df)
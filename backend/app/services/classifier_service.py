import os
import joblib
import pandas as pd
from anyio import to_thread
from typing import Optional

from app.core.config import settings
from app.schemas.ml import DestinationFeatures

class TravelStyleClassifier:
    def __init__(self):
        self.model = None

    def load_model(self):
        """Loads the scikit-learn pipeline into memory. Called once at startup."""
        if self.model is None:
            # We use the absolute path to ensure it finds the joblib file
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))            
            project_root = os.path.dirname(backend_dir)
            model_path = os.path.join(project_root, "data", "ml", "travel_style_classifier.joblib")
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Classifier model not found at {model_path}")
            
            self.model = joblib.load(model_path)

    async def predict_style(self, features: DestinationFeatures) -> str:
        """
        Takes validated Pydantic features, converts to DataFrame, and predicts.
        Runs in a separate thread to ensure FastAPI's event loop isn't blocked.
        """
        if self.model is None:
            raise RuntimeError("Classifier model is not loaded. Check lifespan startup.")

        # Convert the Pydantic model to a dictionary, respecting the alias for 'Cost of Living Index'
        data_dict = features.model_dump(by_alias=True)
        
        # Wrap the dictionary in a list so Pandas creates a 1-row DataFrame
        df = pd.DataFrame([data_dict])
        
        # Run the synchronous CPU-bound predict function in a thread worker
        prediction = await to_thread.run_sync(self.model.predict, df)
        
        # Return the string label (e.g., "Culture", "Adventure")
        return prediction[0]

# The Singleton Instance
classifier_service = TravelStyleClassifier()
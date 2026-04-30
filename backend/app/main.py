from fastapi import FastAPI
from contextlib import asynccontextmanager

# Import our singletons
from app.services.embedder import embedder
from app.services.classifier_service import classifier_service
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    print("Loading all-mpnet-base-v2 into GPU VRAM...")
    embedder.load_model()
    print("Embedding model ready.")

    print("Loading ML Classifier into memory...")
    classifier_service.load_model() # <-- NEW
    print("ML Classifier ready.")

    yield # The application handles requests while yielding here

    # --- SHUTDOWN ---
    print("Shutting down Smart Travel Planner...")
    await engine.dispose() # Cleanly close DB connections

app = FastAPI(lifespan=lifespan, title="Smart Travel Planner API")

@app.get("/")
async def health_check():
    return {"status": "online", "message": "Smart Travel Planner is running."}
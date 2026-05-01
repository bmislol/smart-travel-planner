from fastapi import FastAPI
from contextlib import asynccontextmanager
import httpx

# Import our singletons
from app.services.embedder import embedder
from app.services.classifier_service import classifier_service
from app.services.weather_service import weather_service
from app.db.session import engine

from app.api import auth, agent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    print("Loading all-mpnet-base-v2 into GPU VRAM...")
    embedder.load_model()
    print("Embedding model ready.")

    print("Loading ML Classifier into memory...")
    classifier_service.load_model()
    print("ML Classifier ready.")

    print("Starting global HTTP client for APIs...")
    weather_service.client = httpx.AsyncClient() 
    print("All systems ready.")

    yield # The application handles requests while yielding here

    # --- SHUTDOWN ---
    print("Shutting down Smart Travel Planner...")
    await weather_service.client.aclose() # <-- Securely close the HTTP client
    await engine.dispose() # Cleanly close DB connections

app = FastAPI(lifespan=lifespan, title="Smart Travel Planner API")

# Include our API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])

@app.get("/")
async def health_check():
    return {"status": "online", "message": "Smart Travel Planner is running."}
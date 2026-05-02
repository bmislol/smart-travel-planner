import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from contextlib import asynccontextmanager
import httpx

# Import our singletons
from app.services.embedder import embedder
from app.services.classifier_service import classifier_service
from app.services.weather_service import weather_service
from app.db.session import engine

if settings.LANGCHAIN_TRACING_V2.lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173"
    ], # Allows your React frontend to connect
    allow_credentials=True,
    allow_methods=["*"], # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"], # Allows Authorization headers (for our JWT)
)

# Include our API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])

@app.get("/")
async def health_check():
    return {"status": "online", "message": "Smart Travel Planner is running."}
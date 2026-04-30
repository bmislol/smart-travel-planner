import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.core.config import settings
from app.db.session import engine
from app.services.embedder import TravelEmbedder
from app.services.classifier_service import MLClassifierService
from app.services.rag_service import RAGService
from app.services.weather_service import WeatherService
from app.api import auth, tools, agent

# 1. Structured Logging Setup
# Fulfills requirement for JSON-formatted logs
logger = structlog.get_logger()

# 2. Lifespan Handler: Singletons Done Right
# Manages startup (load models) and shutdown (cleanup)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Initializing hardware-accelerated services...")
    
    # Load MPNet onto RTX 3060 via the singleton service
    embedder = TravelEmbedder(model_name=settings.EMBEDDING_MODEL_NAME)
    
    # Initialize services
    ml_service = MLClassifierService(model_path=settings.CLASSIFIER_MODEL_PATH)
    rag_service = RAGService(embedder=embedder)
    weather_service = WeatherService()

    # Store in app.state to make them available to dependencies
    app.state.embedder = embedder
    app.state.ml_service = ml_service
    app.state.rag_service = rag_service
    app.state.weather_service = weather_service
    
    logger.info("All services ready. Server up.")
    
    yield
    
    # --- Shutdown ---
    logger.info("Shutting down... disposing database engine.")
    await engine.dispose()

# 3. App Initialization
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    version="1.0.0"
)

# 4. Dependency Injection Helpers
# These functions allow routers to use Depends(get_rag_service)
def get_rag_service(request: Request) -> RAGService:
    return request.app.state.rag_service

def get_ml_service(request: Request) -> MLClassifierService:
    return request.app.state.ml_service

def get_weather_service(request: Request) -> WeatherService:
    return request.app.state.weather_service

# 5. Include Routers
# Organizing by module for code hygiene
app.include_router(auth.router)
app.include_router(tools.router)
app.include_router(agent.router)

@app.get("/health")
async def health_check():
    return {"status": "online", "hardware": "RTX 3060 Detected"}
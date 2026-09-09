from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.health import router as health_router
from backend.app.api.chat import router as chat_router
from backend.app.api.memories import router as memories_router
from backend.app.api.graph import router as graph_router
from backend.app.api.temporal import router as temporal_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(memories_router, prefix=settings.API_V1_STR)
app.include_router(graph_router, prefix=settings.API_V1_STR)
app.include_router(temporal_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Threadline API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
        "chat": f"{settings.API_V1_STR}/chat",
        "memories": f"{settings.API_V1_STR}/memories",
        "graph": f"{settings.API_V1_STR}/graph",
        "temporal": f"{settings.API_V1_STR}/temporal",
    }

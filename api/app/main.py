from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routes import router
from app import __version__


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown logic.
    Creates database tables on startup.
    """
    # Startup: initialize database
    await init_db()
    yield
    # Shutdown: cleanup if needed (database connections close automatically)


app = FastAPI(
    title="QuickFlicks API",
    description="Fast video recommendation platform",
    version=__version__,
    lifespan=lifespan,
)

# CORS middleware to allow frontend requests
# In production, replace "*" with your specific frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(router, prefix="/api", tags=["recommendations"])


@app.get("/")
async def root():
    """
    Root endpoint that shows API info.
    """
    return {
        "service": "QuickFlicks API",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/health",
    }

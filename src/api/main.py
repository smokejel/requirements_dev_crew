from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from contextlib import asynccontextmanager

from .routes import auth, crew, files, config, websocket
from .services.config_service import ConfigService

# Global configuration service
config_service = ConfigService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting CrewAI Requirements API...")
    yield
    # Shutdown
    print("Shutting down CrewAI Requirements API...")

app = FastAPI(
    title="CrewAI Requirements Decomposer API",
    description="API for AI-powered requirement decomposition system",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "CrewAI Requirements API is running"}

# API routes
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(crew.router, prefix="/api/crew", tags=["crew"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(config.router, prefix="/api/config", tags=["configuration"])
app.include_router(websocket.router, prefix="/api", tags=["websocket"])

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

def main():
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
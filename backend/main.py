"""
FastAPI application entry point - CORRECTED VERSION
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from backend.config import settings
from backend.routes import upload, generate, download

# Create FastAPI app
app = FastAPI(
    title="AI Code Documentation Generator",
    description="Generate professional documentation from code using AI",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(generate.router, prefix="/api/generate", tags=["Generate"])
app.include_router(download.router, prefix="/api/download", tags=["Download"])

# Frontend directory
frontend_dir = Path("frontend")

if frontend_dir.exists():
    # Serve static files (CSS, JS) from frontend folder
    @app.get("/style.css")
    async def serve_css():
        """Serve CSS file"""
        css_file = frontend_dir / "style.css"
        if css_file.exists():
            return FileResponse(str(css_file), media_type="text/css")
        return {"error": "CSS not found"}
    
    @app.get("/app.js")
    async def serve_js():
        """Serve JavaScript file"""
        js_file = frontend_dir / "app.js"
        if js_file.exists():
            return FileResponse(str(js_file), media_type="application/javascript")
        return {"error": "JS not found"}

@app.get("/")
async def root():
    """Serve frontend HTML"""
    frontend_html = frontend_dir / "index.html"
    if frontend_html.exists():
        return FileResponse(str(frontend_html))
    return {
        "message": "AI Code Documentation Generator API",
        "version": "1.0.0",
        "endpoints": {
            "swagger_ui": "/api/docs",
            "redoc": "/api/redoc",
            "openapi_schema": "/api/openapi.json",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "groq_configured": bool(settings.GROQ_API_KEY),
        "frontend_exists": frontend_dir.exists()
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🚀 AI CODE DOCUMENTATION GENERATOR")
    print("="*70)
    print(f"📍 Server: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 Swagger UI: http://{settings.HOST}:{settings.PORT}/api/docs")
    print(f"📖 ReDoc: http://{settings.HOST}:{settings.PORT}/api/redoc")
    print(f"💚 Health Check: http://{settings.HOST}:{settings.PORT}/health")
    print("="*70 + "\n")
    
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
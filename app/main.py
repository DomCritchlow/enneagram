"""
Refactored Enneagram Team Assessment Application.

A FastAPI application for team Enneagram assessments with improved architecture,
security, error handling, and performance optimizations.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

# Import our modules
from core.config import settings
from core.logging import setup_logging, app_logger
from core.exceptions import EnneagramException, ValidationError as AppValidationError, create_error_response
from core.security import SecurityHeaders
from api.quiz import router as quiz_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    app_logger.info("Starting Enneagram application...")
    
    try:
        # Initialize Google Sheets service (test connection)
        from services.sheets_service import sheets_service
        if sheets_service.test_connection():
            app_logger.info("Google Sheets connection successful")
            sheets_service.initialize_sheet_headers()
        else:
            app_logger.warning("Google Sheets connection failed - results logging may not work")
        
        # Log configuration status
        if settings.debug:
            app_logger.info("Running in DEBUG mode")
        
        app_logger.info(f"Application started successfully on {settings.app_title}")
        
    except Exception as e:
        app_logger.error("Failed to start application", exception=e)
        # Don't raise - continue without Google Sheets if needed
    
    yield
    
    # Shutdown
    app_logger.info("Shutting down Enneagram application...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_title,
    description="Team Enneagram assessment tool with enhanced security and performance",
    version="2.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Add security headers and enforce HTTPS in production."""
    # HTTPS enforcement in production
    if not settings.debug:
        # Check if request is HTTPS (considering proxy headers from Cloud Run)
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        if forwarded_proto == "http":
            # Redirect to HTTPS
            url = request.url.replace(scheme="https")
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=str(url), status_code=301)
    
    response = await call_next(request)
    
    # Add security headers (conditional based on debug mode)
    headers = SecurityHeaders.get_headers(debug_mode=settings.debug)
    for key, value in headers.items():
        response.headers[key] = value
    
    return response


# Add CORS middleware (restrict in production)
if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:8000"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )


# Mount static files
try:
    static_path = settings.app_dir / "static"
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
except Exception as e:
    app_logger.error(f"Failed to mount static files: {e}")


# Initialize templates
try:
    templates = Jinja2Templates(directory=str(settings.app_dir / "templates"))
except Exception as e:
    app_logger.error(f"Failed to initialize templates: {e}")
    templates = None


# Exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    app_logger.warning(f"Validation error: {exc}")
    if templates:
        return create_error_response(
            request, templates, "Invalid input provided", 422
        )
    return HTMLResponse(
        content="<h1>Validation Error</h1><p>Invalid input provided</p>",
        status_code=422
    )


@app.exception_handler(AppValidationError)
async def app_validation_exception_handler(request: Request, exc: AppValidationError):
    """Handle application validation errors."""
    app_logger.warning(f"Application validation error: {exc.message}")
    if templates:
        return create_error_response(
            request, templates, exc.message, 400, exc.details
        )
    return HTMLResponse(
        content=f"<h1>Validation Error</h1><p>{exc.message}</p>",
        status_code=400
    )


@app.exception_handler(EnneagramException)
async def enneagram_exception_handler(request: Request, exc: EnneagramException):
    """Handle custom application errors."""
    app_logger.error(f"Application error: {exc.message}", exception=exc)
    if templates:
        return create_error_response(
            request, templates, exc.message, 500, exc.details
        )
    return HTMLResponse(
        content=f"<h1>Application Error</h1><p>{exc.message}</p>",
        status_code=500
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    """Handle internal server errors."""
    app_logger.error("Internal server error", exception=exc)
    if templates:
        return create_error_response(
            request, templates, "An internal server error occurred", 500
        )
    return HTMLResponse(
        content="<h1>Internal Server Error</h1><p>Something went wrong</p>",
        status_code=500
    )


# Include routers
app.include_router(quiz_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    try:
        # Test Google Sheets connection
        from services.sheets_service import sheets_service
        sheets_available = sheets_service.test_connection()
        
        return {
            "status": "healthy",
            "service": settings.app_title,
            "version": "2.0.0",
            "debug": settings.debug,
            "google_sheets": "available" if sheets_available else "unavailable"
        }
    except Exception as e:
        app_logger.error("Health check failed", exception=e)
        raise HTTPException(status_code=503, detail="Service unavailable")


# Removed debug endpoints for simplicity


# Root redirect for convenience
@app.get("/app")
async def redirect_to_quiz():
    """Redirect /app to main quiz page."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/")


if __name__ == "__main__":
    import uvicorn
    
    # Setup logging
    setup_logging()
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )

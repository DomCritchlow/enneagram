"""
Admin-related API routes.
"""
import csv
import io
from typing import List

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from core.config import settings
from core.exceptions import create_error_response
from core.logging import app_logger
from core.security import validate_admin_credentials
from services.quiz_service import quiz_service

router = APIRouter()


async def get_templates() -> Jinja2Templates:
    """Get templates instance."""
    return Jinja2Templates(directory=str(settings.app_dir / "templates"))


def log_admin_action(request: Request, action: str, username: str = "admin"):
    """Log admin actions with IP address."""
    client_ip = request.client.host if request.client else "unknown"
    app_logger.log_admin_access(username, action, client_ip)


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, _: bool = Depends(validate_admin_credentials)):
    """Admin dashboard showing type distribution."""
    try:
        templates = await get_templates()
        
        # Log admin access
        log_admin_action(request, "dashboard_access")
        
        # Get statistics
        counts = quiz_service.get_admin_stats()
        blurbs = quiz_service.load_type_blurbs()
        
        return templates.TemplateResponse(
            "admin.html", 
            {
                "request": request, 
                "counts": counts, 
                "blurbs": {k: v.dict() for k, v in blurbs.items()}
            }
        )
        
    except Exception as e:
        app_logger.error("Error loading admin dashboard", exception=e)
        templates = await get_templates()
        return create_error_response(
            request, templates, "Error loading admin dashboard.", 500
        )


@router.get("/export.csv")
async def export_csv(request: Request, _: bool = Depends(validate_admin_credentials)):
    """Export quiz results as CSV."""
    try:
        # Log export action
        log_admin_action(request, "data_export")
        
        # Get CSV data
        csv_data = quiz_service.export_results_csv()
        
        # Create CSV string
        output = io.StringIO()
        writer = csv.writer(output)
        for row in csv_data:
            writer.writerow(row)
        csv_string = output.getvalue()
        output.close()
        
        # Log export completion
        app_logger.log_data_export(len(csv_data) - 1, "admin")  # -1 for header row
        
        # Return as streaming response
        def generate_csv():
            yield csv_string
        
        return StreamingResponse(
            generate_csv(),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=enneagram_results.csv"
            }
        )
        
    except Exception as e:
        app_logger.error("Error exporting CSV", exception=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting data"
        )


@router.get("/admin/health")
async def admin_health(request: Request, _: bool = Depends(validate_admin_credentials)):
    """Admin health check endpoint."""
    try:
        log_admin_action(request, "health_check")
        
        # Get basic statistics
        counts = quiz_service.get_admin_stats()
        total_responses = sum(counts.values())
        
        health_data = {
            "status": "healthy",
            "total_responses": total_responses,
            "type_distribution": counts,
            "database_accessible": True,
            "config_valid": True,
        }
        
        return health_data
        
    except Exception as e:
        app_logger.error("Health check failed", exception=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

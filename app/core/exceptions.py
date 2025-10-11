"""
Simplified exception handling.
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


class EnneagramException(Exception):
    """Base exception for Enneagram application."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(EnneagramException):
    """Raised when input validation fails."""
    pass


def create_error_response(
    request: Request,
    templates: Jinja2Templates,
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None
) -> HTMLResponse:
    """Create a standardized error response."""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "message": message,
            "details": details or {},
            "status_code": status_code
        },
        status_code=status_code
    )


def create_http_exception(
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create a standardized HTTP exception."""
    return HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "details": details or {}
        }
    )
"""
Quiz-related API routes.
"""
import json
from typing import Dict, Any

from fastapi import APIRouter, Form, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.config import settings
from core.exceptions import ValidationError, create_error_response
from core.logging import app_logger
from core.security import sanitize_input
from services.quiz_service import quiz_service
from models.schemas import QuizSubmission

router = APIRouter()

# Router for quiz-related endpoints


async def get_templates() -> Jinja2Templates:
    """Get templates instance."""
    return Jinja2Templates(directory=str(settings.app_dir / "templates"))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with new UI."""
    templates = await get_templates()
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/api/questions")
async def get_questions():
    """API endpoint to get questions as JSON."""
    try:
        questions = quiz_service.load_questions()
        return [q.dict() for q in questions]
    except Exception as e:
        app_logger.error("Failed to load questions via API", exception=e)
        raise HTTPException(status_code=500, detail="Failed to load questions")


@router.get("/quiz", response_class=HTMLResponse) 
async def redirect_to_home(request: Request):
    """Redirect old quiz URL to new home page."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=301)


@router.get("/results", response_class=HTMLResponse)
async def show_results(request: Request, name: str = None, type: int = None, token: str = None):
    """Show results page."""
    templates = await get_templates()
    
    if not all([name, type, token]):
        # No result data, show message to take assessment
        return templates.TemplateResponse("results.html", {
            "request": request,
            "message": "Complete the assessment to see your results.",
            "show_message_only": True
        })
    
    try:
        # Get the actual result data from database using token
        result_data = quiz_service.get_result_by_token(token)
        
        if not result_data:
            # Token not found, show message to take assessment
            return templates.TemplateResponse("results.html", {
                "request": request,
                "message": "Results not found. Please take the assessment again.",
                "show_message_only": True
            })
        
        # Get type information
        blurbs = quiz_service.load_type_blurbs()
        type_info = blurbs.get(result_data["top_type"], None)
        
        # Ensure scores is always a dictionary
        scores = result_data.get("scores", {})
        if not scores:
            # Fallback scores if none found
            scores = {i: 15 + (5 if i == result_data["top_type"] else 0) for i in range(1, 10)}
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "name": result_data["name"],
            "top_type": result_data["top_type"],
            "scores": scores,
            "wings": result_data["wings"],
            "type_info": type_info.dict() if type_info else {},
            "delete_token": token,
            "validity": result_data.get("validity", {"mean": 3.0, "sd": 1.0})
        })
        
    except Exception as e:
        app_logger.error("Error displaying results", exception=e)
        return create_error_response(
            request, templates, "Error loading results", 500
        )


@router.get("/types", response_class=HTMLResponse)
async def show_types(request: Request):
    """Show all Enneagram types overview page."""
    templates = await get_templates()
    
    try:
        # Get all type information
        blurbs = quiz_service.load_type_blurbs()
        
        return templates.TemplateResponse("types.html", {
            "request": request,
            "types_data": blurbs
        })
        
    except Exception as e:
        app_logger.error("Error displaying types", exception=e)
        return create_error_response(
            request, templates, "Error loading types", 500
        )


@router.post("/submit", response_class=HTMLResponse)
async def submit_quiz(request: Request, name: str = Form(...), consent: str = Form(...)):
    """Process quiz submission."""
    templates = await get_templates()
    
    try:
        # Get client IP for logging
        client_ip = request.client.host if request.client else "unknown"
        
        name = sanitize_input(name.strip(), settings.name_max_length)
        
        # Validate basic form data
        if consent != "yes":
            app_logger.warning(f"Quiz submission without consent from {client_ip}")
            return create_error_response(
                request, templates, "You must consent to proceed.", 400
            )
        
        if not name:
            return create_error_response(
                request, templates, "Name is required.", 400
            )
        
        # Get all form data for quiz answers
        form_data = await request.form()
        quiz_answers = {}
        
        # Extract quiz answers
        for key, value in form_data.items():
            if key.startswith('q_'):
                try:
                    quiz_answers[key] = int(value)
                except ValueError:
                    return create_error_response(
                        request, templates, f"Invalid response for {key}", 400
                    )
        
        # Validate we have all required answers
        questions = quiz_service.load_questions()
        for question in questions:
            key = f"q_{question.id}"
            if key not in quiz_answers:
                return create_error_response(
                    request, templates, f"Missing answer for question {question.id}", 400
                )
        
        # Process the quiz
        try:
            app_logger.info(f"Processing quiz submission for: {name}")
            result = quiz_service.process_quiz_submission(name, quiz_answers)
            app_logger.info(f"Quiz processed successfully, saving result for: {name}")
            quiz_service.save_quiz_result(result)
            app_logger.info(f"Quiz result saved successfully for: {name}")
            
            # Log successful submission
            tied = result.tied_types is not None and len(result.tied_types) > 1
            app_logger.log_quiz_submission(result.name, result.top_type, tied)
            
            # Redirect to results page with result data
            from urllib.parse import urlencode
            result_params = {
                'name': result.name,
                'type': result.top_type,
                'token': result.delete_token
            }
            return RedirectResponse(
                url=f"/results?{urlencode(result_params)}", 
                status_code=303
            )
            
        except ValueError as e:
            app_logger.error(f"Quiz processing error for {name}", exception=e)
            return create_error_response(
                request, templates, "Error processing quiz results.", 500
            )
        
    except Exception as e:
        app_logger.error("Unexpected error in quiz submission", exception=e)
        return create_error_response(
            request, templates, "An unexpected error occurred.", 500
        )


@router.get("/delete/{token}")
async def delete_entry(request: Request, token: str):
    """Delete quiz entry using delete token."""
    try:
        # Sanitize token
        clean_token = sanitize_input(token, 50)
        
        # Attempt to delete
        deleted_name = quiz_service.delete_entry_by_token(clean_token)
        
        if deleted_name:
            app_logger.log_quiz_deletion(deleted_name, clean_token)
            return HTMLResponse(
                f"<html><body>"
                f"<h3>Deleted entry for <em>{deleted_name}</em>.</h3>"
                f"<p>You can close this window.</p>"
                f"</body></html>"
            )
        else:
            templates = await get_templates()
            return create_error_response(
                request, templates, "Invalid or already used delete link.", 404
            )
            
    except Exception as e:
        app_logger.error("Error deleting entry", exception=e)
        templates = await get_templates()
        return create_error_response(
            request, templates, "Error deleting entry.", 500
        )

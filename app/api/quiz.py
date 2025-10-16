"""
Quiz-related API routes.
"""
import json
from typing import Dict, Any, List
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Form, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.config import settings
from core.exceptions import ValidationError, create_error_response
from core.logging import app_logger
from core.security import sanitize_input
from services.quiz_service import quiz_service
from services.sheets_service import sheets_service
from models.schemas import QuizSubmission, TeamStats, TeamTypeCount

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
    """API endpoint to get questions as JSON (without type information)."""
    try:
        questions = quiz_service.load_questions()
        # Exclude sensitive type information from API response
        return [
            {
                "id": q.id,
                "text": q.text,
                "reverse": q.reverse
            }
            for q in questions
        ]
    except Exception as e:
        app_logger.error("Failed to load questions via API", exception=e)
        raise HTTPException(status_code=500, detail="Failed to load questions")


@router.get("/quiz", response_class=HTMLResponse) 
async def redirect_to_home(request: Request):
    """Redirect old quiz URL to new home page."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=301)


@router.get("/results", response_class=HTMLResponse)
async def show_results(request: Request, data: str = None):
    """Show results page."""
    templates = await get_templates()
    
    if not data:
        # No result data, show message to take assessment
        return templates.TemplateResponse("results.html", {
            "request": request,
            "message": "Complete the assessment to see your results.",
            "show_message_only": True
        })
    
    try:
        # Decode result data from URL parameter
        import json
        import base64
        
        decoded_data = base64.urlsafe_b64decode(data.encode('utf-8')).decode('utf-8')
        result_data = json.loads(decoded_data)
        
        # Get type information
        blurbs = quiz_service.load_type_blurbs()
        type_info = blurbs.get(str(result_data["top_type"]), None)
        
        # Calculate wings from the scores
        wings = quiz_service.calculate_wings(result_data["top_type"], result_data["scores"])
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "name": result_data["name"],
            "team": result_data.get("team"),
            "top_type": result_data["top_type"],
            "scores": result_data["scores"],
            "wings": wings,
            "type_info": type_info if type_info else {},
            "validity": result_data.get("validity", {"mean": 3.0, "sd": 1.0}),
            "show_delete_option": False  # No delete functionality in stateless version
        })
        
    except Exception as e:
        app_logger.error("Error displaying results", exception=e)
        return templates.TemplateResponse("results.html", {
            "request": request,
            "message": "Invalid results data. Please take the assessment again.",
            "show_message_only": True
        })


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
async def submit_quiz(request: Request, name: str = Form(...), consent: str = Form(...), team: str = Form(None)):
    """Process quiz submission."""
    templates = await get_templates()
    
    try:
        # Get client IP for logging
        client_ip = request.client.host if request.client else "unknown"
        
        # Sanitize inputs
        name = sanitize_input(name.strip(), settings.name_max_length)
        team = sanitize_input(team.strip() if team else "", 20) if team else None
        
        # Validate submission using schema
        try:
            submission = QuizSubmission(name=name, team=team, consent=consent)
        except ValueError as e:
            app_logger.warning(f"Quiz submission validation failed from {client_ip}: {e}")
            return create_error_response(
                request, templates, str(e), 400
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
            result = quiz_service.process_quiz_submission(submission.name, quiz_answers, submission.team)
            app_logger.info(f"Quiz processed successfully for: {name}")
            
            # Log to Google Sheets (non-blocking - don't fail if this fails)
            try:
                sheets_success = sheets_service.log_quiz_result(result)
                if sheets_success:
                    app_logger.info(f"Quiz result logged to Google Sheets for: {name}")
                else:
                    app_logger.warning(f"Failed to log quiz result to Google Sheets for: {name}")
            except Exception as e:
                app_logger.error(f"Error logging to Google Sheets for {name}: {e}")
            
            # Log successful submission
            tied = result.tied_types is not None and len(result.tied_types) > 1
            app_logger.log_quiz_submission(result.name, result.top_type, tied)
            
            # Redirect to results page with full result data
            from urllib.parse import urlencode
            import json
            import base64
            
            # Encode result data for URL
            result_data = {
                'name': result.name,
                'team': result.team,
                'top_type': result.top_type,
                'scores': result.scores.to_dict(),
                'validity': {
                    'mean': result.validity.mean,
                    'sd': result.validity.sd
                },
                'tied_types': result.tied_types
            }
            
            # Base64 encode the JSON to make it URL-safe
            encoded_data = base64.urlsafe_b64encode(
                json.dumps(result_data).encode('utf-8')
            ).decode('utf-8')
            
            result_params = {'data': encoded_data}
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


# Simple in-memory cache for team data
team_cache = {}
CACHE_DURATION = timedelta(minutes=1)  # Cache for 1 minute


def calculate_team_stats(team_data: List[Dict[str, Any]], team_name: str) -> TeamStats:
    """Calculate team statistics from raw team data."""
    if not team_data:
        # Return empty stats for teams with no data
        return TeamStats(
            team_name=team_name,
            total_members=0,
            type_distribution=[],
            missing_types=list(range(1, 10)),
            underrepresented_types=[],
            dominant_types=[],
            balance_score=0.0
        )
    
    # Count types
    type_counts = {i: 0 for i in range(1, 10)}
    for member in team_data:
        top_type = int(member.get('Top Type', 0))
        if 1 <= top_type <= 9:
            type_counts[top_type] += 1
    
    total_members = len(team_data)
    
    # Create type distribution
    type_names = {
        1: "Reformer", 2: "Helper", 3: "Achiever", 4: "Individualist", 5: "Investigator",
        6: "Loyalist", 7: "Enthusiast", 8: "Challenger", 9: "Peacemaker"
    }
    
    type_distribution = []
    for type_num in range(1, 10):
        count = type_counts[type_num]
        percentage = (count / total_members * 100) if total_members > 0 else 0
        type_distribution.append(TeamTypeCount(
            type_number=type_num,
            type_name=type_names[type_num],
            count=count,
            percentage=round(percentage, 1)
        ))
    
    # Calculate missing, underrepresented, and dominant types
    missing_types = [t for t in range(1, 10) if type_counts[t] == 0]
    underrepresented_types = [t for t in range(1, 10) if type_counts[t] == 1 and total_members > 3]
    
    # Dominant types are those with significantly higher representation
    if total_members > 0:
        avg_per_type = total_members / 9
        dominant_threshold = max(2, avg_per_type * 1.5)  # At least 50% above average, minimum 2
        dominant_types = [t for t in range(1, 10) if type_counts[t] >= dominant_threshold]
    else:
        dominant_types = []
    
    # Calculate balance score (how evenly distributed)
    if total_members > 0:
        # Use standard deviation to measure balance - lower SD = better balance
        expected_per_type = total_members / 9
        variance = sum((type_counts[t] - expected_per_type) ** 2 for t in range(1, 10)) / 9
        std_dev = variance ** 0.5
        
        # Convert to 0-100 scale where 100 is perfectly balanced
        # Normalize by theoretical maximum std deviation for this team size
        max_possible_std = ((total_members ** 2) / 9) ** 0.5  # If all members in one type
        normalized_std = std_dev / max_possible_std if max_possible_std > 0 else 0
        balance_score = max(0, 100 * (1 - normalized_std))
    else:
        balance_score = 0.0
    
    return TeamStats(
        team_name=team_name,
        total_members=total_members,
        type_distribution=type_distribution,
        missing_types=missing_types,
        underrepresented_types=underrepresented_types,
        dominant_types=dominant_types,
        balance_score=round(balance_score, 1)
    )


@router.get("/team/{team_name}", response_class=HTMLResponse)
async def team_stats(request: Request, team_name: str):
    """Display team statistics and analysis."""
    templates = await get_templates()
    
    try:
        # Sanitize team name (same validation as in submission)
        clean_team_name = sanitize_input(team_name.strip().lower(), 20)
        
        # Validate team name format
        if not re.match(r'^[a-z0-9]+$', clean_team_name) or len(clean_team_name) < 3:
            app_logger.warning(f"Invalid team name requested: {team_name}")
            return create_error_response(
                request, templates, "Invalid team name. Team names must be 3-20 characters, letters and numbers only.", 400
            )
        
        # Check cache first (unless caching is disabled)
        cache_key = f"team_{clean_team_name}"
        now = datetime.now()
        
        if not settings.disable_caching and cache_key in team_cache:
            cached_data, cached_time = team_cache[cache_key]
            if now - cached_time < CACHE_DURATION:
                app_logger.info(f"Serving cached team stats for: {clean_team_name}")
                return templates.TemplateResponse("team.html", {
                    "request": request,
                    "team_stats": cached_data
                })
        
        # Get team data from Google Sheets
        cache_status = "caching disabled" if settings.disable_caching else "cache miss"
        app_logger.info(f"Fetching team data for: {clean_team_name} ({cache_status})")
        team_data = sheets_service.get_team_data(clean_team_name)
        
        # Calculate statistics
        team_stats_obj = calculate_team_stats(team_data, clean_team_name)
        
        # Cache the results (unless caching is disabled)
        if not settings.disable_caching:
            team_cache[cache_key] = (team_stats_obj, now)
        
        # Clean old cache entries (simple cleanup)
        if len(team_cache) > 50:  # Arbitrary limit
            oldest_keys = sorted(team_cache.keys(), key=lambda k: team_cache[k][1])[:10]
            for old_key in oldest_keys:
                del team_cache[old_key]
        
        app_logger.info(f"Successfully generated team stats for {clean_team_name}: {team_stats_obj.total_members} members")
        
        return templates.TemplateResponse("team.html", {
            "request": request,
            "team_stats": team_stats_obj
        })
        
    except Exception as e:
        app_logger.error(f"Error generating team stats for {team_name}", exception=e)
        return create_error_response(
            request, templates, "Error loading team statistics. Please try again later.", 500
        )



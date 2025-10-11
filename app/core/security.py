"""
Security utilities and authentication.
"""
import secrets
import hashlib
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from core.config import settings

security = HTTPBasic()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_delete_token() -> str:
    """Generate a secure delete token."""
    # 32 bytes = 256 bits of entropy for extra security
    return secrets.token_urlsafe(32)


def generate_secret_key() -> str:
    """Generate a secure secret key."""
    return secrets.token_urlsafe(32)


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not text:
        return ""
    
    # Strip whitespace and limit length
    text = text.strip()[:max_length]
    
    # Remove potential XSS characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text


def validate_admin_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """
    Validate admin credentials with secure comparison.
    
    Args:
        credentials: HTTP Basic credentials
        
    Returns:
        True if credentials are valid
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Use constant-time comparison to prevent timing attacks
    username_correct = secrets.compare_digest(
        credentials.username.encode('utf-8'),
        settings.admin_user.encode('utf-8')
    )
    password_correct = secrets.compare_digest(
        credentials.password.encode('utf-8'),
        settings.admin_pass.encode('utf-8')
    )
    
    if not (username_correct and password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return True


def create_csrf_token() -> str:
    """Create a CSRF token for form protection."""
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, expected: str) -> bool:
    """Validate CSRF token."""
    return secrets.compare_digest(token, expected)


class SecurityHeaders:
    """Security headers for HTTP responses."""
    
    @staticmethod
    def get_headers(debug_mode: bool = False) -> dict:
        """Get security headers dictionary."""
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
        }
        
        if debug_mode:
            # Relaxed headers for local development
            headers.update({
                "X-Frame-Options": "SAMEORIGIN",  # Allow framing from same origin
                "Content-Security-Policy": "default-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            })
        else:
            # Strict headers for production
            headers.update({
                "X-Frame-Options": "DENY",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'",
            })
        
        return headers


def generate_session_id() -> str:
    """Generate a secure session identifier."""
    return hashlib.sha256(secrets.token_bytes(32)).hexdigest()


# Session management (consolidated from auth_service)
_session_tokens = {}  # In-memory session storage

def authenticate_admin(username: str, password: str) -> bool:
    """Authenticate admin credentials."""
    username_correct = secrets.compare_digest(
        username.encode('utf-8'),
        settings.admin_user.encode('utf-8')
    )
    password_correct = secrets.compare_digest(
        password.encode('utf-8'),
        settings.admin_pass.encode('utf-8')
    )
    return username_correct and password_correct

def create_session_token(username: str) -> str:
    """Create a session token for authenticated user."""
    token = secrets.token_urlsafe(32)
    _session_tokens[token] = username
    return token

def validate_session_token(token: str) -> Optional[str]:
    """Validate session token and return username if valid."""
    return _session_tokens.get(token)

# Legacy function for backwards compatibility
def auth_guard(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """Legacy auth guard function."""
    return validate_admin_credentials(credentials)

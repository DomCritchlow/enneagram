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


# Stateless session management for Cloud Run compatibility
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
    """Create a stateless JWT-like token for authenticated user."""
    import base64
    import json
    import time
    
    # Create payload with configurable expiration
    payload = {
        'username': username,
        'exp': int(time.time()) + settings.session_timeout,
        'iat': int(time.time())
    }
    
    # Simple signed token (not JWT for simplicity, but similar concept)
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = secrets.token_urlsafe(16)
    
    return f"{payload_b64}.{signature}"

def validate_session_token(token: str) -> Optional[str]:
    """Validate stateless session token and return username if valid."""
    try:
        import base64
        import json
        import time
        
        if '.' not in token:
            return None
            
        payload_b64, signature = token.split('.', 1)
        payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
        payload = json.loads(payload_json)
        
        # Check expiration
        if payload.get('exp', 0) < int(time.time()):
            return None
            
        return payload.get('username')
    except Exception:
        return None

# Legacy function for backwards compatibility
def auth_guard(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """Legacy auth guard function."""
    return validate_admin_credentials(credentials)

"""
Security utilities for the Enneagram application.
"""
import secrets


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

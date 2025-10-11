"""
Simplified logging configuration.
"""
import logging
import sys
from pathlib import Path

from core.config import settings


def setup_logging() -> logging.Logger:
    """Set up application logging configuration."""
    # Create logs directory if it doesn't exist
    log_dir = settings.app_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Set logging level
    log_level = logging.DEBUG if settings.debug else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "app.log"),
        ]
    )
    
    # Create application logger
    logger = logging.getLogger("enneagram")
    
    # Security logger for authentication events
    security_logger = logging.getLogger("enneagram.security")
    security_handler = logging.FileHandler(log_dir / "security.log")
    security_handler.setFormatter(logging.Formatter(log_format))
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)
    
    return logger


class ApplicationLogger:
    """Simplified application logger."""
    
    def __init__(self):
        self.logger = logging.getLogger("enneagram")
        self.security_logger = logging.getLogger("enneagram.security")
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str, exception: Exception = None):
        """Log error message."""
        if exception:
            self.logger.error(f"{message}: {str(exception)}", exc_info=True)
        else:
            self.logger.error(message)
    
    def log_quiz_submission(self, name: str, top_type: int, tied: bool = False):
        """Log quiz submission."""
        tie_info = " (tied result)" if tied else ""
        self.info(f"Quiz submitted: {name} -> Type {top_type}{tie_info}")
    
    def log_admin_access(self, username: str, action: str, ip_address: str = "unknown"):
        """Log admin actions."""
        self.security_logger.info(f"Admin action: {username} from {ip_address} - {action}")
    
    def log_auth_attempt(self, username: str, success: bool, ip_address: str = "unknown"):
        """Log authentication attempt."""
        status = "SUCCESS" if success else "FAILED"
        self.security_logger.info(f"Auth attempt: {username} from {ip_address} - {status}")
    
    def log_data_export(self, record_count: int, username: str = "admin"):
        """Log data export activity."""
        self.security_logger.info(f"Data export: {record_count} records exported by {username}")
    
    def log_quiz_deletion(self, name: str, token: str):
        """Log quiz deletion activity."""
        # Only log the name for privacy - don't log the full token
        self.info(f"Quiz result deleted: {name} (token: {token[:8]}...)")


# Global logger instances
app_logger = ApplicationLogger()

# Initialize logging
setup_logging()
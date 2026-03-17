"""Logging configuration for Glaze."""
import logging
import json
from datetime import datetime
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    SENSITIVE_KEYS = {
        'access_token', 'refresh_token', 'api_key', 'password',
        'secret', 'token', 'authorization', 'gemini_api_key',
        'google_client_secret'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'component': record.name,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra'):
            extra = self._sanitize_data(record.extra)
            log_data.update(extra)
        
        return json.dumps(log_data)
    
    def _sanitize_data(self, data: Any) -> Any:
        """Remove sensitive data from logs."""
        if isinstance(data, dict):
            return {
                k: '***' if k.lower() in self.SENSITIVE_KEYS else self._sanitize_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, str):
            # Check if string contains sensitive patterns
            lower_data = data.lower()
            for key in self.SENSITIVE_KEYS:
                if key in lower_data:
                    return '***'
            return data
        else:
            return data


def setup_logging(level: str = "INFO", use_json: bool = False):
    """
    Configure application logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        use_json: Use JSON structured logging
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create handler
    handler = logging.StreamHandler()
    
    # Set formatter
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

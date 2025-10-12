"""
Logging utilities for Google Ads Dashboard
Provides structured logging with different levels and formatters
"""

import os
import sys
import logging
import logging.handlers
from typing import Optional
from datetime import datetime
import json

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message']:
                log_entry[key] = value
        
        return json.dumps(log_entry)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        """Format log record with colors"""
        # Get color for log level
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format message
        message = f"{color}[{timestamp}] {record.levelname:8} {record.name}: {record.getMessage()}{reset}"
        
        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message

class DashboardLogger:
    """Main logger class for the dashboard"""
    
    def __init__(self, name: str = "google_ads_dashboard"):
        """
        Initialize dashboard logger
        
        Args:
            name: Logger name
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self._configured = False
    
    def configure(self, 
                 level: str = "INFO",
                 log_file: Optional[str] = None,
                 console_output: bool = True,
                 json_format: bool = False,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """
        Configure logger with handlers and formatters
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            console_output: Whether to output to console
            json_format: Whether to use JSON formatting
            max_file_size: Maximum log file size in bytes
            backup_count: Number of backup files to keep
        """
        if self._configured:
            return
        
        # Set log level
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            
            if json_format:
                console_handler.setFormatter(JSONFormatter())
            else:
                console_handler.setFormatter(ColoredFormatter())
            
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            # Rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count
            )
            file_handler.setLevel(log_level)
            
            if json_format:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
            
            self.logger.addHandler(file_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
        self._configured = True
        
        self.logger.info(f"Logger configured: level={level}, file={log_file}, json={json_format}")
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""
        if not self._configured:
            # Auto-configure with defaults
            self.configure()
        
        return self.logger

# Global logger instance
_dashboard_logger = None

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get logger instance
    
    Args:
        name: Logger name (uses default if None)
        
    Returns:
        Configured logger instance
    """
    global _dashboard_logger
    
    if name:
        # Return named logger
        logger = logging.getLogger(name)
        if not logger.handlers:
            # Configure if not already configured
            dashboard_logger = DashboardLogger(name)
            dashboard_logger.configure(
                level=os.getenv('LOG_LEVEL', 'INFO'),
                log_file=os.getenv('LOG_FILE'),
                json_format=os.getenv('LOG_FORMAT', '').lower() == 'json'
            )
            return dashboard_logger.get_logger()
        return logger
    
    # Return default logger
    if _dashboard_logger is None:
        _dashboard_logger = DashboardLogger()
        _dashboard_logger.configure(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE'),
            json_format=os.getenv('LOG_FORMAT', '').lower() == 'json'
        )
    
    return _dashboard_logger.get_logger()

def setup_logging(level: str = "INFO", 
                 log_file: Optional[str] = None,
                 json_format: bool = False):
    """
    Setup logging for the entire application
    
    Args:
        level: Log level
        log_file: Path to log file
        json_format: Whether to use JSON formatting
    """
    global _dashboard_logger
    
    _dashboard_logger = DashboardLogger()
    _dashboard_logger.configure(
        level=level,
        log_file=log_file,
        json_format=json_format
    )

class LogContext:
    """Context manager for adding context to log messages"""
    
    def __init__(self, logger: logging.Logger, **context):
        """
        Initialize log context
        
        Args:
            logger: Logger instance
            **context: Context fields to add to log messages
        """
        self.logger = logger
        self.context = context
        self.old_factory = None
    
    def __enter__(self):
        """Enter context manager"""
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        logging.setLogRecordFactory(self.old_factory)

def log_api_call(customer_id: str, operation: str):
    """
    Decorator to log Google Ads API calls
    
    Args:
        customer_id: Google Ads customer ID
        operation: Operation being performed
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(f"google_ads_api.{operation}")
            
            with LogContext(logger, customer_id=customer_id, operation=operation):
                logger.info(f"Starting {operation} for customer {customer_id}")
                
                try:
                    start_time = datetime.now()
                    result = func(*args, **kwargs)
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"Completed {operation} in {duration:.2f}s")
                    return result
                    
                except Exception as e:
                    logger.error(f"Failed {operation}: {str(e)}")
                    raise
        
        return wrapper
    return decorator

def log_performance(func):
    """Decorator to log function performance"""
    def wrapper(*args, **kwargs):
        logger = get_logger("performance")
        func_name = f"{func.__module__}.{func.__name__}"
        
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.debug(f"{func_name} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"{func_name} failed after {duration:.3f}s: {str(e)}")
            raise
    
    return wrapper
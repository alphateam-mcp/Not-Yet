#!/usr/bin/env python3
"""
Enhanced Logging Configuration for Not-Yet Platform
Provides structured logging with JSON formatting and log aggregation.
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self, service_name: str = "not-yet"):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Basic log data
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': self.service_name
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_data[key] = value
        
        # Add code location
        log_data['location'] = f"{record.filename}:{record.lineno}"
        log_data['function'] = record.funcName
        
        return json.dumps(log_data, default=str)

class SecurityFilter(logging.Filter):
    """Filter to remove sensitive information from logs"""
    
    SENSITIVE_PATTERNS = [
        'password', 'passwd', 'pwd', 'secret', 'key', 'token', 
        'auth', 'credential', 'private', 'sensitive'
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out sensitive information"""
        message = record.getMessage().lower()
        
        # Check if message contains sensitive keywords
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                # Redact the message
                record.msg = "[REDACTED - Contains sensitive information]"
                record.args = ()
                break
        
        return True

class ContextualAdapter(logging.LoggerAdapter):
    """Logger adapter that adds contextual information"""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        super().__init__(logger, extra)
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra context to log messages"""
        kwargs.setdefault('extra', {}).update(self.extra)
        return msg, kwargs

def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    enable_json: bool = True,
    enable_console: bool = True,
    enable_file: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup comprehensive logging configuration
    
    Args:
        service_name: Name of the service for logging context
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: ./logs)
        enable_json: Enable JSON formatting
        enable_console: Enable console logging
        enable_file: Enable file logging
        max_file_size: Maximum size per log file in bytes
        backup_count: Number of backup files to keep
    
    Returns:
        Configured logger instance
    """
    
    # Create log directory
    if log_dir is None:
        log_dir = os.path.join(os.getcwd(), 'logs')
    
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Security filter
    security_filter = SecurityFilter()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.addFilter(security_filter)
        
        if enable_json:
            console_handler.setFormatter(JSONFormatter(service_name))
        else:
            console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            console_handler.setFormatter(logging.Formatter(console_format))
        
        root_logger.addHandler(console_handler)
    
    # File handlers
    if enable_file:
        # Main application log
        app_log_file = os.path.join(log_dir, f'{service_name}.log')
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        app_handler.setLevel(getattr(logging, log_level.upper()))
        app_handler.addFilter(security_filter)
        
        if enable_json:
            app_handler.setFormatter(JSONFormatter(service_name))
        else:
            file_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            app_handler.setFormatter(logging.Formatter(file_format))
        
        root_logger.addHandler(app_handler)
        
        # Error log (ERROR and CRITICAL only)
        error_log_file = os.path.join(log_dir, f'{service_name}-error.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(security_filter)
        
        if enable_json:
            error_handler.setFormatter(JSONFormatter(service_name))
        else:
            error_handler.setFormatter(logging.Formatter(file_format))
        
        root_logger.addHandler(error_handler)
        
        # Access log for HTTP requests
        access_log_file = os.path.join(log_dir, f'{service_name}-access.log')
        access_handler = logging.handlers.RotatingFileHandler(
            access_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        access_handler.setLevel(logging.INFO)
        
        # Create access logger
        access_logger = logging.getLogger('werkzeug')
        access_logger.addHandler(access_handler)
        access_logger.setLevel(logging.INFO)
    
    # Configure specific loggers
    configure_specific_loggers(service_name)
    
    logger = logging.getLogger(service_name)
    logger.info(f"Logging configured for {service_name}", extra={
        'log_level': log_level,
        'log_dir': log_dir,
        'json_enabled': enable_json,
        'console_enabled': enable_console,
        'file_enabled': enable_file
    })
    
    return logger

def configure_specific_loggers(service_name: str):
    """Configure specific loggers with appropriate levels"""
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    
    # Set levels for monitoring components
    logging.getLogger('monitoring').setLevel(logging.INFO)
    logging.getLogger('monitoring.metrics_collector').setLevel(logging.INFO)
    logging.getLogger('monitoring.middleware').setLevel(logging.INFO)
    logging.getLogger('monitoring.dashboard').setLevel(logging.INFO)

def get_contextual_logger(name: str, **context) -> ContextualAdapter:
    """
    Get a logger with additional context
    
    Args:
        name: Logger name
        **context: Additional context to include in logs
    
    Returns:
        Contextual logger adapter
    """
    base_logger = logging.getLogger(name)
    return ContextualAdapter(base_logger, context)

def log_tool_execution(tool_name: str, target: str, options: str = "") -> ContextualAdapter:
    """
    Get a logger configured for tool execution
    
    Args:
        tool_name: Name of the security tool
        target: Target being scanned
        options: Tool options/parameters
    
    Returns:
        Contextual logger for the tool execution
    """
    return get_contextual_logger(
        f'tools.{tool_name}',
        tool=tool_name,
        target=target,
        options=options,
        execution_id=f"{tool_name}_{int(datetime.now().timestamp())}"
    )

def log_request_context(endpoint: str, method: str, user_agent: str = "") -> ContextualAdapter:
    """
    Get a logger configured for HTTP request context
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        user_agent: User agent string
    
    Returns:
        Contextual logger for the request
    """
    return get_contextual_logger(
        'http.requests',
        endpoint=endpoint,
        method=method,
        user_agent=user_agent,
        request_id=f"req_{int(datetime.now().timestamp())}"
    )

class LogAggregator:
    """Simple log aggregation for collecting logs from multiple sources"""
    
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def aggregate_logs(self, time_range: str = "1h") -> Dict[str, Any]:
        """
        Aggregate logs from multiple sources
        
        Args:
            time_range: Time range to aggregate (1h, 6h, 24h)
        
        Returns:
            Aggregated log data
        """
        aggregated = {
            'summary': {
                'total_entries': 0,
                'by_level': {},
                'by_service': {},
                'errors': [],
                'time_range': time_range
            },
            'entries': []
        }
        
        # Find all log files
        log_files = list(self.log_dir.glob('*.log'))
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            if line.strip().startswith('{'):
                                # JSON log entry
                                entry = json.loads(line.strip())
                                aggregated['entries'].append(entry)
                                aggregated['summary']['total_entries'] += 1
                                
                                # Count by level
                                level = entry.get('level', 'UNKNOWN')
                                aggregated['summary']['by_level'][level] = \
                                    aggregated['summary']['by_level'].get(level, 0) + 1
                                
                                # Count by service
                                service = entry.get('service', 'unknown')
                                aggregated['summary']['by_service'][service] = \
                                    aggregated['summary']['by_service'].get(service, 0) + 1
                                
                                # Collect errors
                                if level in ['ERROR', 'CRITICAL']:
                                    aggregated['summary']['errors'].append({
                                        'timestamp': entry.get('timestamp'),
                                        'message': entry.get('message'),
                                        'service': service,
                                        'location': entry.get('location')
                                    })
                        except json.JSONDecodeError:
                            # Skip non-JSON lines
                            continue
            except Exception as e:
                logging.error(f"Error reading log file {log_file}: {e}")
        
        return aggregated

# Pre-configured logging setups for different environments
def setup_development_logging(service_name: str) -> logging.Logger:
    """Setup logging for development environment"""
    return setup_logging(
        service_name=service_name,
        log_level="DEBUG",
        enable_json=False,
        enable_console=True,
        enable_file=True
    )

def setup_production_logging(service_name: str, log_dir: str = "/var/log/not-yet") -> logging.Logger:
    """Setup logging for production environment"""
    return setup_logging(
        service_name=service_name,
        log_level="INFO",
        log_dir=log_dir,
        enable_json=True,
        enable_console=False,
        enable_file=True,
        max_file_size=50 * 1024 * 1024,  # 50MB
        backup_count=10
    )

def setup_testing_logging(service_name: str) -> logging.Logger:
    """Setup logging for testing environment"""
    return setup_logging(
        service_name=service_name,
        log_level="WARNING",
        enable_json=False,
        enable_console=True,
        enable_file=False
    )
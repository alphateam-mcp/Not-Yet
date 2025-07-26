#!/usr/bin/env python3
"""
Monitoring Middleware for Not-Yet Platform
Provides Flask middleware for automatic metrics collection and request tracking.
"""

import time
import functools
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from flask import Flask, request, g, Response
from werkzeug.exceptions import HTTPException

from .metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)

class MonitoringMiddleware:
    """Flask middleware for automatic monitoring and metrics collection"""
    
    def __init__(self, app: Optional[Flask] = None, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.metrics_collector = get_metrics_collector()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize middleware with Flask app"""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown)
        
        # Add error handler for monitoring
        app.errorhandler(Exception)(self._handle_exception)
        
        # Store reference in app config
        app.config['MONITORING_MIDDLEWARE'] = self
        
        logger.info("Monitoring middleware initialized")
    
    def _before_request(self):
        """Called before each request"""
        g.start_time = time.time()
        g.request_id = self._generate_request_id()
        
        # Log request start
        logger.debug(f"Request started: {request.method} {request.path} [ID: {g.request_id}]")
        
        # Record request start metric
        self.metrics_collector.add_metric(
            "http.requests.started",
            1,
            {
                "method": request.method,
                "endpoint": request.endpoint or "unknown",
                "path": request.path
            }
        )
    
    def _after_request(self, response: Response) -> Response:
        """Called after each request"""
        if not hasattr(g, 'start_time'):
            return response
        
        # Calculate response time
        response_time = time.time() - g.start_time
        
        # Get endpoint name
        endpoint = request.endpoint or request.path
        if endpoint.startswith('/'):
            endpoint = endpoint[1:].replace('/', '_') or 'root'
        
        # Record metrics
        self.metrics_collector.record_request(
            endpoint=endpoint,
            response_time=response_time,
            status_code=response.status_code
        )
        
        # Additional detailed metrics
        self.metrics_collector.add_metric(
            "http.request.duration",
            response_time,
            {
                "method": request.method,
                "endpoint": endpoint,
                "status_code": str(response.status_code),
                "status_class": f"{response.status_code // 100}xx"
            }
        )
        
        # Record response size if available
        if hasattr(response, 'content_length') and response.content_length:
            self.metrics_collector.add_metric(
                "http.response.size",
                response.content_length,
                {
                    "endpoint": endpoint,
                    "method": request.method
                }
            )
        
        # Log request completion
        logger.debug(
            f"Request completed: {request.method} {request.path} "
            f"[{response.status_code}] in {response_time:.3f}s [ID: {g.request_id}]"
        )
        
        # Add custom headers for monitoring
        if self.config.get('add_timing_headers', True):
            response.headers['X-Response-Time'] = f"{response_time:.3f}"
            response.headers['X-Request-ID'] = g.request_id
        
        return response
    
    def _teardown(self, exception=None):
        """Called when request context is torn down"""
        if exception:
            logger.error(f"Request failed with exception: {exception}")
            
            # Record error metric
            self.metrics_collector.add_metric(
                "http.errors.count",
                1,
                {
                    "error_type": type(exception).__name__,
                    "endpoint": request.endpoint or "unknown"
                }
            )
    
    def _handle_exception(self, error: Exception) -> Response:
        """Handle exceptions and record metrics"""
        # Record error metrics
        error_type = type(error).__name__
        
        self.metrics_collector.add_metric(
            "http.exceptions.count",
            1,
            {
                "error_type": error_type,
                "endpoint": request.endpoint or "unknown",
                "method": request.method
            }
        )
        
        # Log error with context
        logger.error(
            f"Exception in {request.method} {request.path}: {error}",
            extra={
                "request_id": getattr(g, 'request_id', 'unknown'),
                "error_type": error_type,
                "endpoint": request.endpoint
            }
        )
        
        # Re-raise the exception to let Flask handle it normally
        raise error
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())[:8]

def monitor_function(metric_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None):
    """Decorator to monitor function execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = metric_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record success metrics
                collector = get_metrics_collector()
                collector.add_metric(
                    f"function.{function_name}.duration",
                    duration,
                    {**(tags or {}), "status": "success"}
                )
                collector.add_metric(
                    f"function.{function_name}.calls",
                    1,
                    {**(tags or {}), "status": "success"}
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error metrics
                collector = get_metrics_collector()
                collector.add_metric(
                    f"function.{function_name}.duration",
                    duration,
                    {**(tags or {}), "status": "error", "error_type": type(e).__name__}
                )
                collector.add_metric(
                    f"function.{function_name}.errors",
                    1,
                    {**(tags or {}), "error_type": type(e).__name__}
                )
                
                raise
        
        return wrapper
    return decorator

def monitor_tool_execution(tool_name: str):
    """Decorator specifically for monitoring tool executions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            collector = get_metrics_collector()
            
            # Record tool execution start
            collector.add_metric(
                f"tool.{tool_name}.executions.started",
                1,
                {"tool": tool_name}
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Determine success based on result
                success = False
                if isinstance(result, dict):
                    success = result.get('success', False) or result.get('return_code', -1) == 0
                
                # Record metrics
                collector.add_metric(
                    f"tool.{tool_name}.execution_time",
                    duration,
                    {"tool": tool_name, "status": "success" if success else "failed"}
                )
                
                collector.add_metric(
                    f"tool.{tool_name}.executions.completed",
                    1,
                    {"tool": tool_name, "status": "success" if success else "failed"}
                )
                
                # Record timeout if applicable
                if isinstance(result, dict) and result.get('timed_out'):
                    collector.add_metric(
                        f"tool.{tool_name}.timeouts",
                        1,
                        {"tool": tool_name}
                    )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error metrics
                collector.add_metric(
                    f"tool.{tool_name}.execution_time",
                    duration,
                    {"tool": tool_name, "status": "error", "error_type": type(e).__name__}
                )
                
                collector.add_metric(
                    f"tool.{tool_name}.errors",
                    1,
                    {"tool": tool_name, "error_type": type(e).__name__}
                )
                
                raise
        
        return wrapper
    return decorator

class HealthCheckManager:
    """Enhanced health check management"""
    
    def __init__(self):
        self.custom_checks = {}
        self.metrics_collector = get_metrics_collector()
    
    def register_check(self, name: str, check_func: Callable[[], Dict[str, Any]]):
        """Register a custom health check"""
        self.custom_checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.custom_checks.items():
            try:
                start_time = time.time()
                result = check_func()
                duration = time.time() - start_time
                
                results[name] = {
                    **result,
                    'check_duration': duration,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Record metrics
                self.metrics_collector.add_metric(
                    f"health_check.{name}.duration",
                    duration,
                    {"check": name}
                )
                
                self.metrics_collector.add_metric(
                    f"health_check.{name}.status",
                    1.0 if result.get('healthy', False) else 0.0,
                    {"check": name}
                )
                
                if not result.get('healthy', False):
                    overall_healthy = False
                    
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = {
                    'healthy': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                overall_healthy = False
                
                # Record error metric
                self.metrics_collector.add_metric(
                    f"health_check.{name}.errors",
                    1,
                    {"check": name, "error_type": type(e).__name__}
                )
        
        return {
            'overall_healthy': overall_healthy,
            'checks': results,
            'timestamp': datetime.now().isoformat()
        }

# Global health check manager
_health_manager: Optional[HealthCheckManager] = None

def get_health_manager() -> HealthCheckManager:
    """Get the global health check manager"""
    global _health_manager
    if _health_manager is None:
        _health_manager = HealthCheckManager()
    return _health_manager

def health_check(name: str):
    """Decorator to register a function as a health check"""
    def decorator(func: Callable) -> Callable:
        get_health_manager().register_check(name, func)
        return func
    return decorator
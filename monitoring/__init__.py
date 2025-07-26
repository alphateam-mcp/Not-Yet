"""
Not-Yet Monitoring System

A comprehensive monitoring and observability system for the Not-Yet security testing platform.
Provides metrics collection, health checks, alerting, and a web dashboard.

Components:
- MetricsCollector: Core metrics collection and storage
- MonitoringMiddleware: Flask middleware for automatic request tracking
- MonitoringDashboard: Web-based dashboard for visualization
- Health check system with custom checks
"""

from .metrics_collector import MetricsCollector, get_metrics_collector, init_metrics_collector
from .middleware import (
    MonitoringMiddleware, 
    monitor_function, 
    monitor_tool_execution,
    HealthCheckManager,
    get_health_manager,
    health_check
)
from .dashboard import MonitoringDashboard, create_dashboard

__version__ = "1.0.0"
__all__ = [
    'MetricsCollector',
    'get_metrics_collector', 
    'init_metrics_collector',
    'MonitoringMiddleware',
    'monitor_function',
    'monitor_tool_execution', 
    'HealthCheckManager',
    'get_health_manager',
    'health_check',
    'MonitoringDashboard',
    'create_dashboard'
]
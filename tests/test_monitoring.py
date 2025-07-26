#!/usr/bin/env python3
"""
Tests for Not-Yet Monitoring System
Comprehensive test suite for monitoring components.
"""

import unittest
import time
import json
import tempfile
import threading
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from monitoring.metrics_collector import MetricsCollector, Metric, ServerHealth
    from monitoring.middleware import MonitoringMiddleware, monitor_function, monitor_tool_execution
    from monitoring.logging_config import JSONFormatter, SecurityFilter, setup_logging
    from monitoring.dashboard import MonitoringDashboard
    MONITORING_AVAILABLE = True
except ImportError as e:
    MONITORING_AVAILABLE = False
    print(f"Warning: Monitoring components not available for testing: {e}")

@unittest.skipUnless(MONITORING_AVAILABLE, "Monitoring components not available")
class TestMetricsCollector(unittest.TestCase):
    """Test cases for MetricsCollector"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.collector = MetricsCollector()
    
    def tearDown(self):
        """Clean up after tests"""
        if self.collector.is_running:
            self.collector.stop_collection()
    
    def test_metric_creation(self):
        """Test metric creation and storage"""
        metric = Metric(
            name="test.metric",
            value=42.0,
            timestamp=datetime.now(),
            tags={"source": "test"}
        )
        
        self.assertEqual(metric.name, "test.metric")
        self.assertEqual(metric.value, 42.0)
        self.assertEqual(metric.tags["source"], "test")
    
    def test_add_metric(self):
        """Test adding metrics to collector"""
        self.collector.add_metric("test.counter", 1, {"type": "counter"})
        
        metrics = self.collector.get_metrics(name_pattern="test.counter")
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0].name, "test.counter")
        self.assertEqual(metrics[0].value, 1)
        self.assertEqual(metrics[0].tags["type"], "counter")
    
    def test_metrics_filtering(self):
        """Test metric filtering by name and time"""
        # Add test metrics
        self.collector.add_metric("test.metric.1", 1)
        self.collector.add_metric("test.metric.2", 2)
        self.collector.add_metric("other.metric", 3)
        
        # Filter by name pattern
        test_metrics = self.collector.get_metrics(name_pattern="test.metric")
        self.assertEqual(len(test_metrics), 2)
        
        # Filter by time range
        recent_metrics = self.collector.get_metrics(time_range=timedelta(minutes=1))
        self.assertEqual(len(recent_metrics), 3)
    
    def test_health_status(self):
        """Test health status management"""
        health = ServerHealth(
            server_name="test-server",
            status="healthy",
            last_check=datetime.now(),
            response_time=0.1
        )
        
        with self.collector.lock:
            self.collector.health_status["test-server"] = health
        
        status = self.collector.get_health_status()
        self.assertIn("test-server", status)
        self.assertEqual(status["test-server"].status, "healthy")
    
    def test_summary_stats(self):
        """Test summary statistics generation"""
        # Add some test metrics
        for i in range(5):
            self.collector.add_metric("test.value", i * 10)
        
        stats = self.collector.get_summary_stats()
        self.assertIn("test.value", stats)
        
        value_stats = stats["test.value"]
        self.assertEqual(value_stats["count"], 5)
        self.assertEqual(value_stats["min"], 0)
        self.assertEqual(value_stats["max"], 40)
        self.assertEqual(value_stats["avg"], 20)
    
    def test_metrics_export_json(self):
        """Test JSON export functionality"""
        self.collector.add_metric("test.export", 123, {"format": "json"})
        
        exported = self.collector.export_metrics("json")
        data = json.loads(exported)
        
        self.assertIn("metrics", data)
        self.assertIn("health", data)
        self.assertIn("summary", data)
        self.assertTrue(len(data["metrics"]) > 0)
    
    def test_metrics_export_prometheus(self):
        """Test Prometheus export functionality"""
        self.collector.add_metric("test.export", 456, {"format": "prometheus"})
        
        exported = self.collector.export_metrics("prometheus")
        
        self.assertIn("# HELP", exported)
        self.assertIn("# TYPE", exported)
        self.assertIn("notyyet_test_export", exported)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_system_metrics_collection(self, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection"""
        # Mock system metrics
        mock_cpu.return_value = 25.0
        mock_memory.return_value = MagicMock(percent=60.0, available=1000000)
        mock_disk.return_value = MagicMock(used=500000, total=1000000, free=500000)
        
        self.collector._collect_system_metrics()
        
        # Check that system metrics were collected
        metrics = self.collector.get_metrics(name_pattern="system.")
        metric_names = [m.name for m in metrics]
        
        self.assertIn("system.cpu.percent", metric_names)
        self.assertIn("system.memory.percent", metric_names)
        self.assertIn("system.disk.percent", metric_names)

@unittest.skipUnless(MONITORING_AVAILABLE, "Monitoring components not available")
class TestMonitoringMiddleware(unittest.TestCase):
    """Test cases for MonitoringMiddleware"""
    
    def setUp(self):
        """Set up test fixtures"""
        from flask import Flask
        self.app = Flask(__name__)
        self.middleware = MonitoringMiddleware(self.app)
        self.client = self.app.test_client()
        
        # Add test route
        @self.app.route('/test')
        def test_route():
            return {'message': 'test'}
    
    def test_middleware_initialization(self):
        """Test middleware initialization"""
        self.assertIsNotNone(self.middleware.metrics_collector)
        self.assertIn('MONITORING_MIDDLEWARE', self.app.config)
    
    def test_request_tracking(self):
        """Test that requests are tracked properly"""
        response = self.client.get('/test')
        self.assertEqual(response.status_code, 200)
        
        # Check that metrics were recorded
        collector = self.middleware.metrics_collector
        metrics = collector.get_metrics(name_pattern="http.")
        
        self.assertTrue(len(metrics) > 0)
        
        # Check for request start metric
        start_metrics = [m for m in metrics if "started" in m.name]
        self.assertTrue(len(start_metrics) > 0)
    
    def test_response_timing(self):
        """Test response time measurement"""
        response = self.client.get('/test')
        self.assertEqual(response.status_code, 200)
        
        # Check for timing headers
        self.assertIn('X-Response-Time', response.headers)
        self.assertIn('X-Request-ID', response.headers)
        
        # Verify timing is reasonable
        response_time = float(response.headers['X-Response-Time'])
        self.assertGreater(response_time, 0)
        self.assertLess(response_time, 1.0)  # Should be less than 1 second

@unittest.skipUnless(MONITORING_AVAILABLE, "Monitoring components not available")
class TestMonitoringDecorators(unittest.TestCase):
    """Test cases for monitoring decorators"""
    
    def setUp(self):
        """Set up test fixtures"""
        from monitoring.metrics_collector import init_metrics_collector
        self.collector = init_metrics_collector()
    
    def tearDown(self):
        """Clean up after tests"""
        if self.collector.is_running:
            self.collector.stop_collection()
    
    def test_function_monitoring_decorator(self):
        """Test function monitoring decorator"""
        @monitor_function("test_function")
        def test_func(x, y):
            time.sleep(0.1)  # Simulate work
            return x + y
        
        result = test_func(2, 3)
        self.assertEqual(result, 5)
        
        # Check that metrics were recorded
        metrics = self.collector.get_metrics(name_pattern="function.test_function")
        self.assertTrue(len(metrics) > 0)
        
        # Check for duration and call metrics
        duration_metrics = [m for m in metrics if "duration" in m.name]
        call_metrics = [m for m in metrics if "calls" in m.name]
        
        self.assertTrue(len(duration_metrics) > 0)
        self.assertTrue(len(call_metrics) > 0)
        
        # Verify duration is reasonable
        duration = duration_metrics[0].value
        self.assertGreater(duration, 0.05)  # At least 50ms due to sleep
        self.assertLess(duration, 1.0)      # Less than 1 second
    
    def test_tool_execution_decorator(self):
        """Test tool execution monitoring decorator"""
        @monitor_tool_execution("test_tool")
        def mock_tool_execution():
            time.sleep(0.05)
            return {
                "success": True,
                "return_code": 0,
                "stdout": "Test output",
                "stderr": ""
            }
        
        result = mock_tool_execution()
        self.assertTrue(result["success"])
        
        # Check that tool metrics were recorded
        metrics = self.collector.get_metrics(name_pattern="tool.test_tool")
        self.assertTrue(len(metrics) > 0)
        
        # Check for execution metrics
        execution_metrics = [m for m in metrics if "execution_time" in m.name]
        completed_metrics = [m for m in metrics if "completed" in m.name]
        
        self.assertTrue(len(execution_metrics) > 0)
        self.assertTrue(len(completed_metrics) > 0)

@unittest.skipUnless(MONITORING_AVAILABLE, "Monitoring components not available")
class TestLoggingComponents(unittest.TestCase):
    """Test cases for logging components"""
    
    def test_json_formatter(self):
        """Test JSON log formatter"""
        formatter = JSONFormatter("test-service")
        
        # Create a log record
        import logging
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        record.custom_field = "custom_value"
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["message"], "Test message")
        self.assertEqual(data["service"], "test-service")
        self.assertEqual(data["function"], "test_function")
        self.assertEqual(data["custom_field"], "custom_value")
        self.assertIn("timestamp", data)
        self.assertIn("location", data)
    
    def test_security_filter(self):
        """Test security filter for sensitive data"""
        security_filter = SecurityFilter()
        
        # Create log records with sensitive data
        import logging
        sensitive_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Login with password: secret123",
            args=(),
            exc_info=None
        )
        
        normal_record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Normal log message",
            args=(),
            exc_info=None
        )
        
        # Apply filter
        security_filter.filter(sensitive_record)
        security_filter.filter(normal_record)
        
        # Check results
        self.assertEqual(sensitive_record.msg, "[REDACTED - Contains sensitive information]")
        self.assertEqual(normal_record.msg, "Normal log message")

@unittest.skipUnless(MONITORING_AVAILABLE, "Monitoring components not available")
class TestDashboard(unittest.TestCase):
    """Test cases for monitoring dashboard"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.dashboard = MonitoringDashboard()
        self.client = self.dashboard.app.test_client()
    
    def test_dashboard_initialization(self):
        """Test dashboard initialization"""
        self.assertIsNotNone(self.dashboard.app)
        self.assertIsNotNone(self.dashboard.metrics_collector)
    
    def test_dashboard_routes(self):
        """Test dashboard API routes"""
        # Test main dashboard page
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Not-Yet Monitoring Dashboard', response.data)
        
        # Test API endpoints
        api_endpoints = ['/api/overview', '/api/metrics', '/api/health', '/api/servers', '/api/alerts']
        
        for endpoint in api_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIsInstance(data, dict)
    
    @patch('requests.get')
    def test_server_status_collection(self, mock_get):
        """Test server status collection"""
        # Mock server response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": 1234
        }
        mock_get.return_value = mock_response
        
        servers_data = self.dashboard._get_servers_data()
        
        self.assertIn('kali', servers_data)
        self.assertEqual(servers_data['kali']['status'], 'healthy')

class TestIntegration(unittest.TestCase):
    """Integration tests for monitoring system"""
    
    @unittest.skipUnless(MONITORING_AVAILABLE, "Monitoring components not available")
    def test_end_to_end_monitoring(self):
        """Test end-to-end monitoring workflow"""
        from flask import Flask
        from monitoring import MonitoringMiddleware, get_metrics_collector
        
        # Create Flask app with monitoring
        app = Flask(__name__)
        middleware = MonitoringMiddleware(app)
        client = app.test_client()
        
        @app.route('/test')
        def test_endpoint():
            return {'status': 'ok'}
        
        # Make request
        response = client.get('/test')
        self.assertEqual(response.status_code, 200)
        
        # Check metrics were collected
        collector = get_metrics_collector()
        metrics = collector.get_metrics(time_range=timedelta(minutes=1))
        
        self.assertTrue(len(metrics) > 0)
        
        # Check for HTTP metrics
        http_metrics = [m for m in metrics if 'http' in m.name]
        self.assertTrue(len(http_metrics) > 0)
        
        # Test export
        exported_json = collector.export_metrics('json')
        data = json.loads(exported_json)
        self.assertIn('metrics', data)
        
        # Cleanup
        collector.stop_collection()

def create_test_suite():
    """Create and return test suite"""
    suite = unittest.TestSuite()
    
    if MONITORING_AVAILABLE:
        # Add all test classes
        test_classes = [
            TestMetricsCollector,
            TestMonitoringMiddleware,
            TestMonitoringDecorators,
            TestLoggingComponents,
            TestDashboard,
            TestIntegration
        ]
        
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
    else:
        print("Skipping monitoring tests - components not available")
    
    return suite

if __name__ == '__main__':
    # Run tests
    if MONITORING_AVAILABLE:
        unittest.main(verbosity=2)
    else:
        print("Cannot run tests - monitoring components not available")
        print("Please install dependencies and ensure monitoring module is available")
        sys.exit(1)
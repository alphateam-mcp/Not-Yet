# Not-Yet Monitoring System Guide

## Overview

The Not-Yet monitoring system provides comprehensive observability for the security testing platform, including metrics collection, health monitoring, alerting, and a web-based dashboard.

## Features

### 🔍 **Metrics Collection**
- System resource monitoring (CPU, memory, disk, network)
- HTTP request tracking and performance metrics
- Security tool execution monitoring
- Custom application metrics
- Prometheus-compatible export

### 🏥 **Health Monitoring**
- Server health checks with automatic discovery
- Tool availability verification
- System resource threshold monitoring
- Custom health check registration

### 📊 **Web Dashboard**
- Real-time system overview
- Interactive metrics visualization
- Server status monitoring
- Alert management interface
- Historical data analysis

### 📝 **Enhanced Logging**
- Structured JSON logging
- Sensitive data redaction
- Contextual log enrichment
- Log aggregation capabilities
- Multiple output destinations

## Quick Start

### 1. Install Dependencies

```bash
# Install monitoring dependencies
pip install -r requirements-monitoring.txt

# Or install specific packages
pip install psutil flask requests pyyaml
```

### 2. Start Monitoring System

```bash
# Start all components (servers + monitoring)
python scripts/start_monitoring.py --start-all

# Or start components individually
python scripts/start_monitoring.py --start-servers
python scripts/start_monitoring.py --start-monitoring

# Interactive mode
python scripts/start_monitoring.py --interactive
```

### 3. Access Dashboard

Open your browser and navigate to:
```
http://localhost:8080
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │◄──►│   Dashboard     │
│                 │    │   (Port 8080)   │
└─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐
│  Kali Server    │◄──►│ Metrics         │
│  (Port 5000)    │    │ Collector       │
└─────────────────┘    └─────────────────┘
                                │
┌─────────────────┐            │
│ Perplexity      │◄───────────┘
│ Server          │
│ (Port 5050)     │
└─────────────────┘
```

## Components

### 1. MetricsCollector

**Purpose**: Core metrics collection and storage engine

**Key Features**:
- Automatic system metrics collection
- Server health monitoring
- Custom metric support
- Data export (JSON/Prometheus)
- Alert threshold checking

**Usage**:
```python
from monitoring import get_metrics_collector

collector = get_metrics_collector()

# Add custom metric
collector.add_metric("custom.counter", 1, {"source": "app"})

# Get metrics
metrics = collector.get_metrics(name_pattern="system.*")

# Export data
json_data = collector.export_metrics("json")
prometheus_data = collector.export_metrics("prometheus")
```

### 2. MonitoringMiddleware

**Purpose**: Flask middleware for automatic request tracking

**Key Features**:
- Automatic HTTP request/response monitoring
- Response time measurement
- Error tracking
- Request context enrichment

**Usage**:
```python
from flask import Flask
from monitoring import MonitoringMiddleware

app = Flask(__name__)
monitoring = MonitoringMiddleware(app)

# Middleware automatically tracks all requests
```

### 3. Monitoring Decorators

**Purpose**: Function and tool execution monitoring

**Key Features**:
- Function execution timing
- Tool execution tracking
- Error counting
- Success/failure metrics

**Usage**:
```python
from monitoring import monitor_function, monitor_tool_execution

@monitor_function("my_function")
def my_function():
    # Function implementation
    pass

@monitor_tool_execution("nmap")
def run_nmap_scan():
    # Tool execution
    return {"success": True, "output": "..."}
```

### 4. Health Check System

**Purpose**: Customizable health monitoring

**Key Features**:
- Built-in system checks
- Custom health check registration
- Threshold-based alerting
- Centralized health status

**Usage**:
```python
from monitoring import health_check, get_health_manager

@health_check("custom_service")
def check_custom_service():
    # Implement health check logic
    return {
        "healthy": True,
        "response_time": 0.1,
        "details": {"status": "operational"}
    }

# Get all health status
health_manager = get_health_manager()
status = health_manager.run_all_checks()
```

### 5. Enhanced Logging

**Purpose**: Structured logging with security features

**Key Features**:
- JSON log formatting
- Sensitive data redaction
- Contextual log enrichment
- Multiple output destinations

**Usage**:
```python
from monitoring.logging_config import setup_logging, get_contextual_logger

# Setup logging
logger = setup_logging("my-service", log_level="INFO")

# Use contextual logging
ctx_logger = get_contextual_logger("module", request_id="123")
ctx_logger.info("Processing request")
```

## Configuration

### Configuration File

Create `monitoring/config.yaml`:

```yaml
# Server endpoints
servers:
  kali:
    url: "http://localhost:5000"
    enabled: true
  perplexity:
    url: "http://localhost:5050"
    enabled: true

# Metrics settings
metrics:
  collection_interval: 30
  buffer_size: 10000
  retention_hours: 24

# Alert thresholds
alert_thresholds:
  cpu_percent: 80.0
  memory_percent: 85.0
  disk_percent: 90.0
  response_time: 5.0
  error_rate: 0.05

# Dashboard settings
dashboard:
  host: "0.0.0.0"
  port: 8080
  auto_refresh_interval: 30
```

### Environment Variables

```bash
# Monitoring configuration
export MONITORING_CONFIG_PATH="/path/to/config.yaml"
export MONITORING_LOG_LEVEL="INFO"
export MONITORING_DASHBOARD_PORT="8080"

# Server URLs
export KALI_SERVER_URL="http://localhost:5000"
export PERPLEXITY_SERVER_URL="http://localhost:5050"
```

## API Endpoints

### Health Check Endpoints

#### GET `/health`
Enhanced health check with monitoring integration.

**Response**:
```json
{
  "status": "healthy",
  "overall_healthy": true,
  "health_checks": {
    "tools_availability": {
      "healthy": true,
      "tools_status": {"nmap": true, "gobuster": true}
    },
    "system_resources": {
      "healthy": true,
      "cpu_percent": 25.5,
      "memory_percent": 60.2
    }
  },
  "server_info": {
    "version": "1.0.0",
    "uptime": 3600,
    "monitoring_enabled": true
  }
}
```

#### GET `/status`
Detailed server status information.

**Response**:
```json
{
  "server_name": "kali-server",
  "version": "1.0.0",
  "status": "running",
  "uptime": 3600,
  "monitoring_enabled": true,
  "metrics_summary": {...},
  "health_status": {...}
}
```

### Metrics Endpoints

#### GET `/metrics`
Prometheus-compatible metrics export.

**Parameters**:
- `format`: `prometheus` (default) or `json`

**Response** (Prometheus format):
```
# HELP notyyet_system_metrics System metrics from Not-Yet platform
# TYPE notyyet_system_metrics gauge
notyyet_system_cpu_percent{source="system"} 25.5
notyyet_system_memory_percent{source="system"} 60.2
notyyet_http_request_duration{method="GET",endpoint="health"} 0.045
```

### Dashboard API Endpoints

#### GET `/api/overview`
System overview for dashboard.

#### GET `/api/metrics`
Metrics data for charts.

#### GET `/api/health`
Health status for all servers.

#### GET `/api/servers`
Detailed server information.

#### GET `/api/alerts`
Active alerts and warnings.

## Monitoring Best Practices

### 1. Metric Naming

Use hierarchical naming with dots:
```
system.cpu.percent
http.request.duration
tool.nmap.execution_time
application.user.login_count
```

### 2. Tagging Strategy

Add relevant tags for filtering:
```python
collector.add_metric("http.request.duration", 0.1, {
    "method": "POST",
    "endpoint": "api/tools/nmap",
    "status_code": "200"
})
```

### 3. Health Check Design

Make health checks:
- **Fast**: Complete within 1-2 seconds
- **Reliable**: Don't depend on external services
- **Informative**: Provide actionable status information

```python
@health_check("database")
def check_database():
    try:
        # Quick database ping
        result = db.execute("SELECT 1")
        return {
            "healthy": True,
            "response_time": 0.05,
            "connection_pool": {"active": 5, "idle": 10}
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }
```

### 4. Alert Thresholds

Set appropriate thresholds:
- **CPU**: 80% for warning, 90% for critical
- **Memory**: 85% for warning, 95% for critical
- **Disk**: 90% for warning, 95% for critical
- **Response Time**: 2s for warning, 5s for critical
- **Error Rate**: 1% for warning, 5% for critical

## Troubleshooting

### Common Issues

#### 1. Monitoring Not Starting

```bash
# Check dependencies
python scripts/start_monitoring.py --check-deps

# Install missing dependencies
python scripts/start_monitoring.py --install-deps
```

#### 2. Dashboard Not Accessible

```bash
# Check if dashboard is running
curl http://localhost:8080/api/overview

# Check logs
tail -f logs/monitoring-manager.log
```

#### 3. Metrics Not Collecting

```python
# Verify metrics collector is running
from monitoring import get_metrics_collector
collector = get_metrics_collector()
print(f"Collector running: {collector.is_running}")

# Check recent metrics
metrics = collector.get_metrics(time_range=timedelta(minutes=5))
print(f"Recent metrics: {len(metrics)}")
```

#### 4. High Memory Usage

```bash
# Check metrics buffer size
grep "buffer_size" monitoring/config.yaml

# Reduce buffer size or retention period
metrics:
  buffer_size: 5000      # Reduced from 10000
  retention_hours: 12    # Reduced from 24
```

### Log Analysis

Check log files for issues:

```bash
# Application logs
tail -f logs/kali-server.log
tail -f logs/perplexity-server.log
tail -f logs/monitoring-manager.log

# Error logs
tail -f logs/kali-server-error.log
tail -f logs/perplexity-server-error.log

# Access logs
tail -f logs/kali-server-access.log
```

## Integration Examples

### 1. Prometheus Integration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'not-yet'
    static_configs:
      - targets: ['localhost:5000', 'localhost:5050']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### 2. Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Not-Yet Monitoring",
    "panels": [
      {
        "title": "System CPU",
        "type": "graph",
        "targets": [
          {
            "expr": "notyyet_system_cpu_percent"
          }
        ]
      }
    ]
  }
}
```

### 3. Custom Alerting

```python
from monitoring import get_metrics_collector

def check_custom_alerts():
    collector = get_metrics_collector()
    
    # Get recent metrics
    metrics = collector.get_metrics(time_range=timedelta(minutes=5))
    
    # Check for high error rate
    error_metrics = [m for m in metrics if 'error' in m.name]
    total_errors = sum(m.value for m in error_metrics)
    
    if total_errors > 10:
        send_alert(f"High error rate: {total_errors} errors in 5 minutes")
```

## Performance Optimization

### 1. Metrics Collection

- Adjust collection interval based on needs
- Use metric sampling for high-frequency events
- Implement metric aggregation for similar events

### 2. Memory Management

- Monitor buffer size and retention period
- Implement metric compression for long-term storage
- Use external storage for large datasets

### 3. Dashboard Performance

- Implement caching for expensive queries
- Use data aggregation for historical views
- Optimize chart refresh intervals

## Security Considerations

### 1. Sensitive Data

- Configure sensitive data patterns
- Review logs for exposed secrets
- Use secure log transmission

### 2. Access Control

- Implement authentication for dashboard
- Use HTTPS for production deployments
- Restrict access to monitoring endpoints

### 3. Network Security

- Bind services to localhost in development
- Use VPN or firewall rules in production
- Monitor for unusual access patterns

## Advanced Features

### 1. Custom Metrics

```python
# Business metrics
collector.add_metric("business.scans_completed", 1, {
    "tool": "nmap",
    "target_type": "web_server"
})

# Performance metrics
collector.add_metric("performance.scan_duration", 45.2, {
    "tool": "nikto",
    "target_size": "large"
})
```

### 2. Alerting Integration

```python
def setup_slack_alerts():
    from slack_sdk import WebClient
    
    def send_slack_alert(message):
        client = WebClient(token=os.environ['SLACK_TOKEN'])
        client.chat_postMessage(
            channel='#alerts',
            text=f"🚨 Not-Yet Alert: {message}"
        )
    
    # Register alert handler
    collector.alert_handlers.append(send_slack_alert)
```

### 3. Log Aggregation

```python
from monitoring.logging_config import LogAggregator

aggregator = LogAggregator("./logs")
aggregated_logs = aggregator.aggregate_logs("24h")

# Send to external system
import elasticsearch
es = elasticsearch.Elasticsearch()
es.index(index="not-yet-logs", body=aggregated_logs)
```

## Reference

### Configuration Reference

See [monitoring/config.yaml](monitoring/config.yaml) for complete configuration options.

### API Reference

See [API_REFERENCE.md](API_REFERENCE.md) for detailed API documentation.

### Development Guide

See [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) for development setup and contribution guidelines.
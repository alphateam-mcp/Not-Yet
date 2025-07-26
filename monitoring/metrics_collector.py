#!/usr/bin/env python3
"""
Metrics Collection System for Not-Yet Platform
Provides comprehensive monitoring and metrics collection for all servers.
"""

import time
import json
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import psutil
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

@dataclass
class ServerHealth:
    """Server health status"""
    server_name: str
    status: str  # healthy, unhealthy, unreachable
    last_check: datetime
    response_time: float
    error_message: Optional[str] = None
    tools_status: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.tools_status is None:
            self.tools_status = {}

@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    load_average: List[float]
    timestamp: datetime

class MetricsCollector:
    """Central metrics collection and storage system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.metrics_buffer = deque(maxlen=self.config.get('buffer_size', 10000))
        self.health_status = {}
        self.alert_thresholds = self.config.get('alert_thresholds', {})
        self.servers = self.config.get('servers', {})
        self.collection_interval = self.config.get('collection_interval', 30)
        self.is_running = False
        self.collection_thread = None
        self.lock = threading.Lock()
        
        # Performance tracking
        self.request_counts = defaultdict(int)
        self.response_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        
        logger.info("MetricsCollector initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            'servers': {
                'kali': {'url': 'http://localhost:5000', 'enabled': True},
                'perplexity': {'url': 'http://localhost:5050', 'enabled': True},
                'mcp': {'enabled': True}
            },
            'collection_interval': 30,
            'buffer_size': 10000,
            'alert_thresholds': {
                'cpu_percent': 80.0,
                'memory_percent': 85.0,
                'disk_percent': 90.0,
                'response_time': 5.0,
                'error_rate': 0.05
            },
            'metrics_retention_hours': 24
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def start_collection(self):
        """Start background metrics collection"""
        if self.is_running:
            logger.warning("Metrics collection already running")
            return
        
        self.is_running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        logger.info("Started metrics collection")
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Stopped metrics collection")
    
    def _collection_loop(self):
        """Main collection loop"""
        while self.is_running:
            try:
                self._collect_system_metrics()
                self._collect_server_health()
                self._cleanup_old_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                time.sleep(5)  # Short delay before retry
    
    def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.add_metric("system.cpu.percent", cpu_percent, {"source": "system"})
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.add_metric("system.memory.percent", memory.percent, {"source": "system"})
            self.add_metric("system.memory.available", memory.available, {"source": "system", "unit": "bytes"})
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.add_metric("system.disk.percent", disk_percent, {"source": "system"})
            self.add_metric("system.disk.free", disk.free, {"source": "system", "unit": "bytes"})
            
            # Network I/O
            network = psutil.net_io_counters()
            self.add_metric("system.network.bytes_sent", network.bytes_sent, {"source": "system", "unit": "bytes"})
            self.add_metric("system.network.bytes_recv", network.bytes_recv, {"source": "system", "unit": "bytes"})
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
                self.add_metric("system.load.1min", load_avg[0], {"source": "system"})
                self.add_metric("system.load.5min", load_avg[1], {"source": "system"})
                self.add_metric("system.load.15min", load_avg[2], {"source": "system"})
            except AttributeError:
                # Windows doesn't have load average
                pass
            
            # Process count
            process_count = len(psutil.pids())
            self.add_metric("system.process.count", process_count, {"source": "system"})
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_server_health(self):
        """Check health of all configured servers"""
        for server_name, server_config in self.servers.items():
            if not server_config.get('enabled', True):
                continue
            
            self._check_server_health(server_name, server_config)
    
    def _check_server_health(self, server_name: str, server_config: Dict[str, Any]):
        """Check health of a specific server"""
        if server_name == 'mcp':
            # MCP server doesn't have HTTP endpoint, just mark as healthy if process exists
            health = ServerHealth(
                server_name=server_name,
                status="healthy",
                last_check=datetime.now(),
                response_time=0.0
            )
        else:
            health = self._http_health_check(server_name, server_config['url'])
        
        with self.lock:
            self.health_status[server_name] = health
        
        # Record health metrics
        status_value = 1.0 if health.status == "healthy" else 0.0
        self.add_metric(f"server.{server_name}.health", status_value, {"server": server_name})
        self.add_metric(f"server.{server_name}.response_time", health.response_time, {"server": server_name, "unit": "seconds"})
    
    def _http_health_check(self, server_name: str, url: str) -> ServerHealth:
        """Perform HTTP health check"""
        start_time = time.time()
        
        try:
            response = requests.get(f"{url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                tools_status = data.get('tools_status', {})
                
                status = "healthy" if data.get('status') in ['healthy', 'ok'] else "unhealthy"
                
                return ServerHealth(
                    server_name=server_name,
                    status=status,
                    last_check=datetime.now(),
                    response_time=response_time,
                    tools_status=tools_status
                )
            else:
                return ServerHealth(
                    server_name=server_name,
                    status="unhealthy",
                    last_check=datetime.now(),
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}"
                )
                
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            return ServerHealth(
                server_name=server_name,
                status="unreachable",
                last_check=datetime.now(),
                response_time=response_time,
                error_message=str(e)
            )
    
    def add_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Add a metric to the collection"""
        metric = Metric(name=name, value=value, timestamp=datetime.now(), tags=tags or {})
        
        with self.lock:
            self.metrics_buffer.append(metric)
        
        # Check for alerts
        self._check_alerts(metric)
    
    def _check_alerts(self, metric: Metric):
        """Check if metric exceeds alert thresholds"""
        metric_key = metric.name.split('.')[-1]  # Get last part of metric name
        threshold = self.alert_thresholds.get(metric_key)
        
        if threshold and metric.value > threshold:
            logger.warning(f"ALERT: {metric.name} = {metric.value} exceeds threshold {threshold}")
            # In a real implementation, you'd send alerts here
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.config.get('metrics_retention_hours', 24))
        
        with self.lock:
            # Find first metric newer than cutoff
            start_index = 0
            for i, metric in enumerate(self.metrics_buffer):
                if metric.timestamp >= cutoff_time:
                    start_index = i
                    break
            
            # Remove old metrics
            if start_index > 0:
                for _ in range(start_index):
                    self.metrics_buffer.popleft()
    
    def get_metrics(self, name_pattern: Optional[str] = None, 
                   time_range: Optional[timedelta] = None) -> List[Metric]:
        """Get metrics matching pattern and time range"""
        cutoff_time = datetime.now() - (time_range or timedelta(hours=1))
        
        with self.lock:
            filtered_metrics = []
            for metric in self.metrics_buffer:
                if metric.timestamp < cutoff_time:
                    continue
                
                if name_pattern and name_pattern not in metric.name:
                    continue
                
                filtered_metrics.append(metric)
        
        return filtered_metrics
    
    def get_health_status(self) -> Dict[str, ServerHealth]:
        """Get current health status of all servers"""
        with self.lock:
            return self.health_status.copy()
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        with self.lock:
            recent_metrics = [m for m in self.metrics_buffer 
                            if m.timestamp >= datetime.now() - timedelta(minutes=5)]
        
        if not recent_metrics:
            return {}
        
        # Group metrics by name
        metric_groups = defaultdict(list)
        for metric in recent_metrics:
            metric_groups[metric.name].append(metric.value)
        
        # Calculate statistics
        stats = {}
        for name, values in metric_groups.items():
            if values:
                stats[name] = {
                    'count': len(values),
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'latest': values[-1]
                }
        
        return stats
    
    def record_request(self, endpoint: str, response_time: float, status_code: int):
        """Record API request metrics"""
        self.request_counts[endpoint] += 1
        self.response_times[endpoint].append(response_time)
        
        if status_code >= 400:
            self.error_counts[endpoint] += 1
        
        # Add to metrics buffer
        self.add_metric(f"api.{endpoint}.response_time", response_time, 
                       {"endpoint": endpoint, "status": str(status_code)})
        self.add_metric(f"api.{endpoint}.requests", 1, {"endpoint": endpoint})
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        if format == "json":
            return self._export_json()
        elif format == "prometheus":
            return self._export_prometheus()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self) -> str:
        """Export metrics as JSON"""
        metrics_data = []
        
        with self.lock:
            for metric in self.metrics_buffer:
                metrics_data.append({
                    'name': metric.name,
                    'value': metric.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'tags': metric.tags
                })
        
        health_data = {}
        for name, health in self.health_status.items():
            health_data[name] = asdict(health)
            health_data[name]['last_check'] = health.last_check.isoformat()
        
        return json.dumps({
            'metrics': metrics_data,
            'health': health_data,
            'summary': self.get_summary_stats(),
            'exported_at': datetime.now().isoformat()
        }, indent=2)
    
    def _export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        lines.append("# HELP notyyet_system_metrics System metrics from Not-Yet platform")
        lines.append("# TYPE notyyet_system_metrics gauge")
        
        with self.lock:
            # Group metrics by name for latest values
            latest_metrics = {}
            for metric in reversed(self.metrics_buffer):
                if metric.name not in latest_metrics:
                    latest_metrics[metric.name] = metric
        
        for metric in latest_metrics.values():
            metric_name = metric.name.replace('.', '_').replace('-', '_')
            tags_str = ','.join([f'{k}="{v}"' for k, v in metric.tags.items()])
            if tags_str:
                tags_str = '{' + tags_str + '}'
            
            lines.append(f"notyyet_{metric_name}{tags_str} {metric.value}")
        
        return '\n'.join(lines)

# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
        _metrics_collector.start_collection()
    return _metrics_collector

def init_metrics_collector(config_path: Optional[str] = None) -> MetricsCollector:
    """Initialize the global metrics collector"""
    global _metrics_collector
    if _metrics_collector:
        _metrics_collector.stop_collection()
    
    _metrics_collector = MetricsCollector(config_path)
    _metrics_collector.start_collection()
    return _metrics_collector
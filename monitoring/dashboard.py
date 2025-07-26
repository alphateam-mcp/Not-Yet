#!/usr/bin/env python3
"""
System Status Dashboard for Not-Yet Platform
Web-based dashboard for monitoring system health and metrics.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from flask import Flask, render_template_string, jsonify, request
import requests

from .metrics_collector import get_metrics_collector

class MonitoringDashboard:
    """Web dashboard for system monitoring"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.app = Flask(__name__)
        self.metrics_collector = get_metrics_collector()
        self._setup_routes()
        
        # Server endpoints to monitor
        self.servers = {
            'kali': self.config.get('kali_url', 'http://localhost:5000'),
            'perplexity': self.config.get('perplexity_url', 'http://localhost:5050')
        }
    
    def _setup_routes(self):
        """Setup Flask routes for the dashboard"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template_string(DASHBOARD_TEMPLATE)
        
        @self.app.route('/api/overview')
        def api_overview():
            """System overview API endpoint"""
            try:
                overview_data = self._get_system_overview()
                return jsonify(overview_data)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """Metrics API endpoint"""
            try:
                time_range = request.args.get('range', '1h')
                metrics_data = self._get_metrics_data(time_range)
                return jsonify(metrics_data)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/health')
        def api_health():
            """Health status API endpoint"""
            try:
                health_data = self._get_health_data()
                return jsonify(health_data)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/servers')
        def api_servers():
            """Server status API endpoint"""
            try:
                servers_data = self._get_servers_data()
                return jsonify(servers_data)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/alerts')
        def api_alerts():
            """Active alerts API endpoint"""
            try:
                alerts_data = self._get_alerts_data()
                return jsonify(alerts_data)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _get_system_overview(self) -> Dict[str, Any]:
        """Get system overview data"""
        # Get recent metrics
        recent_metrics = self.metrics_collector.get_metrics(
            time_range=timedelta(minutes=5)
        )
        
        # Calculate overview stats
        overview = {
            'total_requests': 0,
            'avg_response_time': 0,
            'error_rate': 0,
            'system_health': 'unknown',
            'active_servers': 0,
            'total_servers': len(self.servers),
            'last_updated': datetime.now().isoformat()
        }
        
        # Process metrics
        request_metrics = [m for m in recent_metrics if 'requests' in m.name]
        response_time_metrics = [m for m in recent_metrics if 'response_time' in m.name or 'duration' in m.name]
        error_metrics = [m for m in recent_metrics if 'error' in m.name]
        
        overview['total_requests'] = sum(m.value for m in request_metrics)
        
        if response_time_metrics:
            overview['avg_response_time'] = sum(m.value for m in response_time_metrics) / len(response_time_metrics)
        
        total_errors = sum(m.value for m in error_metrics)
        if overview['total_requests'] > 0:
            overview['error_rate'] = total_errors / overview['total_requests']
        
        # Check server health
        health_status = self.metrics_collector.get_health_status()
        healthy_servers = sum(1 for h in health_status.values() if h.status == 'healthy')
        overview['active_servers'] = healthy_servers
        
        if healthy_servers == len(self.servers):
            overview['system_health'] = 'healthy'
        elif healthy_servers > 0:
            overview['system_health'] = 'degraded'
        else:
            overview['system_health'] = 'unhealthy'
        
        return overview
    
    def _get_metrics_data(self, time_range: str) -> Dict[str, Any]:
        """Get metrics data for specified time range"""
        # Parse time range
        range_mapping = {
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6),
            '24h': timedelta(hours=24)
        }
        
        delta = range_mapping.get(time_range, timedelta(hours=1))
        metrics = self.metrics_collector.get_metrics(time_range=delta)
        
        # Group metrics by type
        grouped_metrics = {
            'system': [],
            'http': [],
            'tools': [],
            'errors': []
        }
        
        for metric in metrics:
            if metric.name.startswith('system.'):
                grouped_metrics['system'].append({
                    'name': metric.name,
                    'value': metric.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'tags': metric.tags
                })
            elif metric.name.startswith('http.') or 'response_time' in metric.name:
                grouped_metrics['http'].append({
                    'name': metric.name,
                    'value': metric.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'tags': metric.tags
                })
            elif metric.name.startswith('tool.'):
                grouped_metrics['tools'].append({
                    'name': metric.name,
                    'value': metric.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'tags': metric.tags
                })
            elif 'error' in metric.name:
                grouped_metrics['errors'].append({
                    'name': metric.name,
                    'value': metric.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'tags': metric.tags
                })
        
        return {
            'time_range': time_range,
            'metrics': grouped_metrics,
            'total_count': len(metrics)
        }
    
    def _get_health_data(self) -> Dict[str, Any]:
        """Get health check data"""
        health_status = self.metrics_collector.get_health_status()
        
        health_data = {
            'overall_status': 'healthy',
            'servers': {},
            'last_updated': datetime.now().isoformat()
        }
        
        unhealthy_count = 0
        for server_name, health in health_status.items():
            health_data['servers'][server_name] = {
                'status': health.status,
                'last_check': health.last_check.isoformat(),
                'response_time': health.response_time,
                'error_message': health.error_message,
                'tools_status': health.tools_status
            }
            
            if health.status != 'healthy':
                unhealthy_count += 1
        
        if unhealthy_count == len(health_status):
            health_data['overall_status'] = 'unhealthy'
        elif unhealthy_count > 0:
            health_data['overall_status'] = 'degraded'
        
        return health_data
    
    def _get_servers_data(self) -> Dict[str, Any]:
        """Get detailed server information"""
        servers_data = {}
        
        for server_name, server_url in self.servers.items():
            try:
                # Try to get server status
                response = requests.get(f"{server_url}/status", timeout=5)
                if response.status_code == 200:
                    servers_data[server_name] = response.json()
                else:
                    servers_data[server_name] = {
                        'error': f"HTTP {response.status_code}",
                        'status': 'unreachable'
                    }
            except requests.RequestException as e:
                servers_data[server_name] = {
                    'error': str(e),
                    'status': 'unreachable'
                }
        
        return servers_data
    
    def _get_alerts_data(self) -> Dict[str, Any]:
        """Get active alerts data"""
        # This is a simplified implementation
        # In a real system, you'd have an alerting system
        alerts = []
        
        # Check for high error rates
        recent_metrics = self.metrics_collector.get_metrics(
            time_range=timedelta(minutes=10)
        )
        
        error_metrics = [m for m in recent_metrics if 'error' in m.name]
        request_metrics = [m for m in recent_metrics if 'requests' in m.name]
        
        total_errors = sum(m.value for m in error_metrics)
        total_requests = sum(m.value for m in request_metrics)
        
        if total_requests > 0:
            error_rate = total_errors / total_requests
            if error_rate > 0.05:  # 5% error rate threshold
                alerts.append({
                    'severity': 'warning',
                    'message': f'High error rate: {error_rate:.2%}',
                    'timestamp': datetime.now().isoformat()
                })
        
        # Check system resources
        system_metrics = [m for m in recent_metrics if m.name.startswith('system.')]
        for metric in system_metrics:
            if 'cpu' in metric.name and metric.value > 90:
                alerts.append({
                    'severity': 'critical',
                    'message': f'High CPU usage: {metric.value:.1f}%',
                    'timestamp': metric.timestamp.isoformat()
                })
            elif 'memory' in metric.name and metric.value > 90:
                alerts.append({
                    'severity': 'critical',
                    'message': f'High memory usage: {metric.value:.1f}%',
                    'timestamp': metric.timestamp.isoformat()
                })
        
        return {
            'alerts': alerts,
            'count': len(alerts)
        }
    
    def run(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """Run the dashboard server"""
        print(f"Starting monitoring dashboard on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# HTML template for the dashboard
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Not-Yet Monitoring Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 1.8rem;
            font-weight: 600;
        }
        
        .header p {
            opacity: 0.9;
            margin-top: 0.5rem;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #e1e5e9;
        }
        
        .card h3 {
            color: #2c3e50;
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-healthy { background-color: #27ae60; }
        .status-degraded { background-color: #f39c12; }
        .status-unhealthy { background-color: #e74c3c; }
        .status-unknown { background-color: #95a5a6; }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid #ecf0f1;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-value {
            font-weight: 600;
            color: #2c3e50;
        }
        
        .server-list {
            list-style: none;
        }
        
        .server-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid #ecf0f1;
        }
        
        .server-item:last-child {
            border-bottom: none;
        }
        
        .alert {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 0.75rem;
            border-radius: 4px;
            margin-bottom: 0.5rem;
        }
        
        .alert.critical {
            background-color: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }
        
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        .refresh-btn:hover {
            background: #5a6fd8;
        }
        
        .loading {
            opacity: 0.6;
            pointer-events: none;
        }
        
        .last-updated {
            font-size: 0.8rem;
            color: #7f8c8d;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Not-Yet Monitoring Dashboard</h1>
        <p>Real-time monitoring for security testing platform</p>
    </div>
    
    <div class="container">
        <!-- System Overview -->
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3>System Overview</h3>
                <button class="refresh-btn" onclick="refreshDashboard()">Refresh</button>
            </div>
            <div id="overview-content">
                <div class="metric">
                    <span>System Health</span>
                    <span id="system-health">
                        <span class="status-indicator status-unknown"></span>
                        Loading...
                    </span>
                </div>
                <div class="metric">
                    <span>Active Servers</span>
                    <span class="metric-value" id="active-servers">-/-</span>
                </div>
                <div class="metric">
                    <span>Total Requests (5m)</span>
                    <span class="metric-value" id="total-requests">-</span>
                </div>
                <div class="metric">
                    <span>Avg Response Time</span>
                    <span class="metric-value" id="avg-response-time">-</span>
                </div>
                <div class="metric">
                    <span>Error Rate</span>
                    <span class="metric-value" id="error-rate">-</span>
                </div>
            </div>
        </div>
        
        <div class="grid">
            <!-- Server Status -->
            <div class="card">
                <h3>Server Status</h3>
                <ul class="server-list" id="server-list">
                    <li class="server-item">Loading server information...</li>
                </ul>
            </div>
            
            <!-- Active Alerts -->
            <div class="card">
                <h3>Active Alerts</h3>
                <div id="alerts-content">
                    <p>Loading alerts...</p>
                </div>
            </div>
        </div>
        
        <div class="last-updated" id="last-updated">
            Last updated: Loading...
        </div>
    </div>
    
    <script>
        let refreshInterval;
        
        function refreshDashboard() {
            loadOverview();
            loadServers();
            loadAlerts();
            updateLastUpdated();
        }
        
        function loadOverview() {
            fetch('/api/overview')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('system-health').innerHTML = 
                        `<span class="status-indicator status-${data.system_health}"></span>${data.system_health}`;
                    document.getElementById('active-servers').textContent = 
                        `${data.active_servers}/${data.total_servers}`;
                    document.getElementById('total-requests').textContent = data.total_requests;
                    document.getElementById('avg-response-time').textContent = 
                        `${(data.avg_response_time * 1000).toFixed(1)}ms`;
                    document.getElementById('error-rate').textContent = 
                        `${(data.error_rate * 100).toFixed(2)}%`;
                })
                .catch(error => console.error('Error loading overview:', error));
        }
        
        function loadServers() {
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {
                    const serverList = document.getElementById('server-list');
                    serverList.innerHTML = '';
                    
                    for (const [serverName, serverData] of Object.entries(data.servers)) {
                        const li = document.createElement('li');
                        li.className = 'server-item';
                        li.innerHTML = `
                            <span>
                                <span class="status-indicator status-${serverData.status}"></span>
                                ${serverName}
                            </span>
                            <span>${serverData.response_time ? (serverData.response_time * 1000).toFixed(1) + 'ms' : '-'}</span>
                        `;
                        serverList.appendChild(li);
                    }
                })
                .catch(error => console.error('Error loading servers:', error));
        }
        
        function loadAlerts() {
            fetch('/api/alerts')
                .then(response => response.json())
                .then(data => {
                    const alertsContent = document.getElementById('alerts-content');
                    
                    if (data.alerts.length === 0) {
                        alertsContent.innerHTML = '<p style="color: #27ae60;">No active alerts</p>';
                    } else {
                        alertsContent.innerHTML = data.alerts.map(alert => 
                            `<div class="alert ${alert.severity}">${alert.message}</div>`
                        ).join('');
                    }
                })
                .catch(error => console.error('Error loading alerts:', error));
        }
        
        function updateLastUpdated() {
            document.getElementById('last-updated').textContent = 
                'Last updated: ' + new Date().toLocaleString();
        }
        
        // Initial load
        refreshDashboard();
        
        // Auto-refresh every 30 seconds
        refreshInterval = setInterval(refreshDashboard, 30000);
        
        // Refresh on visibility change
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden) {
                refreshDashboard();
            }
        });
    </script>
</body>
</html>
'''

def create_dashboard(config: Optional[Dict[str, Any]] = None) -> MonitoringDashboard:
    """Create and return a monitoring dashboard instance"""
    return MonitoringDashboard(config)

if __name__ == '__main__':
    dashboard = create_dashboard()
    dashboard.run(debug=True)
#!/usr/bin/env python3
"""
Start Monitoring Script for Not-Yet Platform
Comprehensive script to start all monitoring components.
"""

import os
import sys
import time
import signal
import subprocess
import threading
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from monitoring import init_metrics_collector, create_dashboard, setup_development_logging
    from monitoring.logging_config import setup_logging
    MONITORING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Monitoring components not available: {e}")
    MONITORING_AVAILABLE = False

class MonitoringManager:
    """Manages all monitoring components"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.processes = {}
        self.threads = {}
        self.running = False
        self.logger = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down...")
        self.stop_all()
        sys.exit(0)
    
    def setup_logging(self, log_level: str = "INFO"):
        """Setup logging for the monitoring system"""
        if MONITORING_AVAILABLE:
            self.logger = setup_logging(
                service_name="monitoring-manager",
                log_level=log_level,
                enable_json=False,
                enable_console=True
            )
        else:
            import logging
            logging.basicConfig(level=getattr(logging, log_level.upper()))
            self.logger = logging.getLogger("monitoring-manager")
    
    def start_servers(self, start_kali: bool = True, start_perplexity: bool = True):
        """Start the main application servers"""
        self.logger.info("Starting application servers...")
        
        if start_kali:
            self._start_server("kali", "kali_server.py", 5000)
        
        if start_perplexity:
            self._start_server("perplexity", "perplexity_server.py", 5050)
        
        # Wait for servers to start
        time.sleep(5)
        self._verify_servers()
    
    def _start_server(self, name: str, script: str, port: int):
        """Start a single server"""
        script_path = project_root / script
        
        if not script_path.exists():
            self.logger.error(f"Server script not found: {script_path}")
            return
        
        try:
            env = os.environ.copy()
            env['PYTHONPATH'] = str(project_root)
            
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=project_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes[name] = {
                'process': process,
                'port': port,
                'script': script
            }
            
            self.logger.info(f"Started {name} server (PID: {process.pid}) on port {port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start {name} server: {e}")
    
    def _verify_servers(self):
        """Verify that servers are running and responding"""
        import requests
        
        for name, info in self.processes.items():
            port = info['port']
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=10)
                if response.status_code == 200:
                    self.logger.info(f"✓ {name} server is healthy")
                else:
                    self.logger.warning(f"⚠ {name} server returned status {response.status_code}")
            except requests.RequestException as e:
                self.logger.error(f"✗ {name} server health check failed: {e}")
    
    def start_monitoring(self):
        """Start monitoring components"""
        if not MONITORING_AVAILABLE:
            self.logger.warning("Monitoring components not available, skipping")
            return
        
        self.logger.info("Starting monitoring components...")
        
        # Initialize metrics collector
        try:
            metrics_collector = init_metrics_collector(self.config_path)
            self.logger.info("✓ Metrics collector started")
        except Exception as e:
            self.logger.error(f"Failed to start metrics collector: {e}")
            return
        
        # Start dashboard in a separate thread
        try:
            dashboard = create_dashboard()
            dashboard_thread = threading.Thread(
                target=dashboard.run,
                kwargs={'host': '0.0.0.0', 'port': 8080, 'debug': False},
                daemon=True
            )
            dashboard_thread.start()
            self.threads['dashboard'] = dashboard_thread
            self.logger.info("✓ Monitoring dashboard started on http://localhost:8080")
        except Exception as e:
            self.logger.error(f"Failed to start dashboard: {e}")
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if all required dependencies are available"""
        dependencies = {
            'python': True,
            'monitoring_module': MONITORING_AVAILABLE,
            'flask': False,
            'requests': False,
            'psutil': False
        }
        
        # Check Python modules
        modules_to_check = ['flask', 'requests', 'psutil']
        for module in modules_to_check:
            try:
                __import__(module)
                dependencies[module] = True
            except ImportError:
                dependencies[module] = False
        
        return dependencies
    
    def install_dependencies(self):
        """Install missing dependencies"""
        self.logger.info("Installing dependencies...")
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                'flask', 'requests', 'psutil', 'aiohttp'
            ])
            self.logger.info("✓ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install dependencies: {e}")
    
    def generate_status_report(self) -> Dict[str, Any]:
        """Generate a status report"""
        report = {
            'timestamp': time.time(),
            'monitoring_available': MONITORING_AVAILABLE,
            'servers': {},
            'dependencies': self.check_dependencies(),
            'processes': {}
        }
        
        # Check server processes
        for name, info in self.processes.items():
            process = info['process']
            report['processes'][name] = {
                'pid': process.pid,
                'running': process.poll() is None,
                'port': info['port']
            }
        
        # Check server health
        import requests
        for name, info in self.processes.items():
            try:
                response = requests.get(
                    f"http://localhost:{info['port']}/health", 
                    timeout=5
                )
                report['servers'][name] = {
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'response_time': response.elapsed.total_seconds(),
                    'data': response.json() if response.status_code == 200 else None
                }
            except Exception as e:
                report['servers'][name] = {
                    'status': 'unreachable',
                    'error': str(e)
                }
        
        return report
    
    def print_status(self):
        """Print current system status"""
        report = self.generate_status_report()
        
        print("\n" + "="*60)
        print("NOT-YET MONITORING SYSTEM STATUS")
        print("="*60)
        
        print(f"\nMonitoring Available: {'✓' if report['monitoring_available'] else '✗'}")
        
        print("\nDependencies:")
        for dep, available in report['dependencies'].items():
            status = '✓' if available else '✗'
            print(f"  {status} {dep}")
        
        print("\nServer Processes:")
        for name, info in report['processes'].items():
            status = '✓' if info['running'] else '✗'
            print(f"  {status} {name} (PID: {info['pid']}, Port: {info['port']})")
        
        print("\nServer Health:")
        for name, info in report['servers'].items():
            if info['status'] == 'healthy':
                print(f"  ✓ {name} - {info['response_time']:.3f}s")
            elif info['status'] == 'unhealthy':
                print(f"  ⚠ {name} - Unhealthy")
            else:
                print(f"  ✗ {name} - {info.get('error', 'Unknown error')}")
        
        if report['monitoring_available']:
            print(f"\nDashboard: http://localhost:8080")
        
        print("\n" + "="*60)
    
    def stop_all(self):
        """Stop all running components"""
        self.logger.info("Stopping all components...")
        
        # Stop server processes
        for name, info in self.processes.items():
            process = info['process']
            if process.poll() is None:  # Process is still running
                self.logger.info(f"Stopping {name} server...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    self.logger.info(f"✓ {name} server stopped")
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Force killing {name} server...")
                    process.kill()
        
        # Stop monitoring components
        if MONITORING_AVAILABLE:
            try:
                from monitoring import get_metrics_collector
                collector = get_metrics_collector()
                collector.stop_collection()
                self.logger.info("✓ Metrics collector stopped")
            except Exception as e:
                self.logger.error(f"Error stopping metrics collector: {e}")
        
        self.running = False
    
    def run_interactive(self):
        """Run in interactive mode"""
        self.running = True
        
        try:
            while self.running:
                print("\nNot-Yet Monitoring System")
                print("1. Start all servers")
                print("2. Start monitoring only")
                print("3. Show status")
                print("4. Install dependencies")
                print("5. Stop all")
                print("6. Exit")
                
                choice = input("\nEnter choice (1-6): ").strip()
                
                if choice == '1':
                    self.start_servers()
                    self.start_monitoring()
                elif choice == '2':
                    self.start_monitoring()
                elif choice == '3':
                    self.print_status()
                elif choice == '4':
                    self.install_dependencies()
                elif choice == '5':
                    self.stop_all()
                elif choice == '6':
                    self.stop_all()
                    break
                else:
                    print("Invalid choice")
                
                if choice in ['1', '2']:
                    input("\nPress Enter to continue...")
                    
        except KeyboardInterrupt:
            self.stop_all()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Not-Yet Monitoring System Manager")
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies and exit')
    parser.add_argument('--install-deps', action='store_true', help='Install dependencies and exit')
    parser.add_argument('--start-all', action='store_true', help='Start all components')
    parser.add_argument('--start-servers', action='store_true', help='Start servers only')
    parser.add_argument('--start-monitoring', action='store_true', help='Start monitoring only')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    parser.add_argument('--dashboard-only', action='store_true', help='Start dashboard only')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    args = parser.parse_args()
    
    # Create manager
    manager = MonitoringManager(args.config)
    manager.setup_logging(args.log_level)
    
    try:
        if args.check_deps:
            deps = manager.check_dependencies()
            print("Dependencies:")
            for dep, available in deps.items():
                status = '✓' if available else '✗'
                print(f"  {status} {dep}")
            sys.exit(0 if all(deps.values()) else 1)
        
        elif args.install_deps:
            manager.install_dependencies()
            sys.exit(0)
        
        elif args.status:
            manager.print_status()
            sys.exit(0)
        
        elif args.start_all:
            manager.start_servers()
            manager.start_monitoring()
            print("\nAll components started. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.stop_all()
        
        elif args.start_servers:
            manager.start_servers()
            print("\nServers started. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.stop_all()
        
        elif args.start_monitoring:
            manager.start_monitoring()
            print("\nMonitoring started. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.stop_all()
        
        elif args.dashboard_only:
            if MONITORING_AVAILABLE:
                dashboard = create_dashboard()
                print("Starting dashboard on http://localhost:8080")
                dashboard.run(host='0.0.0.0', port=8080, debug=True)
            else:
                print("Error: Monitoring components not available")
                sys.exit(1)
        
        elif args.interactive:
            manager.run_interactive()
        
        else:
            print("No action specified. Use --help for options or --interactive for interactive mode.")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
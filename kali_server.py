#!/usr/bin/env python3

# This script connect the MCP AI agent to Kali Linux terminal and API Server.

# some of the code here was inspired from https://github.com/whit3rabbit0/project_astro , be sure to check them out

import argparse
import json
import logging
import os
import subprocess
import sys
import traceback
import threading
from typing import Dict, Any
from flask import Flask, request, jsonify

# Import monitoring components
try:
    from monitoring.middleware import MonitoringMiddleware, monitor_tool_execution, get_health_manager, health_check
    from monitoring.metrics_collector import get_metrics_collector
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    logger.warning("Monitoring components not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.environ.get("API_PORT", 5000))
DEBUG_MODE = os.environ.get("DEBUG_MODE", "0").lower() in ("1", "true", "yes", "y")
COMMAND_TIMEOUT = 3600  # 5 minutes default timeout

app = Flask(__name__)

# Initialize monitoring if available
if MONITORING_AVAILABLE:
    monitoring = MonitoringMiddleware(app)
    metrics_collector = get_metrics_collector()
    health_manager = get_health_manager()
    logger.info("Monitoring enabled")
else:
    monitoring = None
    metrics_collector = None
    health_manager = None

class CommandExecutor:
    """Class to handle command execution with better timeout management"""
    
    def __init__(self, command: str, timeout: int = COMMAND_TIMEOUT):
        self.command = command
        self.timeout = timeout
        self.process = None
        self.stdout_data = ""
        self.stderr_data = ""
        self.stdout_thread = None
        self.stderr_thread = None
        self.return_code = None
        self.timed_out = False
    
    def _read_stdout(self):
        """Thread function to continuously read stdout"""
        for line in iter(self.process.stdout.readline, ''):
            self.stdout_data += line
    
    def _read_stderr(self):
        """Thread function to continuously read stderr"""
        for line in iter(self.process.stderr.readline, ''):
            self.stderr_data += line
    
    def execute(self) -> Dict[str, Any]:
        """Execute the command and handle timeout gracefully"""
        logger.info(f"Executing command: {self.command}")
        
        try:
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Start threads to read output continuously
            self.stdout_thread = threading.Thread(target=self._read_stdout)
            self.stderr_thread = threading.Thread(target=self._read_stderr)
            self.stdout_thread.daemon = True
            self.stderr_thread.daemon = True
            self.stdout_thread.start()
            self.stderr_thread.start()
            
            # Wait for the process to complete or timeout
            try:
                self.return_code = self.process.wait(timeout=self.timeout)
                # Process completed, join the threads
                self.stdout_thread.join()
                self.stderr_thread.join()
            except subprocess.TimeoutExpired:
                # Process timed out but we might have partial results
                self.timed_out = True
                logger.warning(f"Command timed out after {self.timeout} seconds. Terminating process.")
                
                # Try to terminate gracefully first
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)  # Give it 5 seconds to terminate
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    logger.warning("Process not responding to termination. Killing.")
                    self.process.kill()
                
                # Update final output
                self.return_code = -1
            
            # Always consider it a success if we have output, even with timeout
            success = True if self.timed_out and (self.stdout_data or self.stderr_data) else (self.return_code == 0)
            
            return {
                "stdout": self.stdout_data,
                "stderr": self.stderr_data,
                "return_code": self.return_code,
                "success": success,
                "timed_out": self.timed_out,
                "partial_results": self.timed_out and (self.stdout_data or self.stderr_data)
            }
        
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "stdout": self.stdout_data,
                "stderr": f"Error executing command: {str(e)}\n{self.stderr_data}",
                "return_code": -1,
                "success": False,
                "timed_out": False,
                "partial_results": bool(self.stdout_data or self.stderr_data)
            }


def execute_command(command: str) -> Dict[str, Any]:
    """
    Execute a shell command and return the result
    
    Args:
        command: The command to execute
        
    Returns:
        A dictionary containing the stdout, stderr, and return code
    """
    executor = CommandExecutor(command)
    return executor.execute()


@app.route("/api/command", methods=["POST"])
def generic_command():
    """Execute any command provided in the request."""
    try:
        params = request.json
        command = params.get("command", "")
        
        if not command:
            logger.warning("Command endpoint called without command parameter")
            return jsonify({
                "error": "Command parameter is required"
            }), 400
        
        result = execute_command(command)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in command endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
        
@app.route("/api/tools/curl", methods=["POST"])
def curl():
    try:
        params = request.json
        target = params.get("target", "")
        
        if not target:
            logger.warning("Curl called without target parameter")
            return jsonify({
                "error": "Target Parameter is required"
            }), 400
        
        command = f"curl {target}"
        
        result = execute_command(command)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in curl endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500


@app.route("/api/tools/nmap", methods=["POST"])
@monitor_tool_execution("nmap") if MONITORING_AVAILABLE else lambda x: x
def nmap():
    """Execute nmap scan with the provided parameters."""
    try:
        params = request.json
        target = params.get("target", "")
        scan_type = params.get("scan_type", "-sCV")
        ports = params.get("ports", "")
        additional_args = params.get("additional_args", "-T4 -Pn")
        
        if not target:
            logger.warning("Nmap called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400        
        
        command = f"nmap {scan_type}"
        
        if ports:
            command += f" -p {ports}"
        
        if additional_args:
            # Basic validation for additional args - more sophisticated validation would be better
            command += f" {additional_args}"
        
        command += f" {target}"
        
        result = execute_command(command)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in nmap endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/gobuster", methods=["POST"])
@monitor_tool_execution("gobuster") if MONITORING_AVAILABLE else lambda x: x
def gobuster():
    """Execute gobuster with the provided parameters."""
    try:
        params = request.json
        url = params.get("url", "")
        mode = params.get("mode", "dir")
        wordlist = params.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        additional_args = params.get("additional_args", "")
        
        if not url:
            logger.warning("Gobuster called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400
        
        # Validate mode
        if mode not in ["dir", "dns", "fuzz", "vhost"]:
            logger.warning(f"Invalid gobuster mode: {mode}")
            return jsonify({
                "error": f"Invalid mode: {mode}. Must be one of: dir, dns, fuzz, vhost"
            }), 400
        
        command = f"gobuster {mode} -u {url} -w {wordlist}"
        
        if additional_args:
            command += f" {additional_args}"
        
        result = execute_command(command)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in gobuster endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/dirb", methods=["POST"])
@monitor_tool_execution("dirb") if MONITORING_AVAILABLE else lambda x: x
def dirb():
    """Execute dirb with the provided parameters."""
    try:
        params = request.json
        url = params.get("url", "")
        wordlist = params.get("wordlist", "/usr/share/wordlists/dirb/common.txt")
        additional_args = params.get("additional_args", "")
        
        if not url:
            logger.warning("Dirb called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400
        
        command = f"dirb {url} {wordlist}"
        
        if additional_args:
            command += f" {additional_args}"
        
        result = execute_command(command)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in dirb endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/nikto", methods=["POST"])
@monitor_tool_execution("nikto") if MONITORING_AVAILABLE else lambda x: x
def nikto():
    """Execute nikto with the provided parameters."""
    try:
        params = request.json
        target = params.get("target", "")
        additional_args = params.get("additional_args", "")
        
        if not target:
            logger.warning("Nikto called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400
        
        command = f"nikto -h {target}"
        
        if additional_args:
            command += f" {additional_args}"
        
        result = execute_command(command)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in nikto endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/sqlmap", methods=["POST"])
@monitor_tool_execution("sqlmap") if MONITORING_AVAILABLE else lambda x: x
def sqlmap():
    """Execute sqlmap with the provided parameters."""
    try:
        params = request.json
        url = params.get("url", "")
        data = params.get("data", "")
        additional_args = params.get("additional_args", "")
        
        if not url:
            logger.warning("SQLMap called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400
        
        command = f"sqlmap -u {url} --batch"
        
        if data:
            command += f" --data=\"{data}\""
        
        if additional_args:
            command += f" {additional_args}"
        
        result = execute_command(command)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in sqlmap endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/metasploit", methods=["POST"])
@monitor_tool_execution("metasploit") if MONITORING_AVAILABLE else lambda x: x
def metasploit():
    """Execute metasploit module with the provided parameters."""
    try:
        params = request.json
        module = params.get("module", "")
        options = params.get("options", {})
        
        if not module:
            logger.warning("Metasploit called without module parameter")
            return jsonify({
                "error": "Module parameter is required"
            }), 400
        
        # Format options for Metasploit
        options_str = ""
        for key, value in options.items():
            options_str += f" {key}={value}"
        
        # Create an MSF resource script
        resource_content = f"use {module}\n"
        for key, value in options.items():
            resource_content += f"set {key} {value}\n"
        resource_content += "exploit\n"
        
        # Save resource script to a temporary file
        resource_file = "/tmp/mcp_msf_resource.rc"
        with open(resource_file, "w") as f:
            f.write(resource_content)
        
        command = f"msfconsole -q -r {resource_file}"
        result = execute_command(command)
        
        # Clean up the temporary file
        try:
            os.remove(resource_file)
        except Exception as e:
            logger.warning(f"Error removing temporary resource file: {str(e)}")
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in metasploit endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/hydra", methods=["POST"])
@monitor_tool_execution("hydra") if MONITORING_AVAILABLE else lambda x: x
def hydra():
    """Execute hydra with the provided parameters."""
    try:
        params = request.json
        target = params.get("target", "")
        service = params.get("service", "")
        username = params.get("username", "")
        username_file = params.get("username_file", "")
        password = params.get("password", "")
        password_file = params.get("password_file", "")
        additional_args = params.get("additional_args", "")
        
        if not target or not service:
            logger.warning("Hydra called without target or service parameter")
            return jsonify({
                "error": "Target and service parameters are required"
            }), 400
        
        if not (username or username_file) or not (password or password_file):
            logger.warning("Hydra called without username/password parameters")
            return jsonify({
                "error": "Username/username_file and password/password_file are required"
            }), 400
        
        command = f"hydra -t 4"
        
        if username:
            command += f" -l {username}"
        elif username_file:
            command += f" -L {username_file}"
        
        if password:
            command += f" -p {password}"
        elif password_file:
            command += f" -P {password_file}"
        
        if additional_args:
            command += f" {additional_args}"
        
        command += f" {target} {service}"
        
        result = execute_command(command)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in hydra endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/john", methods=["POST"])
@monitor_tool_execution("john") if MONITORING_AVAILABLE else lambda x: x
def john():
    """Execute john with the provided parameters."""
    try:
        params = request.json
        hash_file = params.get("hash_file", "")
        wordlist = params.get("wordlist", "/usr/share/wordlists/rockyou.txt")
        format_type = params.get("format", "")
        additional_args = params.get("additional_args", "")
        
        if not hash_file:
            logger.warning("John called without hash_file parameter")
            return jsonify({
                "error": "Hash file parameter is required"
            }), 400
        
        command = f"john"
        
        if format_type:
            command += f" --format={format_type}"
        
        if wordlist:
            command += f" --wordlist={wordlist}"
        
        if additional_args:
            command += f" {additional_args}"
        
        command += f" {hash_file}"
        
        result = execute_command(command)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in john endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/wpscan", methods=["POST"])
@monitor_tool_execution("wpscan") if MONITORING_AVAILABLE else lambda x: x
def wpscan():
    """Execute wpscan with the provided parameters."""
    try:
        params = request.json
        url = params.get("url", "")
        additional_args = params.get("additional_args", "")
        
        if not url:
            logger.warning("WPScan called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400
        
        command = f"wpscan --url {url}"
        
        if additional_args:
            command += f" {additional_args}"
        
        result = execute_command(command)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in wpscan endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/enum4linux", methods=["POST"])
@monitor_tool_execution("enum4linux") if MONITORING_AVAILABLE else lambda x: x
def enum4linux():
    """Execute enum4linux with the provided parameters."""
    try:
        params = request.json
        target = params.get("target", "")
        additional_args = params.get("additional_args", "-a")
        
        if not target:
            logger.warning("Enum4linux called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400
        
        command = f"enum4linux {additional_args} {target}"
        
        result = execute_command(command)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in enum4linux endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
        
@app.route("/api/tools/trivy", methods=["POST"])
@monitor_tool_execution("trivy") if MONITORING_AVAILABLE else lambda x: x
def trivy():
    """Execute trivy for making SBOM file from local package-lock.json."""
    try:
        params = request.json
        file_path = params.get("file_path", "").strip()

        if not file_path:
            logger.warning("Trivy can't find any file path.")
            return jsonify({
                "error": "File Path is required." 
            }), 400

        file_path = os.path.abspath(file_path)

        package_lock_path = os.path.join(file_path, "package-lock.json")
        sbom_output_path = os.path.join(file_path, "sbom.json")

        if not os.path.exists(package_lock_path):
            logger.warning(f"File not found: {package_lock_path}")
            return jsonify({
                "error": f"'package-lock.json' not found in: {file_path}"
            }), 404

        command = f"trivy fs --format cyclonedx --scanners vuln --output \"{sbom_output_path}\" \"{package_lock_path}\""

        logger.info(f"Executing command: {command}")
        execute_command(command)
        
        cmd = f"cat {sbom_output_path}"
        
        result = execute_command(cmd)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in trivy endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500        

# Enhanced health check with monitoring
@health_check("tools_availability") if MONITORING_AVAILABLE else lambda: {}
def check_tools_availability():
    """Check if essential tools are available"""
    essential_tools = ["nmap", "gobuster", "dirb", "nikto", "sqlmap", "hydra", "john", "wpscan", "enum4linux", "trivy"]
    tools_status = {}
    
    for tool in essential_tools:
        try:
            result = execute_command(f"which {tool}")
            tools_status[tool] = result["success"]
        except:
            tools_status[tool] = False
    
    all_available = all(tools_status.values())
    
    return {
        "healthy": all_available,
        "tools_status": tools_status,
        "available_count": sum(tools_status.values()),
        "total_count": len(tools_status)
    }

@health_check("system_resources") if MONITORING_AVAILABLE else lambda: {}
def check_system_resources():
    """Check system resource availability"""
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Define thresholds
        cpu_healthy = cpu_percent < 90
        memory_healthy = memory.percent < 90
        disk_healthy = (disk.used / disk.total * 100) < 95
        
        return {
            "healthy": cpu_healthy and memory_healthy and disk_healthy,
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.used / disk.total * 100,
            "thresholds_ok": {
                "cpu": cpu_healthy,
                "memory": memory_healthy,
                "disk": disk_healthy
            }
        }
    except ImportError:
        return {"healthy": True, "message": "psutil not available, skipping resource check"}

# Main health endpoint
@app.route("/health", methods=["GET"])
def health_endpoint():
    """Comprehensive health check endpoint"""
    if MONITORING_AVAILABLE:
        # Use enhanced health checks
        health_results = health_manager.run_all_checks()
        
        # Add basic server info
        response = {
            "status": "healthy" if health_results["overall_healthy"] else "unhealthy",
            "message": "Kali Linux Tools API Server",
            "server_info": {
                "version": "1.0.0",
                "uptime": time.time() - app.config.get('START_TIME', time.time()),
                "monitoring_enabled": True
            },
            "health_checks": health_results["checks"],
            "overall_healthy": health_results["overall_healthy"],
            "timestamp": health_results["timestamp"]
        }
    else:
        # Fallback to basic health check
        tools_check = check_tools_availability()
        response = {
            "status": "healthy" if tools_check["healthy"] else "degraded",
            "message": "Kali Linux Tools API Server (basic health check)",
            "server_info": {
                "version": "1.0.0",
                "monitoring_enabled": False
            },
            "tools_status": tools_check["tools_status"],
            "all_essential_tools_available": tools_check["healthy"]
        }
    
    status_code = 200 if response.get("overall_healthy", response["status"] == "healthy") else 503
    return jsonify(response), status_code

# New monitoring endpoints
@app.route("/metrics", methods=["GET"])
def metrics_endpoint():
    """Prometheus-style metrics endpoint"""
    if not MONITORING_AVAILABLE:
        return jsonify({"error": "Monitoring not available"}), 503
    
    format_type = request.args.get('format', 'prometheus')
    try:
        metrics_data = metrics_collector.export_metrics(format_type)
        
        if format_type == 'prometheus':
            return metrics_data, 200, {'Content-Type': 'text/plain'}
        else:
            return jsonify(json.loads(metrics_data))
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/status", methods=["GET"])
def status_endpoint():
    """Detailed server status information"""
    response = {
        "server_name": "kali-server",
        "version": "1.0.0",
        "status": "running",
        "uptime": time.time() - app.config.get('START_TIME', time.time()),
        "monitoring_enabled": MONITORING_AVAILABLE
    }
    
    if MONITORING_AVAILABLE:
        # Add metrics summary
        response["metrics_summary"] = metrics_collector.get_summary_stats()
        response["health_status"] = metrics_collector.get_health_status()
    
    return jsonify(response)

@app.route("/mcp/capabilities", methods=["GET"])
def get_capabilities():
    """Return tool capabilities for MCP integration"""
    capabilities = {
        "tools": {
            "nmap": {"description": "Network scanning and discovery", "timeout": 3600},
            "gobuster": {"description": "Directory/file brute-forcing", "timeout": 1800},
            "dirb": {"description": "Web content scanner", "timeout": 1800},
            "nikto": {"description": "Web server scanner", "timeout": 1200},
            "sqlmap": {"description": "SQL injection detection", "timeout": 2400},
            "metasploit": {"description": "Metasploit framework", "timeout": 1800},
            "hydra": {"description": "Password brute-forcing", "timeout": 1800},
            "john": {"description": "Password hash cracking", "timeout": 3600},
            "wpscan": {"description": "WordPress vulnerability scanner", "timeout": 1200},
            "enum4linux": {"description": "SMB enumeration", "timeout": 900},
            "trivy": {"description": "Container vulnerability scanner", "timeout": 600}
        },
        "features": {
            "monitoring": MONITORING_AVAILABLE,
            "health_checks": True,
            "metrics": MONITORING_AVAILABLE
        }
    }
    return jsonify(capabilities)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Kali Linux API Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=API_PORT, help=f"Port for the API server (default: {API_PORT})")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Set configuration from command line arguments
    if args.debug:
        DEBUG_MODE = True
        os.environ["DEBUG_MODE"] = "1"
        logger.setLevel(logging.DEBUG)
    
    if args.port != API_PORT:
        API_PORT = args.port
    
    # Store start time for uptime calculation
    app.config['START_TIME'] = time.time()
    
    # Initialize monitoring if available
    if MONITORING_AVAILABLE:
        logger.info("Monitoring system initialized")
        # Register additional health checks
        check_tools_availability()
        check_system_resources()
    
    logger.info(f"Starting Kali Linux Tools API Server on port {API_PORT}")
    logger.info(f"Monitoring enabled: {MONITORING_AVAILABLE}")
    
    try:
        app.run(host="0.0.0.0", port=API_PORT, debug=DEBUG_MODE)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        if MONITORING_AVAILABLE and metrics_collector:
            metrics_collector.stop_collection()
    except Exception as e:
        logger.error(f"Server error: {e}")
        if MONITORING_AVAILABLE and metrics_collector:
            metrics_collector.stop_collection()
        raise

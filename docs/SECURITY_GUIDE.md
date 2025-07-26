# Not-Yet Security Guide

## Overview

This guide covers security considerations, best practices, and usage guidelines for the Not-Yet security testing framework. The system is designed for legitimate security testing and educational purposes only.

## Ethical Usage Guidelines

### Legal Requirements

1. **Authorization**: Only test systems you own or have explicit written permission to test
2. **Scope**: Stay within agreed-upon testing boundaries
3. **Compliance**: Follow all applicable laws and regulations
4. **Disclosure**: Report findings through appropriate channels
5. **Documentation**: Keep detailed logs of all testing activities

### Responsible Disclosure

When discovering vulnerabilities:
1. Document the finding with reproduction steps
2. Notify the affected party privately
3. Allow reasonable time for remediation
4. Avoid public disclosure until patched
5. Never exploit vulnerabilities for gain

## System Security

### Network Security

**Default Configuration**:
- Servers bind to `localhost` only
- No authentication by default
- Plain HTTP communication

**Production Hardening**:
```python
# Bind to specific interface
app.run(host='127.0.0.1', port=5000)

# Enable HTTPS
app.run(ssl_context='adhoc')

# Add authentication middleware
@app.before_request
def require_auth():
    if not validate_token(request.headers.get('Authorization')):
        abort(401)
```

### Authentication & Authorization

**Implementing API Keys**:
```python
# Add to each server
API_KEYS = os.environ.get('API_KEYS', '').split(',')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key not in API_KEYS:
            abort(401, 'Invalid API key')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/tools/nmap', methods=['POST'])
@require_api_key
def nmap_scan():
    # ... existing code ...
```

### Input Validation

**Command Injection Prevention**:
```python
import shlex
import re

def validate_target(target):
    """Validate IP address or hostname"""
    # IP address pattern
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    # Hostname pattern
    host_pattern = r'^[a-zA-Z0-9.-]+$'
    
    if not (re.match(ip_pattern, target) or re.match(host_pattern, target)):
        raise ValueError("Invalid target format")
    
    return target

def sanitize_options(options):
    """Remove dangerous characters from options"""
    # Whitelist allowed characters
    allowed = re.compile(r'^[a-zA-Z0-9\s\-.,/=]+$')
    if not allowed.match(options):
        raise ValueError("Invalid characters in options")
    
    return shlex.quote(options)
```

### Resource Limits

**Implementing Rate Limiting**:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/tools/nmap', methods=['POST'])
@limiter.limit("5 per minute")
def nmap_scan():
    # ... existing code ...
```

**Resource Quotas**:
```python
import resource
import os

def set_resource_limits():
    """Set process resource limits"""
    # Maximum CPU time (seconds)
    resource.setrlimit(resource.RLIMIT_CPU, (3600, 3600))
    
    # Maximum memory (bytes)
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, 2 * 1024 * 1024 * 1024))
    
    # Maximum number of processes
    resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))
```

## Tool-Specific Security

### Nmap Security

**Safe Scanning Practices**:
```python
# Limit scan types
ALLOWED_SCAN_TYPES = ['-sT', '-sS', '-sV', '-sU']

# Restrict port ranges
MAX_PORTS = 1000

# Validate options
def validate_nmap_options(options):
    opts = options.split()
    for opt in opts:
        if opt.startswith('-') and opt not in ALLOWED_SCAN_TYPES:
            raise ValueError(f"Scan type {opt} not allowed")
    
    # Check port range
    if '-p' in opts:
        port_idx = opts.index('-p') + 1
        if port_idx < len(opts):
            ports = opts[port_idx]
            if '-' in ports:
                start, end = map(int, ports.split('-'))
                if end - start > MAX_PORTS:
                    raise ValueError("Port range too large")
```

### SQLMap Security

**Preventing Abuse**:
```python
# Restrict SQLMap levels
MAX_LEVEL = 3
MAX_RISK = 2

def validate_sqlmap_options(options):
    # Parse options
    if '--level' in options:
        level = int(re.search(r'--level\s+(\d+)', options).group(1))
        if level > MAX_LEVEL:
            raise ValueError(f"Level {level} exceeds maximum {MAX_LEVEL}")
    
    if '--risk' in options:
        risk = int(re.search(r'--risk\s+(\d+)', options).group(1))
        if risk > MAX_RISK:
            raise ValueError(f"Risk {risk} exceeds maximum {MAX_RISK}")
    
    # Prevent OS command execution
    dangerous_options = ['--os-cmd', '--os-shell', '--os-pwn']
    for dangerous in dangerous_options:
        if dangerous in options:
            raise ValueError(f"Option {dangerous} is not allowed")
```

### Metasploit Security

**Restricting Exploits**:
```python
# Whitelist safe modules
SAFE_MODULES = [
    'auxiliary/scanner/',
    'auxiliary/gather/',
    'post/gather/'
]

def validate_metasploit_command(command):
    # Only allow specific module types
    if 'use' in command:
        module = command.split('use')[1].strip()
        if not any(module.startswith(safe) for safe in SAFE_MODULES):
            raise ValueError("Module type not allowed")
    
    # Prevent payload execution
    if any(word in command for word in ['exploit', 'run', 'sessions']):
        raise ValueError("Command not allowed")
```

## Data Security

### Sensitive Data Handling

**Log Sanitization**:
```python
import re

def sanitize_output(output):
    """Remove sensitive data from output"""
    # Remove potential passwords
    output = re.sub(r'password["\']?\s*[:=]\s*["\']?[\w\S]+', 'password=***', output, flags=re.I)
    
    # Remove API keys
    output = re.sub(r'api[_-]?key["\']?\s*[:=]\s*["\']?[\w\S]+', 'api_key=***', output, flags=re.I)
    
    # Remove tokens
    output = re.sub(r'token["\']?\s*[:=]\s*["\']?[\w\S]+', 'token=***', output, flags=re.I)
    
    return output
```

**Secure Storage**:
```python
import hashlib
from cryptography.fernet import Fernet

class SecureStorage:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def store_result(self, scan_id, data):
        """Encrypt and store scan results"""
        encrypted = self.cipher.encrypt(data.encode())
        
        # Store with hash as filename
        filename = hashlib.sha256(scan_id.encode()).hexdigest()
        with open(f'/secure/storage/{filename}', 'wb') as f:
            f.write(encrypted)
    
    def retrieve_result(self, scan_id):
        """Retrieve and decrypt scan results"""
        filename = hashlib.sha256(scan_id.encode()).hexdigest()
        with open(f'/secure/storage/{filename}', 'rb') as f:
            encrypted = f.read()
        
        return self.cipher.decrypt(encrypted).decode()
```

## Deployment Security

### Docker Security

**Secure Dockerfile**:
```dockerfile
FROM python:3.12-slim

# Run as non-root user
RUN useradd -m -s /bin/bash scanner
USER scanner

# Copy only necessary files
COPY --chown=scanner:scanner requirements.txt .
COPY --chown=scanner:scanner *.py .

# Install dependencies
RUN pip install --user -r requirements.txt

# Expose only necessary ports
EXPOSE 5000

# Run with limited privileges
CMD ["python", "-u", "kali_server.py"]
```

**Docker Compose Security**:
```yaml
version: '3.8'

services:
  kali-server:
    build: .
    restart: unless-stopped
    ports:
      - "127.0.0.1:5000:5000"
    environment:
      - API_KEY=${API_KEY}
    cap_drop:
      - ALL
    cap_add:
      - NET_RAW  # Required for nmap
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
```

### Network Isolation

**Firewall Rules**:
```bash
# Allow only local connections
iptables -A INPUT -p tcp --dport 5000 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 5000 -j DROP

# Restrict outbound connections
iptables -A OUTPUT -m owner --uid-owner scanner -d 10.0.0.0/8 -j DROP
iptables -A OUTPUT -m owner --uid-owner scanner -d 172.16.0.0/12 -j DROP
iptables -A OUTPUT -m owner --uid-owner scanner -d 192.168.0.0/16 -j DROP
```

## Monitoring & Auditing

### Logging Configuration

**Comprehensive Logging**:
```python
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger('security')
        handler = RotatingFileHandler('security.log', maxBytes=10*1024*1024, backupCount=5)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_scan(self, tool, target, user, options):
        """Log security scan activity"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'tool': tool,
            'target': target,
            'user': user,
            'options': options,
            'event': 'scan_initiated'
        }
        self.logger.info(json.dumps(log_entry))
```

### Intrusion Detection

**Anomaly Detection**:
```python
class AnomalyDetector:
    def __init__(self):
        self.baseline = {}
        self.threshold = 3  # Standard deviations
    
    def check_anomaly(self, user, action):
        """Detect anomalous behavior"""
        key = f"{user}:{action}"
        
        # Track frequency
        if key not in self.baseline:
            self.baseline[key] = []
        
        current_time = time.time()
        self.baseline[key].append(current_time)
        
        # Calculate rate
        recent = [t for t in self.baseline[key] if current_time - t < 3600]
        rate = len(recent)
        
        # Check against baseline
        if rate > self.get_baseline_rate(key) * self.threshold:
            self.alert_anomaly(user, action, rate)
            return True
        
        return False
```

## Incident Response

### Response Plan

1. **Detection**: Monitor logs for suspicious activity
2. **Containment**: Isolate affected systems
3. **Eradication**: Remove threats and patch vulnerabilities
4. **Recovery**: Restore services safely
5. **Lessons Learned**: Document and improve

### Emergency Procedures

**Kill Switch Implementation**:
```python
import signal
import sys

class EmergencyShutdown:
    def __init__(self):
        signal.signal(signal.SIGUSR1, self.emergency_stop)
        self.shutdown_flag = False
    
    def emergency_stop(self, signum, frame):
        """Emergency shutdown procedure"""
        self.shutdown_flag = True
        
        # Stop all running scans
        for thread in threading.enumerate():
            if hasattr(thread, 'terminate'):
                thread.terminate()
        
        # Log emergency shutdown
        logging.critical("EMERGENCY SHUTDOWN INITIATED")
        
        # Close all connections
        # ... cleanup code ...
        
        sys.exit(1)
```

## Best Practices Summary

### Do's
- ✅ Always verify authorization before testing
- ✅ Use the minimum required privileges
- ✅ Log all activities comprehensively
- ✅ Implement rate limiting and timeouts
- ✅ Validate and sanitize all inputs
- ✅ Encrypt sensitive data at rest and in transit
- ✅ Regular security updates and patching
- ✅ Monitor for anomalous behavior

### Don'ts
- ❌ Never test without permission
- ❌ Don't store credentials in code
- ❌ Avoid running as root/administrator
- ❌ Don't expose services to public internet
- ❌ Never disable security features
- ❌ Don't ignore security warnings
- ❌ Avoid using outdated dependencies
- ❌ Never share API keys or credentials

## Security Checklist

- [ ] Authorization verified for all targets
- [ ] Authentication implemented on all endpoints
- [ ] Input validation for all parameters
- [ ] Rate limiting configured
- [ ] Logging enabled with rotation
- [ ] Sensitive data sanitized
- [ ] Network isolation configured
- [ ] Resource limits set
- [ ] Regular security updates scheduled
- [ ] Incident response plan documented
- [ ] Monitoring and alerting active
- [ ] Backup and recovery tested
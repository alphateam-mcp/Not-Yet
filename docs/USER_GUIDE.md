# Not-Yet User Guide

## Introduction

Not-Yet is a powerful security testing and AI research platform that combines Kali Linux security tools with AI-powered search capabilities. This guide will help you effectively use the system for security testing, vulnerability assessment, and threat research.

## Getting Started

### Prerequisites

Before using Not-Yet, ensure you have:
- ✅ Completed installation (see [Installation Guide](INSTALLATION_GUIDE.md))
- ✅ Valid authorization for all testing targets
- ✅ Understanding of security testing ethics
- ✅ Basic knowledge of command-line tools

### Starting the System

1. **Activate the environment**:
```bash
conda activate not-yet
```

2. **Start the servers**:
```bash
# Start all servers in separate terminals or use screen/tmux
python kali_server.py
python perplexity_server.py
python mcp_server.py  # Only if using Claude Desktop
```

3. **Verify system health**:
```bash
curl http://localhost:5000/health
```

## Core Features

### 1. Network Scanning

**Basic Network Discovery**:
```bash
# Scan single host
curl -X POST http://localhost:5000/api/tools/nmap \
  -H "Content-Type: application/json" \
  -d '{
    "target": "scanme.nmap.org",
    "options": "-sV",
    "timeout": 300
  }'

# Scan network range
curl -X POST http://localhost:5000/api/tools/nmap \
  -H "Content-Type: application/json" \
  -d '{
    "target": "192.168.1.0/24",
    "options": "-sn",
    "timeout": 600
  }'
```

**Advanced Scanning**:
```bash
# Service version detection
curl -X POST http://localhost:5000/api/tools/nmap \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "options": "-sV -sC -O -A",
    "timeout": 1200
  }'

# Specific port scanning
curl -X POST http://localhost:5000/api/tools/nmap \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "options": "-p 80,443,8080,8443",
    "timeout": 300
  }'
```

### 2. Web Application Testing

**Directory Discovery**:
```bash
# Using Gobuster
curl -X POST http://localhost:5000/api/tools/gobuster \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://example.com",
    "wordlist": "/usr/share/wordlists/dirb/common.txt",
    "options": "-t 50 -x php,asp,aspx,jsp",
    "timeout": 900
  }'

# Using Dirb
curl -X POST http://localhost:5000/api/tools/dirb \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://example.com",
    "wordlist": "/usr/share/wordlists/dirb/big.txt",
    "options": "-S",
    "timeout": 900
  }'
```

**Vulnerability Scanning**:
```bash
# Nikto web scanner
curl -X POST http://localhost:5000/api/tools/nikto \
  -H "Content-Type: application/json" \
  -d '{
    "host": "http://example.com",
    "options": "-h -ssl -Format json",
    "timeout": 1800
  }'

# SQL injection testing
curl -X POST http://localhost:5000/api/tools/sqlmap \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://example.com/page.php?id=1",
    "options": "--batch --risk=2 --level=3",
    "timeout": 2400
  }'
```

### 3. WordPress Security Testing

```bash
# Comprehensive WordPress scan
curl -X POST http://localhost:5000/api/tools/wpscan \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://wordpress.example.com",
    "options": "--enumerate p,t,u,m --plugins-detection aggressive",
    "timeout": 1200
  }'

# Specific plugin vulnerability check
curl -X POST http://localhost:5000/api/tools/wpscan \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://wordpress.example.com",
    "options": "--enumerate vp --plugins-version-all",
    "timeout": 900
  }'
```

### 4. Password Security Testing

**Password Cracking**:
```bash
# Crack password hashes
curl -X POST http://localhost:5000/api/tools/john \
  -H "Content-Type: application/json" \
  -d '{
    "hashfile": "/tmp/hashes.txt",
    "options": "--wordlist=/usr/share/wordlists/rockyou.txt --format=raw-md5",
    "timeout": 3600
  }'
```

**Brute Force Testing**:
```bash
# SSH brute force
curl -X POST http://localhost:5000/api/tools/hydra \
  -H "Content-Type: application/json" \
  -d '{
    "target": "192.168.1.100",
    "service": "ssh",
    "userlist": "/usr/share/wordlists/metasploit/unix_users.txt",
    "passlist": "/usr/share/wordlists/metasploit/unix_passwords.txt",
    "options": "-t 4",
    "timeout": 1800
  }'
```

### 5. SMB Enumeration

```bash
# Enumerate SMB shares
curl -X POST http://localhost:5000/api/tools/enum4linux \
  -H "Content-Type: application/json" \
  -d '{
    "target": "192.168.1.100",
    "options": "-a -M -l -d",
    "timeout": 900
  }'
```

### 6. Container Security Scanning

```bash
# Scan Docker image
curl -X POST http://localhost:5000/api/tools/trivy \
  -H "Content-Type: application/json" \
  -d '{
    "target": "alpine:latest",
    "options": "--severity HIGH,CRITICAL --format json",
    "timeout": 600
  }'

# Generate SBOM
curl -X POST http://localhost:5000/api/tools/trivy \
  -H "Content-Type: application/json" \
  -d '{
    "target": "myapp:latest",
    "options": "--format spdx",
    "timeout": 300
  }'
```

### 7. AI-Powered Security Research

```bash
# Research latest vulnerabilities
curl -X POST http://localhost:5050/api/perplexity/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest critical vulnerabilities in Apache Struts 2024?"
  }'

# Get exploitation techniques
curl -X POST http://localhost:5050/api/perplexity/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to detect and prevent SQL injection attacks in modern web applications?"
  }'

# Security best practices
curl -X POST http://localhost:5050/api/perplexity/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the current best practices for securing Kubernetes clusters?"
  }'
```

## Advanced Usage

### Combining Tools

**Reconnaissance Workflow**:
```bash
# 1. Network discovery
TARGET="example.com"

# 2. DNS enumeration
curl -X POST http://localhost:5000/api/command \
  -H "Content-Type: application/json" \
  -d "{\"command\": \"dig +short $TARGET\", \"timeout\": 30}"

# 3. Port scanning
curl -X POST http://localhost:5000/api/tools/nmap \
  -H "Content-Type: application/json" \
  -d "{\"target\": \"$TARGET\", \"options\": \"-sV -sC\", \"timeout\": 600}"

# 4. Web technology detection
curl -X POST http://localhost:5000/api/command \
  -H "Content-Type: application/json" \
  -d "{\"command\": \"whatweb $TARGET\", \"timeout\": 60}"
```

### Automation Scripts

**Create a scanning script**:
```python
#!/usr/bin/env python3
import requests
import json
import time

class NotYetClient:
    def __init__(self, kali_url="http://localhost:5000", perplexity_url="http://localhost:5050"):
        self.kali_url = kali_url
        self.perplexity_url = perplexity_url
    
    def nmap_scan(self, target, options=""):
        response = requests.post(
            f"{self.kali_url}/api/tools/nmap",
            json={"target": target, "options": options, "timeout": 600}
        )
        return response.json()
    
    def research_vulnerability(self, query):
        response = requests.post(
            f"{self.perplexity_url}/api/perplexity/search",
            json={"query": query}
        )
        return response.json()
    
    def comprehensive_scan(self, target):
        results = {}
        
        # Network scan
        print(f"Scanning {target}...")
        results['nmap'] = self.nmap_scan(target, "-sV -sC")
        
        # Research vulnerabilities
        print("Researching vulnerabilities...")
        results['research'] = self.research_vulnerability(
            f"Known vulnerabilities for services on {target}"
        )
        
        return results

# Usage
client = NotYetClient()
results = client.comprehensive_scan("scanme.nmap.org")
print(json.dumps(results, indent=2))
```

### Using with Claude Desktop

When integrated with Claude Desktop via MCP:

1. **Start a conversation** with Claude
2. **Request security analysis**:
   - "Scan example.com for open ports"
   - "Check if this WordPress site has vulnerabilities"
   - "Research the latest Apache vulnerabilities"

3. **Claude will**:
   - Execute appropriate tools
   - Analyze results
   - Provide recommendations

## Best Practices

### 1. Scanning Etiquette

- **Start Slow**: Begin with light scans before intensive ones
- **Respect Limits**: Don't overwhelm targets with requests
- **Time Appropriately**: Scan during agreed maintenance windows
- **Document Everything**: Keep logs of all activities

### 2. Efficient Workflows

**Progressive Scanning**:
1. Start with passive reconnaissance
2. Perform light network scanning
3. Identify specific services
4. Deep dive into interesting findings
5. Research vulnerabilities
6. Document and report

**Resource Management**:
```bash
# Use appropriate timeouts
SHORT_TIMEOUT=300    # 5 minutes for quick scans
MEDIUM_TIMEOUT=900   # 15 minutes for moderate scans
LONG_TIMEOUT=3600    # 1 hour for comprehensive scans

# Limit concurrent operations
# Run intensive scans sequentially, not in parallel
```

### 3. Security Research Tips

**Effective Queries**:
```bash
# Good: Specific and contextual
"What are the latest CVEs for Apache Struts 2.5.x with CVSS score above 7?"

# Better: Include mitigation context
"How to detect and mitigate CVE-2023-12345 in production environments?"

# Best: Comprehensive security posture
"What are the security implications of running Apache Struts 2.5.30 and recommended hardening steps?"
```

## Common Use Cases

### 1. Pre-deployment Security Check

```bash
# Scan staging environment
./scan_staging.sh

# Content of scan_staging.sh:
#!/bin/bash
TARGET="staging.example.com"

echo "Running pre-deployment security check for $TARGET"

# Port scan
echo "1. Checking open ports..."
curl -X POST http://localhost:5000/api/tools/nmap \
  -H "Content-Type: application/json" \
  -d "{\"target\": \"$TARGET\", \"options\": \"-sV\", \"timeout\": 600}"

# Web vulnerabilities
echo "2. Checking web vulnerabilities..."
curl -X POST http://localhost:5000/api/tools/nikto \
  -H "Content-Type: application/json" \
  -d "{\"host\": \"http://$TARGET\", \"options\": \"-h\", \"timeout\": 1200}"

# SSL/TLS check
echo "3. Checking SSL/TLS configuration..."
curl -X POST http://localhost:5000/api/command \
  -H "Content-Type: application/json" \
  -d "{\"command\": \"sslscan $TARGET\", \"timeout\": 300}"
```

### 2. Incident Response

```bash
# Quick compromise assessment
SUSPECT_IP="192.168.1.100"

# Check for common backdoors
curl -X POST http://localhost:5000/api/tools/nmap \
  -H "Content-Type: application/json" \
  -d "{\"target\": \"$SUSPECT_IP\", \"options\": \"-sV -p 1-65535\", \"timeout\": 3600}"

# Research indicators
curl -X POST http://localhost:5050/api/perplexity/search \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Common backdoor ports and services used by attackers in 2024\"}"
```

### 3. Compliance Scanning

```bash
# OWASP Top 10 check
./owasp_check.sh target.example.com

# PCI DSS scan
./pci_scan.sh ecommerce.example.com

# HIPAA compliance
./hipaa_scan.sh healthcare.example.com
```

## Tips and Tricks

### 1. Performance Optimization

- **Use specific port ranges** instead of full port scans
- **Leverage wordlist size** appropriately (start small)
- **Set reasonable timeouts** based on network conditions
- **Run scans during off-peak hours** when possible

### 2. Output Management

```bash
# Save outputs for analysis
SCAN_DATE=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="scans/$SCAN_DATE"
mkdir -p $OUTPUT_DIR

# Redirect outputs
curl -X POST http://localhost:5000/api/tools/nmap \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "options": "-sV"}' \
  > $OUTPUT_DIR/nmap_results.json
```

### 3. Troubleshooting

**Timeout Issues**:
- Increase timeout values for slow networks
- Use more specific targeting
- Break large scans into smaller chunks

**Permission Errors**:
- Ensure tools have necessary capabilities
- Run servers with appropriate permissions
- Check file path permissions

**No Results**:
- Verify target is reachable
- Check firewall rules
- Ensure tools are properly installed

## Safety Reminders

1. **Legal Authorization**: Always have written permission
2. **Scope Boundaries**: Never exceed authorized scope
3. **Data Protection**: Secure all captured data
4. **Responsible Disclosure**: Report vulnerabilities properly
5. **Ethical Use**: Use for defense, not offense

## Getting Help

1. **API Documentation**: See [API Reference](API_REFERENCE.md)
2. **Security Guidelines**: Review [Security Guide](SECURITY_GUIDE.md)
3. **Architecture Details**: Check [Architecture](ARCHITECTURE.md)
4. **Development**: Contribute via [Development Guide](DEVELOPMENT_GUIDE.md)

## Conclusion

Not-Yet provides powerful capabilities for security testing and research. Use it responsibly, ethically, and always with proper authorization. Regular practice and continuous learning will help you maximize the platform's potential while maintaining security best practices.
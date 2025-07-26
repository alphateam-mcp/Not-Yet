# Not-Yet Installation Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Quick Start](#quick-start)
3. [Detailed Installation](#detailed-installation)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **OS**: Kali Linux 2023.x+ (recommended) or Debian 11+
- **Python**: 3.12+
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB free space
- **Network**: Internet connection for package installation

### Required Tools
The following Kali tools must be installed:
- nmap
- gobuster
- dirb
- nikto
- sqlmap
- metasploit-framework
- hydra
- john
- wpscan
- enum4linux
- trivy

## Quick Start

For experienced users who want to get up and running quickly:

```bash
# Clone repository
git clone https://github.com/yourusername/not-yet.git
cd not-yet

# Create conda environment
conda create -n not-yet python=3.12 -y
conda activate not-yet

# Install dependencies
pip install -r requirements.txt

# Set API key
export PERPLEXITY_API_KEY="your_api_key_here"

# Start servers
python kali_server.py &
python perplexity_server.py &
python mcp_server.py
```

## Detailed Installation

### Step 1: System Preparation

**Update System**
```bash
sudo apt update && sudo apt upgrade -y
```

**Install System Dependencies**
```bash
sudo apt install -y \
    build-essential \
    git \
    curl \
    wget \
    software-properties-common
```

### Step 2: Install Miniconda

```bash
# Download Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Make executable
chmod +x Miniconda3-latest-Linux-x86_64.sh

# Install Miniconda
./Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3

# Add to PATH
echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
conda --version
```

### Step 3: Install Security Tools

**On Kali Linux** (tools pre-installed):
```bash
# Verify tools are available
which nmap gobuster dirb nikto sqlmap msfconsole hydra john wpscan enum4linux

# Install missing tools if needed
sudo apt install -y nmap gobuster dirb nikto sqlmap metasploit-framework hydra john wpscan enum4linux
```

**Install Trivy**:
```bash
# Add Trivy repository
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list

# Install Trivy
sudo apt-get update
sudo apt-get install trivy
```

**On Other Debian-based Systems**:
```bash
# Add Kali repository (use with caution)
echo "deb http://http.kali.org/kali kali-rolling main non-free contrib" | sudo tee /etc/apt/sources.list.d/kali.list
wget -q -O - https://archive.kali.org/archive-key.asc | sudo apt-key add -

# Install tools
sudo apt update
sudo apt install -y nmap gobuster dirb nikto sqlmap metasploit-framework hydra john wpscan enum4linux trivy
```

### Step 4: Clone and Setup Not-Yet

```bash
# Clone repository
git clone https://github.com/yourusername/not-yet.git
cd not-yet

# Create conda environment
conda create -n not-yet python=3.12 -y
conda activate not-yet

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs
mkdir -p config
mkdir -p data
```

### Step 5: Configure Environment

**Create `.env` file**:
```bash
cat > .env << EOF
# API Keys
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Server Configuration
KALI_SERVER_HOST=127.0.0.1
KALI_SERVER_PORT=5000
PERPLEXITY_SERVER_HOST=127.0.0.1
PERPLEXITY_SERVER_PORT=5050

# Timeouts
DEFAULT_TIMEOUT=3600
MAX_TIMEOUT=7200

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/not-yet.log

# Security
API_KEY=your_secure_api_key_here
ENABLE_AUTH=false

# Debug
DEBUG_MODE=false
EOF
```

**Load environment variables**:
```bash
source .env
```

### Step 6: Claude Desktop Integration (Optional)

**Install Claude Desktop**:
1. Download Claude Desktop from Anthropic
2. Install following the platform-specific instructions

**Configure MCP Server**:

Create or edit `~/.config/claude/claude_config.json`:
```json
{
  "mcpServers": {
    "not-yet": {
      "command": "/home/user/miniconda3/envs/not-yet/bin/python",
      "args": ["/path/to/not-yet/mcp_server.py"],
      "env": {
        "PERPLEXITY_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Configuration

### Server Configuration

**Create `config/servers.yaml`**:
```yaml
kali_server:
  host: 127.0.0.1
  port: 5000
  timeout: 3600
  max_workers: 4
  
perplexity_server:
  host: 127.0.0.1
  port: 5050
  model: sonar
  max_tokens: 4096
  
mcp_server:
  name: not-yet
  description: Security testing and AI search tools
```

### Tool Configuration

**Create `config/tools.yaml`**:
```yaml
tools:
  nmap:
    default_options: "-sV"
    max_timeout: 3600
    allowed_options: ["-sV", "-sS", "-sU", "-p"]
    
  gobuster:
    default_wordlist: "/usr/share/wordlists/dirb/common.txt"
    max_timeout: 1800
    threads: 50
    
  sqlmap:
    max_level: 3
    max_risk: 2
    batch_mode: true
```

### Security Configuration

**Create `config/security.yaml`**:
```yaml
security:
  enable_auth: true
  api_keys:
    - "your-api-key-1"
    - "your-api-key-2"
  
  rate_limits:
    default: "100 per hour"
    nmap: "10 per hour"
    sqlmap: "5 per hour"
  
  allowed_targets:
    - "scanme.nmap.org"
    - "10.0.0.0/8"
    - "172.16.0.0/12"
    - "192.168.0.0/16"
```

## Verification

### Step 1: Verify Python Environment

```bash
# Check Python version
python --version  # Should be 3.12+

# Check installed packages
pip list

# Verify conda environment
conda info --envs
```

### Step 2: Verify Security Tools

```bash
# Create verification script
cat > verify_tools.py << 'EOF'
#!/usr/bin/env python3
import subprocess
import sys

tools = [
    'nmap', 'gobuster', 'dirb', 'nikto', 'sqlmap',
    'msfconsole', 'hydra', 'john', 'wpscan', 'enum4linux', 'trivy'
]

print("Checking tool availability...\n")

for tool in tools:
    try:
        result = subprocess.run(['which', tool], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {tool}: {result.stdout.strip()}")
        else:
            print(f"✗ {tool}: NOT FOUND")
    except Exception as e:
        print(f"✗ {tool}: ERROR - {e}")

print("\nTool check complete!")
EOF

chmod +x verify_tools.py
python verify_tools.py
```

### Step 3: Test Servers

**Test Kali Server**:
```bash
# Start server
python kali_server.py &

# Wait for startup
sleep 5

# Test health endpoint
curl http://localhost:5000/health

# Test simple command
curl -X POST http://localhost:5000/api/command \
  -H "Content-Type: application/json" \
  -d '{"command": "echo Hello World", "timeout": 10}'
```

**Test Perplexity Server**:
```bash
# Start server
python perplexity_server.py &

# Wait for startup
sleep 5

# Test search
curl -X POST http://localhost:5050/api/perplexity/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is OWASP Top 10?"}'
```

### Step 4: Full System Test

```bash
# Create test script
cat > test_system.sh << 'EOF'
#!/bin/bash

echo "Starting Not-Yet system test..."

# Start all servers
python kali_server.py &
KALI_PID=$!

python perplexity_server.py &
PERPLEXITY_PID=$!

python mcp_server.py &
MCP_PID=$!

# Wait for servers to start
sleep 10

# Test endpoints
echo -e "\n1. Testing Kali Server Health..."
curl -s http://localhost:5000/health | jq .

echo -e "\n2. Testing Nmap Scan..."
curl -s -X POST http://localhost:5000/api/tools/nmap \
  -H "Content-Type: application/json" \
  -d '{"target": "scanme.nmap.org", "options": "-sV -p 22,80", "timeout": 60}' | jq .

echo -e "\n3. Testing Perplexity Search..."
curl -s -X POST http://localhost:5050/api/perplexity/search \
  -H "Content-Type: application/json" \
  -d '{"query": "latest nginx vulnerabilities"}' | jq .

# Cleanup
echo -e "\nCleaning up..."
kill $KALI_PID $PERPLEXITY_PID $MCP_PID

echo "System test complete!"
EOF

chmod +x test_system.sh
./test_system.sh
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port
sudo lsof -i :5000

# Kill process
sudo kill -9 <PID>

# Or use different port
export KALI_SERVER_PORT=5001
```

#### 2. Permission Denied for Tools
```bash
# Some tools need special permissions
sudo setcap cap_net_raw+ep $(which nmap)
sudo setcap cap_net_raw+ep $(which tcpdump)
```

#### 3. Module Import Errors
```bash
# Ensure correct environment
conda activate not-yet

# Reinstall requirements
pip install --force-reinstall -r requirements.txt

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

#### 4. API Key Issues
```bash
# Check environment variable
echo $PERPLEXITY_API_KEY

# Set in current session
export PERPLEXITY_API_KEY="your_key_here"

# Add to .bashrc for persistence
echo 'export PERPLEXITY_API_KEY="your_key_here"' >> ~/.bashrc
```

#### 5. Tool Not Found
```bash
# Update package list
sudo apt update

# Search for package
apt-cache search toolname

# Install missing tool
sudo apt install toolname

# Verify installation
which toolname
```

### Debug Mode

Enable debug mode for detailed logging:
```bash
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG

# Run with debug output
python kali_server.py 2>&1 | tee debug.log
```

### Getting Help

1. **Check Logs**:
```bash
tail -f logs/not-yet.log
```

2. **Verify Configuration**:
```bash
python -c "import os; print(os.environ.get('PERPLEXITY_API_KEY', 'NOT SET'))"
```

3. **Test Individual Components**:
```bash
# Test just the command executor
python -c "from kali_server import execute_command; print(execute_command(['echo', 'test'], 10))"
```

## Next Steps

1. Review the [Security Guide](SECURITY_GUIDE.md) for safe usage
2. Check the [API Reference](API_REFERENCE.md) for endpoint details
3. Read the [Development Guide](DEVELOPMENT_GUIDE.md) to contribute
4. Explore the [Architecture](ARCHITECTURE.md) for system design

## Uninstallation

To completely remove Not-Yet:

```bash
# Remove conda environment
conda deactivate
conda remove -n not-yet --all

# Remove project files
cd ..
rm -rf not-yet

# Remove configuration (optional)
rm -rf ~/.config/claude/claude_config.json

# Remove logs (optional)
rm -rf /var/log/not-yet
```
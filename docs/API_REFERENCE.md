# Not-Yet API Reference

## Overview

Not-Yet provides three interconnected servers that enable AI-powered security testing and analysis:

1. **Kali Server** - RESTful API for Kali Linux security tools
2. **MCP Server** - Model Context Protocol bridge for Claude Desktop
3. **Perplexity Server** - AI-powered search capabilities

## Kali Server API

### Base URL
```
http://localhost:5000
```

### Health Check

#### `GET /health`
Check server status and available tools.

**Response:**
```json
{
  "status": "healthy",
  "available_tools": {
    "curl": true,
    "nmap": true,
    "gobuster": true,
    "dirb": true,
    "nikto": true,
    "sqlmap": true,
    "metasploit": true,
    "hydra": true,
    "john": true,
    "wpscan": true,
    "enum4linux": true,
    "trivy": true
  }
}
```

### Generic Command Execution

#### `POST /api/command`
Execute arbitrary commands on the Kali system.

**Request Body:**
```json
{
  "command": "ls -la",
  "timeout": 60
}
```

**Response:**
```json
{
  "output": "total 48\ndrwxr-xr-x  5 user user 4096...",
  "error": "",
  "return_code": 0
}
```

### Security Tools

#### `POST /api/tools/nmap`
Network discovery and security auditing.

**Request Body:**
```json
{
  "target": "192.168.1.1",
  "options": "-sV -p 1-1000",
  "timeout": 300
}
```

**Response:**
```json
{
  "output": "Starting Nmap 7.94...",
  "error": "",
  "return_code": 0
}
```

#### `POST /api/tools/gobuster`
Directory/file brute-forcing tool.

**Request Body:**
```json
{
  "url": "http://example.com",
  "wordlist": "/usr/share/wordlists/dirb/common.txt",
  "options": "-t 50",
  "timeout": 600
}
```

#### `POST /api/tools/dirb`
Web content scanner.

**Request Body:**
```json
{
  "url": "http://example.com",
  "wordlist": "/usr/share/wordlists/dirb/common.txt",
  "options": "",
  "timeout": 600
}
```

#### `POST /api/tools/nikto`
Web server scanner.

**Request Body:**
```json
{
  "host": "http://example.com",
  "options": "-h",
  "timeout": 1200
}
```

#### `POST /api/tools/sqlmap`
SQL injection detection and exploitation.

**Request Body:**
```json
{
  "url": "http://example.com/page?id=1",
  "options": "--batch --banner",
  "timeout": 1800
}
```

#### `POST /api/tools/metasploit`
Metasploit framework operations.

**Request Body:**
```json
{
  "command": "search ms17-010",
  "timeout": 300
}
```

#### `POST /api/tools/hydra`
Password brute-forcing tool.

**Request Body:**
```json
{
  "target": "192.168.1.1",
  "service": "ssh",
  "userlist": "/usr/share/wordlists/metasploit/unix_users.txt",
  "passlist": "/usr/share/wordlists/metasploit/unix_passwords.txt",
  "options": "",
  "timeout": 1800
}
```

#### `POST /api/tools/john`
Password hash cracking.

**Request Body:**
```json
{
  "hashfile": "/path/to/hashes.txt",
  "options": "--wordlist=/usr/share/wordlists/rockyou.txt",
  "timeout": 3600
}
```

#### `POST /api/tools/wpscan`
WordPress vulnerability scanner.

**Request Body:**
```json
{
  "url": "http://wordpress.example.com",
  "options": "--enumerate p,t,u",
  "timeout": 600
}
```

#### `POST /api/tools/enum4linux`
SMB enumeration tool.

**Request Body:**
```json
{
  "target": "192.168.1.1",
  "options": "-a",
  "timeout": 600
}
```

#### `POST /api/tools/trivy`
Container and filesystem vulnerability scanner.

**Request Body:**
```json
{
  "target": "alpine:latest",
  "options": "--severity HIGH,CRITICAL",
  "timeout": 600
}
```

## Perplexity Server API

### Base URL
```
http://localhost:5050
```

### Search Endpoint

#### `POST /api/perplexity/search`
Perform AI-powered searches using Perplexity.

**Request Body:**
```json
{
  "query": "What are the latest CVEs for Apache Struts?",
  "model": "sonar"
}
```

**Response:**
```json
{
  "status": "success",
  "response": "Here are the latest CVEs for Apache Struts...",
  "citations": [
    {
      "url": "https://nvd.nist.gov/vuln/detail/CVE-2023-50164",
      "title": "NVD - CVE-2023-50164"
    }
  ]
}
```

## MCP Server Tools

The MCP server exposes all functionality through the Model Context Protocol for Claude Desktop integration.

### Available Tools

1. **execute_command** - Run arbitrary commands
2. **nmap_scan** - Network scanning
3. **gobuster_scan** - Directory brute-forcing
4. **dirb_scan** - Web content discovery
5. **nikto_scan** - Web vulnerability scanning
6. **sqlmap_scan** - SQL injection testing
7. **metasploit_command** - Metasploit operations
8. **hydra_attack** - Password brute-forcing
9. **john_crack** - Password hash cracking
10. **wpscan** - WordPress vulnerability scanning
11. **enum4linux_scan** - SMB enumeration
12. **trivy_scan** - Container/filesystem scanning
13. **perplexity_search** - AI-powered search

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "status": "error",
  "return_code": -1
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad request (missing parameters)
- `500` - Internal server error
- `504` - Gateway timeout (operation exceeded timeout)

## Rate Limiting

No built-in rate limiting is implemented. Consider adding a reverse proxy with rate limiting for production use.

## Security Considerations

1. **Authentication**: No authentication is implemented. Secure the servers behind a firewall or VPN.
2. **Command Injection**: The servers execute commands directly. Only use in trusted environments.
3. **Network Access**: Tools may perform network scans. Ensure you have permission to test targets.
4. **Resource Usage**: Long-running scans can consume significant CPU and memory.

## Configuration

### Environment Variables

- `PERPLEXITY_API_KEY` - Required for Perplexity server
- `PERPLEXITY_MODEL` - AI model selection (default: "sonar")
- `API_PORT` - Server port configuration
- `DEBUG_MODE` - Enable debug logging

### Timeouts

Default timeout: 3600 seconds (1 hour)
Configurable per request in the `timeout` field.

## Examples

### Basic Nmap Scan
```bash
curl -X POST http://localhost:5000/api/tools/nmap \
  -H "Content-Type: application/json" \
  -d '{
    "target": "scanme.nmap.org",
    "options": "-sV",
    "timeout": 300
  }'
```

### AI-Powered Security Research
```bash
curl -X POST http://localhost:5050/api/perplexity/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest security vulnerabilities in WordPress 6.4?"
  }'
```

### WordPress Vulnerability Scan
```bash
curl -X POST http://localhost:5000/api/tools/wpscan \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://example-wordpress.com",
    "options": "--enumerate vp,vt",
    "timeout": 900
  }'
```
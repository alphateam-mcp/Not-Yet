# Not-Yet Development Guide

## Getting Started

This guide will help you set up a development environment, understand the codebase, and contribute to the Not-Yet project.

## Development Environment Setup

### Prerequisites

- Kali Linux (recommended) or Debian-based Linux
- Python 3.12+
- Miniconda or Anaconda
- Git
- Claude Desktop (optional for MCP integration)

### Initial Setup

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/not-yet.git
cd not-yet
```

2. **Create Conda Environment**
```bash
conda create -n not-yet python=3.12
conda activate not-yet
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

4. **Set Environment Variables**
```bash
export PERPLEXITY_API_KEY="your_api_key_here"
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
```

5. **Verify Tool Installation**
```bash
# Check that security tools are available
which nmap gobuster dirb nikto sqlmap
```

## Project Structure

```
not-yet/
├── kali_server.py          # Kali tools API server
├── mcp_server.py           # MCP bridge server
├── perplexity_server.py    # AI search server
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── tests/                  # Test suite
│   ├── test_kali_server.py
│   ├── test_mcp_server.py
│   └── test_perplexity_server.py
├── docs/                   # Documentation
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md
│   ├── SECURITY_GUIDE.md
│   └── DEVELOPMENT_GUIDE.md
├── config/                 # Configuration files
│   ├── default.yaml
│   └── development.yaml
├── scripts/                # Utility scripts
│   ├── setup.sh
│   └── test_endpoints.py
└── docker/                 # Docker configurations
    ├── Dockerfile
    └── docker-compose.yml
```

## Development Workflow

### Running the Servers

1. **Start Kali Server**
```bash
python kali_server.py
# Server starts on http://localhost:5000
```

2. **Start Perplexity Server**
```bash
python perplexity_server.py
# Server starts on http://localhost:5050
```

3. **Start MCP Server**
```bash
python mcp_server.py
# MCP server starts and waits for connections
```

### Testing

**Unit Tests**
```bash
pytest tests/ -v
```

**Integration Tests**
```bash
pytest tests/integration/ -v
```

**Coverage Report**
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

**Manual Testing**
```bash
# Test Kali server health
curl http://localhost:5000/health

# Test a simple nmap scan
curl -X POST http://localhost:5000/api/tools/nmap \
  -H "Content-Type: application/json" \
  -d '{"target": "scanme.nmap.org", "options": "-sV", "timeout": 60}'

# Test Perplexity search
curl -X POST http://localhost:5050/api/perplexity/search \
  -H "Content-Type: application/json" \
  -d '{"query": "latest nginx vulnerabilities"}'
```

## Code Style Guide

### Python Style

We follow PEP 8 with some modifications:

```python
# Good: Descriptive function names
def execute_nmap_scan(target: str, options: str = "", timeout: int = 300) -> dict:
    """
    Execute an nmap scan against the specified target.
    
    Args:
        target: IP address or hostname to scan
        options: Additional nmap options
        timeout: Maximum execution time in seconds
    
    Returns:
        Dictionary containing output, error, and return code
    """
    pass

# Good: Type hints and docstrings
from typing import Optional, Dict, List

class SecurityScanner:
    """Base class for security scanning tools."""
    
    def __init__(self, timeout: int = 3600) -> None:
        self.timeout = timeout
        self.results: List[Dict[str, Any]] = []
```

### Error Handling

```python
# Good: Specific exception handling
try:
    result = execute_command(cmd, timeout)
except subprocess.TimeoutExpired:
    logger.warning(f"Command timed out after {timeout} seconds")
    return {"error": "Operation timed out", "partial_output": get_partial_output()}
except subprocess.CalledProcessError as e:
    logger.error(f"Command failed: {e}")
    return {"error": str(e), "return_code": e.returncode}
except Exception as e:
    logger.exception("Unexpected error")
    return {"error": "Internal server error", "details": str(e)}
```

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Good: Structured logging
logger.info("Starting scan", extra={
    "tool": "nmap",
    "target": target,
    "user": user_id,
    "scan_id": scan_id
})
```

## Adding New Features

### Adding a New Security Tool

1. **Create the endpoint in `kali_server.py`**:
```python
@app.route('/api/tools/newtool', methods=['POST'])
def newtool_scan():
    """Execute newtool scan."""
    data = request.json
    
    # Validate parameters
    target = data.get('target')
    if not target:
        return jsonify({"error": "Target is required"}), 400
    
    # Build command
    cmd = ['newtool', target]
    
    # Add options if provided
    options = data.get('options', '')
    if options:
        cmd.extend(shlex.split(options))
    
    # Execute
    timeout = data.get('timeout', DEFAULT_TIMEOUT)
    return execute_command(cmd, timeout)
```

2. **Add to health check**:
```python
def check_tool_availability():
    tools = {
        'newtool': is_tool_available('newtool'),
        # ... other tools
    }
    return tools
```

3. **Register in MCP server**:
```python
@server.tool()
async def newtool_scan(target: str, options: str = "", timeout: int = 3600) -> str:
    """Execute newtool scan.
    
    Args:
        target: Target to scan
        options: Additional options
        timeout: Timeout in seconds
    """
    response = await kali_client.newtool_scan(target, options, timeout)
    return response
```

4. **Add tests**:
```python
def test_newtool_scan():
    response = client.post('/api/tools/newtool', json={
        'target': 'example.com',
        'options': '-v'
    })
    assert response.status_code == 200
    assert 'output' in response.json()
```

### Adding New API Endpoints

1. **Define the route**:
```python
@app.route('/api/new-feature', methods=['POST'])
@require_auth  # Add authentication if needed
@limiter.limit("10 per minute")  # Add rate limiting
def new_feature():
    """Handle new feature requests."""
    data = request.json
    
    # Validate input
    validated_data = validate_new_feature_data(data)
    
    # Process request
    result = process_new_feature(validated_data)
    
    # Return response
    return jsonify(result)
```

2. **Add validation**:
```python
from marshmallow import Schema, fields, validate

class NewFeatureSchema(Schema):
    """Validation schema for new feature."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    type = fields.Str(required=True, validate=validate.OneOf(['type1', 'type2']))
    options = fields.Dict(missing={})
```

3. **Document the endpoint**:
```python
from flask_restful import Resource
from flask_apispec import marshal_with, doc, use_kwargs

class NewFeatureResource(Resource):
    @doc(description='New feature endpoint')
    @use_kwargs(NewFeatureSchema, location='json')
    @marshal_with(ResponseSchema)
    def post(self, **kwargs):
        """Process new feature request."""
        return process_new_feature(kwargs)
```

## Testing Guidelines

### Unit Testing

```python
import pytest
from unittest.mock import patch, Mock

class TestKaliServer:
    """Test cases for Kali server."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_nmap_scan_success(self, client):
        """Test successful nmap scan."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout="Nmap scan report...",
                stderr="",
                returncode=0
            )
            
            response = client.post('/api/tools/nmap', json={
                'target': '127.0.0.1',
                'options': '-sV'
            })
            
            assert response.status_code == 200
            assert 'Nmap scan report' in response.json['output']
    
    def test_nmap_scan_timeout(self, client):
        """Test nmap scan timeout."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired('nmap', 60)
            
            response = client.post('/api/tools/nmap', json={
                'target': '192.168.1.0/24',
                'timeout': 60
            })
            
            assert response.status_code == 504
            assert 'timeout' in response.json['error'].lower()
```

### Integration Testing

```python
import asyncio
from httpx import AsyncClient

class TestIntegration:
    """Integration tests across services."""
    
    @pytest.mark.asyncio
    async def test_mcp_to_kali_integration(self):
        """Test MCP server to Kali server integration."""
        async with AsyncClient() as client:
            # Start servers
            # ... server startup code ...
            
            # Test through MCP
            response = await client.post('http://localhost:8000/execute', json={
                'tool': 'nmap_scan',
                'params': {
                    'target': 'scanme.nmap.org',
                    'options': '-sV'
                }
            })
            
            assert response.status_code == 200
            assert 'Nmap' in response.json()['result']
```

## Debugging

### Debug Mode

Enable debug mode for detailed logging:
```python
# In your server files
if os.environ.get('DEBUG_MODE', 'false').lower() == 'true':
    app.debug = True
    logging.getLogger().setLevel(logging.DEBUG)
```

### Using Debugger

```python
# Add breakpoints
import pdb

def complex_function():
    # ... some code ...
    pdb.set_trace()  # Debugger will stop here
    # ... more code ...
```

### Performance Profiling

```python
import cProfile
import pstats

def profile_function():
    """Profile function performance."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Code to profile
    result = expensive_operation()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
```

## Contributing

### Git Workflow

1. **Fork the repository**
2. **Create a feature branch**
```bash
git checkout -b feature/new-tool-support
```

3. **Make changes and commit**
```bash
git add .
git commit -m "feat: Add support for new security tool"
```

4. **Push to your fork**
```bash
git push origin feature/new-tool-support
```

5. **Create Pull Request**

### Commit Message Format

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

### Code Review Checklist

- [ ] Code follows project style guide
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] Security considerations addressed
- [ ] Performance impact assessed
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate
- [ ] No sensitive data exposed

## Performance Optimization

### Profiling Tools

```bash
# CPU profiling
python -m cProfile -o profile.stats kali_server.py

# Memory profiling
pip install memory-profiler
python -m memory_profiler kali_server.py
```

### Optimization Techniques

1. **Connection Pooling**
```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.3)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
session.mount('http://', adapter)
```

2. **Caching**
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=128)
def get_tool_path(tool_name: str) -> str:
    """Cache tool path lookups."""
    return shutil.which(tool_name)

# For complex caching
from cachetools import TTLCache

cache = TTLCache(maxsize=100, ttl=300)  # 5-minute TTL

def get_cached_result(key: str) -> Optional[dict]:
    return cache.get(key)
```

3. **Async Operations**
```python
import asyncio
import aiohttp

async def fetch_multiple(urls: List[str]) -> List[dict]:
    """Fetch multiple URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_one(session, url) for url in urls]
        return await asyncio.gather(*tasks)
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
```bash
# Find process using port
lsof -i :5000
# Kill process
kill -9 <PID>
```

2. **Permission Denied**
```bash
# Some tools require special permissions
sudo setcap cap_net_raw+ep $(which nmap)
```

3. **Module Import Errors**
```bash
# Ensure you're in the right environment
conda activate not-yet
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Debug Techniques

1. **Request/Response Logging**
```python
@app.before_request
def log_request():
    logger.debug(f"Request: {request.method} {request.path}")
    logger.debug(f"Headers: {dict(request.headers)}")
    logger.debug(f"Body: {request.get_data()}")

@app.after_request
def log_response(response):
    logger.debug(f"Response: {response.status}")
    return response
```

2. **Exception Tracking**
```python
import traceback

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    logger.error(traceback.format_exc())
    return jsonify({"error": "Internal server error"}), 500
```

## Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [FastMCP Documentation](https://github.com/fastmcp/fastmcp)
- [Kali Linux Tools](https://www.kali.org/tools/)

### Security References
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CWE Database](https://cwe.mitre.org/)

### Python Resources
- [Python Security](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Async Python](https://docs.python.org/3/library/asyncio.html)
- [Testing Best Practices](https://docs.pytest.org/en/latest/goodpractices.html)
# Not-Yet Architecture Documentation

## System Overview

Not-Yet is a distributed system that integrates AI capabilities with security testing tools through a microservices architecture. The system consists of three independent servers that communicate via HTTP REST APIs.

## Architecture Diagram

```
┌─────────────────┐
│ Claude Desktop  │
│   (Client)      │
└────────┬────────┘
         │ MCP Protocol
         │
┌────────▼────────┐
│   MCP Server    │
│   (Bridge)      │
└────┬────────┬───┘
     │        │ HTTP
     │        │
┌────▼────┐ ┌─▼──────────┐
│  Kali   │ │ Perplexity │
│ Server  │ │   Server   │
└─────────┘ └────────────┘
```

## Component Architecture

### 1. Kali Server (`kali_server.py`)

**Purpose**: Expose Kali Linux security tools through a RESTful API

**Architecture Pattern**: Command Executor with Thread Pool

```python
# Core Architecture Components
class KaliServer:
    - Flask Application
    - Thread-based Command Executor
    - Tool Registry
    - Health Monitor
```

**Key Design Decisions**:
- **Thread-based Execution**: Allows handling of long-running security scans without blocking
- **Partial Result Capture**: Returns available output even if process times out
- **Tool Abstraction**: Each tool has a dedicated endpoint with parameter validation
- **Graceful Timeout**: Processes are terminated cleanly with partial results preserved

**Request Flow**:
1. HTTP request received at tool endpoint
2. Parameters validated and command constructed
3. Command executed in separate thread
4. Output streamed to result buffer
5. Response returned (complete or partial on timeout)

### 2. MCP Server (`mcp_server.py`)

**Purpose**: Bridge between Claude Desktop and backend services using Model Context Protocol

**Architecture Pattern**: Adapter/Bridge Pattern with Tool Registry

```python
# Core Architecture Components
class MCPServer:
    - FastMCP Framework
    - HTTP Client Adapters (Kali, Perplexity)
    - Tool Registry with Decorators
    - STDIO Transport Layer
```

**Key Design Decisions**:
- **Client Abstraction**: Separate client classes for each backend service
- **Decorator-based Registration**: Tools registered using FastMCP decorators
- **Unified Interface**: Consistent tool interface regardless of backend
- **Error Propagation**: Backend errors cleanly propagated to Claude

**Integration Points**:
- **Input**: MCP protocol messages from Claude Desktop
- **Output**: Structured tool responses via MCP
- **Backend**: HTTP requests to Kali and Perplexity servers

### 3. Perplexity Server (`perplexity_server.py`)

**Purpose**: Provide AI-powered search capabilities for security research

**Architecture Pattern**: Async HTTP Gateway

```python
# Core Architecture Components
class PerplexityServer:
    - Flask Application
    - Async HTTP Client (aiohttp)
    - API Key Management
    - Response Parser
```

**Key Design Decisions**:
- **Async Operations**: Non-blocking API calls to Perplexity
- **Citation Extraction**: Parses and includes source citations
- **Model Flexibility**: Configurable AI model selection
- **Error Handling**: Graceful degradation on API failures

## Data Flow

### Security Tool Execution Flow

```
1. User Request (Claude Desktop)
   ↓
2. MCP Server receives tool call
   ↓
3. HTTP request to Kali Server
   ↓
4. Command execution in thread
   ↓
5. Output streaming to buffer
   ↓
6. Response aggregation
   ↓
7. Return to MCP Server
   ↓
8. Format for Claude Desktop
```

### AI Search Flow

```
1. User Query (Claude Desktop)
   ↓
2. MCP Server receives search request
   ↓
3. HTTP request to Perplexity Server
   ↓
4. Async API call to Perplexity
   ↓
5. Response with citations
   ↓
6. Return to MCP Server
   ↓
7. Format for Claude Desktop
```

## Security Architecture

### Threat Model

1. **Command Injection**: Direct command execution requires trusted environment
2. **Network Exposure**: Servers bind to localhost by default
3. **API Key Security**: Environment variable storage for sensitive keys
4. **Resource Exhaustion**: Long-running scans could consume resources

### Security Controls

1. **Network Isolation**: Bind to localhost only
2. **Input Validation**: Parameter validation at each endpoint
3. **Timeout Protection**: Maximum execution time limits
4. **Process Isolation**: Commands run in separate processes
5. **Error Sanitization**: Sensitive information removed from errors

## Scalability Considerations

### Current Limitations

1. **Single-threaded Flask**: Each server handles one request at a time
2. **Local Execution**: Tools run on the same machine as servers
3. **No Caching**: Results not cached between requests
4. **No Queue**: Long-running operations block subsequent requests

### Scaling Strategies

1. **Horizontal Scaling**: Run multiple server instances behind load balancer
2. **Task Queue**: Implement Redis/Celery for async task management
3. **Result Caching**: Cache common scan results with TTL
4. **Container Deployment**: Docker containers for easy scaling
5. **API Gateway**: Centralized routing and rate limiting

## Error Handling Strategy

### Error Categories

1. **Validation Errors**: Missing or invalid parameters (400)
2. **Execution Errors**: Tool execution failures (500)
3. **Timeout Errors**: Operation exceeded time limit (504)
4. **Network Errors**: Backend communication failures (503)
5. **Resource Errors**: System resource constraints (507)

### Error Response Format

```json
{
  "error": "Descriptive error message",
  "status": "error",
  "return_code": -1,
  "details": {
    "type": "validation|execution|timeout|network|resource",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## Performance Characteristics

### Response Times

- **Simple commands**: 100-500ms
- **Network scans**: 1-60 seconds
- **Vulnerability scans**: 1-60 minutes
- **AI searches**: 2-5 seconds

### Resource Usage

- **Memory**: ~50-200MB per server
- **CPU**: Variable based on tool usage
- **Network**: Depends on scan targets
- **Disk**: Minimal, logs and temp files

## Deployment Architecture

### Development Setup

```
Local Machine (Kali Linux)
├── Conda Environment (Python 3.12)
├── Three Flask Servers (ports 5000, 5050, MCP)
├── Claude Desktop (separate process)
└── Shared filesystem for results
```

### Production Considerations

1. **Containerization**: Docker containers for each service
2. **Orchestration**: Kubernetes for container management
3. **Service Mesh**: Istio for inter-service communication
4. **Monitoring**: Prometheus + Grafana for metrics
5. **Logging**: ELK stack for centralized logging

## Extension Points

### Adding New Tools

1. Create endpoint in `kali_server.py`
2. Add validation logic for parameters
3. Register tool in MCP server
4. Update health check to verify availability

### Adding New AI Models

1. Update Perplexity server for new model support
2. Add model-specific parameters
3. Update response parsing if needed
4. Configure model selection logic

### Adding Authentication

1. Implement JWT or API key middleware
2. Add user management system
3. Implement role-based access control
4. Update all clients with auth headers

## Configuration Management

### Environment Variables

```bash
# Perplexity Server
PERPLEXITY_API_KEY=your_api_key
PERPLEXITY_MODEL=sonar

# Server Ports
KALI_PORT=5000
PERPLEXITY_PORT=5050

# Timeouts
DEFAULT_TIMEOUT=3600
MAX_TIMEOUT=7200

# Debug
DEBUG_MODE=false
LOG_LEVEL=INFO
```

### Configuration Files

Consider implementing:
- `config.yaml` for tool configurations
- `wordlists.json` for default wordlist paths
- `models.json` for AI model configurations
- `limits.json` for resource limits

## Monitoring and Observability

### Metrics to Track

1. **Request Rate**: Requests per second by endpoint
2. **Response Time**: P50, P95, P99 latencies
3. **Error Rate**: Errors by type and endpoint
4. **Resource Usage**: CPU, memory, disk, network
5. **Tool Usage**: Frequency of each tool usage

### Health Checks

1. **Service Health**: Each server's `/health` endpoint
2. **Tool Availability**: Verify tool binaries exist
3. **Backend Connectivity**: Check backend services
4. **Resource Availability**: Disk space, memory
5. **API Key Validity**: Verify external API access

## Future Architecture Considerations

1. **Event-Driven Architecture**: Move to event streaming
2. **Microservices Mesh**: Service-to-service communication
3. **API Gateway**: Centralized API management
4. **Caching Layer**: Redis for result caching
5. **Message Queue**: RabbitMQ/Kafka for async operations
6. **Distributed Tracing**: Jaeger for request tracing
7. **Circuit Breakers**: Resilience patterns
8. **Rate Limiting**: Token bucket algorithm
9. **Multi-tenancy**: User isolation and quotas
10. **Cloud Native**: Kubernetes-native design
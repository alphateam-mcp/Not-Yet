import os
import json
import asyncio
import aiohttp
import time
import logging
from flask import Flask, request, jsonify

# Import monitoring components
try:
    from monitoring.middleware import MonitoringMiddleware, monitor_function, get_health_manager, health_check
    from monitoring.metrics_collector import get_metrics_collector
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    print("Monitoring components not available")

app = Flask(__name__)

# Initialize monitoring if available
if MONITORING_AVAILABLE:
    monitoring = MonitoringMiddleware(app)
    metrics_collector = get_metrics_collector()
    health_manager = get_health_manager()
    print("Monitoring enabled for Perplexity server")
else:
    monitoring = None
    metrics_collector = None
    health_manager = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: 프롬프트 엔지니어링 관련 주석 수정 필요
# PROMPT_TEMPLATES = {
#     "default": [{"role": "system", "content": "Be precise and concise."}]
# }

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


# async def call_perplexity_api(query: str, recency: str, prompt_type: str) -> str:
@monitor_function("perplexity_api_call") if MONITORING_AVAILABLE else lambda x: x
async def call_perplexity_api(query: str) -> str:
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return "PERPLEXITY_API_KEY is not set."

    model = os.getenv("PERPLEXITY_MODEL", "sonar")
    
    # prompt = PROMPT_TEMPLATES.get(prompt_type, PROMPT_TEMPLATES["default"]).copy()
    # prompt.append({"role": "user", "content": query})

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": query},
        ],
        "max_tokens": "512",
        "temperature": 0.2,
        "top_p": 0.9,
        "return_images": False,
        "return_related_questions": False,
 #       "search_recency_filter": recency,
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1,
        "return_citations": True,
        "search_context_size": "low",
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(PERPLEXITY_API_URL, json=payload, headers=headers) as response:
            if response.status != 200:
                return f"Error: {response.status} - {await response.text()}"
            data = await response.json()
            content = data["choices"][0]["message"]["content"]
            if "citations" in data:
                citations = data["citations"]
                formatted_citations = "\n\nCitations:\n" + "\n".join(f"[{i+1}] {url}" for i, url in enumerate(citations))
                return content + formatted_citations
            return content


@app.route("/api/perplexity/search", methods=["POST"])
@monitor_function("perplexity_search") if MONITORING_AVAILABLE else lambda x: x
def search():
    body = request.get_json()
    query = body.get("query")
    # recency = body.get("recency", "month")
    # prompt_type = body.get("prompt_type", "default")

    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    # result = asyncio.run(call_perplexity_api(query, recency, prompt_type))
    result = asyncio.run(call_perplexity_api(query))
    return jsonify({"result": result})


@health_check("perplexity_api") if MONITORING_AVAILABLE else lambda: {}
def check_perplexity_api():
    """Check Perplexity API connectivity"""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return {
            "healthy": False,
            "error": "PERPLEXITY_API_KEY not configured"
        }
    
    try:
        # Simple test - just check if we can make a request structure
        # We don't actually call the API to avoid costs
        return {
            "healthy": True,
            "api_key_configured": bool(api_key),
            "model": os.getenv("PERPLEXITY_MODEL", "sonar")
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }

@app.route("/health", methods=["GET"])
def health():
    """Enhanced health endpoint with monitoring"""
    if MONITORING_AVAILABLE:
        health_results = health_manager.run_all_checks()
        
        response = {
            "status": "healthy" if health_results["overall_healthy"] else "unhealthy",
            "message": "Perplexity API Flask server",
            "server_info": {
                "version": "1.0.0",
                "uptime": time.time() - app.config.get('START_TIME', time.time()),
                "monitoring_enabled": True
            },
            "health_checks": health_results["checks"],
            "overall_healthy": health_results["overall_healthy"],
            "timestamp": health_results["timestamp"]
        }
        
        status_code = 200 if health_results["overall_healthy"] else 503
        return jsonify(response), status_code
    else:
        return jsonify({
            "status": "ok",
            "message": "Perplexity API Flask server running",
            "monitoring_enabled": False
        })


# Add monitoring endpoints
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
        "server_name": "perplexity-server",
        "version": "1.0.0",
        "status": "running",
        "uptime": time.time() - app.config.get('START_TIME', time.time()),
        "monitoring_enabled": MONITORING_AVAILABLE,
        "api_configured": bool(os.getenv("PERPLEXITY_API_KEY"))
    }
    
    if MONITORING_AVAILABLE:
        response["metrics_summary"] = metrics_collector.get_summary_stats()
        response["health_status"] = metrics_collector.get_health_status()
    
    return jsonify(response)

if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 5050))
    
    # Store start time for uptime calculation
    app.config['START_TIME'] = time.time()
    
    # Initialize monitoring if available
    if MONITORING_AVAILABLE:
        logger.info("Monitoring system initialized")
        # Register health checks
        check_perplexity_api()
    
    logger.info(f"Starting Perplexity server on port {port}")
    logger.info(f"Monitoring enabled: {MONITORING_AVAILABLE}")
    
    try:
        app.run(host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        if MONITORING_AVAILABLE and metrics_collector:
            metrics_collector.stop_collection()
    except Exception as e:
        logger.error(f"Server error: {e}")
        if MONITORING_AVAILABLE and metrics_collector:
            metrics_collector.stop_collection()
        raise

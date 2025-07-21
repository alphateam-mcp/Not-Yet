import sys
import os
import argparse
import logging
import asyncio
import json
from typing import Dict, Any, Optional
import requests

from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

DEFAULT_KALI_SERVER = "http://localhost:5000"
DEFAULT_REQUEST_TIMEOUT = 3600

DEFAULT_PERPLEXITY_SERVER = "http://localhost:5050"

class KaliToolsClient:
    def __init__(self, server_url: str, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        logger.info(f"Initialized Kali Tools Client connecting to {server_url}")

    def safe_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if params is None:
            params = {}
        url = f"{self.server_url}/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}", "success": False}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    def safe_post(self, endpoint: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.server_url}/{endpoint}"
        try:
            response = requests.post(url, json=json_data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}", "success": False}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    def execute_command(self, command: str) -> Dict[str, Any]:
        return self.safe_post("api/command", {"command": command})

    def check_health(self) -> Dict[str, Any]:
        return self.safe_get("health")
    
class PerplexityClient:
    def __init__(self, server_url: str, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        logger.info(f"Initialized Perplexity Client connecting to {server_url}")
        
    def safe_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if params is None:
            params = {}
        url = f"{self.server_url}/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}", "success": False}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    def safe_post(self, endpoint: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.server_url}/{endpoint}"
        try:
            response = requests.post(url, json=json_data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Perplexity API request failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}", "success": False}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}
        
    def check_health(self) -> Dict[str, Any]:
        return self.safe_get("health")

def setup_perplexity_tools(perplexity_client: PerplexityClient):
    @mcp.tool()
    def perplexity_search(query: str):
    # def perplexity_search(query: str, recency: str = "month", prompt_type: str = "default"):
        return perplexity_client.safe_post("api/perplexity/search", {
            "query": query
            # "prompt_type": prompt_type
        })

mcp = FastMCP("kali + sbom")

def setup_kali_tools(kali_client: KaliToolsClient):
    @mcp.tool()
    def nmap_scan(target: str, scan_type: str = "-sV", ports: str = "", additional_args: str = ""):
        return kali_client.safe_post("api/tools/nmap", {
            "target": target, "scan_type": scan_type, "ports": ports, "additional_args": additional_args
        })

    @mcp.tool()
    def gobuster_scan(url: str, mode: str = "dir", wordlist: str = "/usr/share/wordlists/dirb/common.txt", additional_args: str = ""):
        return kali_client.safe_post("api/tools/gobuster", {
            "url": url, "mode": mode, "wordlist": wordlist, "additional_args": additional_args
        })

    @mcp.tool()
    def dirb_scan(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt", additional_args: str = ""):
        return kali_client.safe_post("api/tools/dirb", {
            "url": url, "wordlist": wordlist, "additional_args": additional_args
        })

    @mcp.tool()
    def nikto_scan(target: str, additional_args: str = ""):
        return kali_client.safe_post("api/tools/nikto", {
            "target": target, "additional_args": additional_args
        })

    @mcp.tool()
    def sqlmap_scan(url: str, data: str = "", additional_args: str = ""):
        return kali_client.safe_post("api/tools/sqlmap", {
            "url": url, "data": data, "additional_args": additional_args
        })

    @mcp.tool()
    def metasploit_run(module: str, options: Dict[str, Any] = {}):
        return kali_client.safe_post("api/tools/metasploit", {
            "module": module, "options": options
        })

    @mcp.tool()
    def hydra_attack(target: str, service: str, username: str = "", username_file: str = "", password: str = "", password_file: str = "", additional_args: str = ""):
        return kali_client.safe_post("api/tools/hydra", {
            "target": target, "service": service, "username": username, "username_file": username_file,
            "password": password, "password_file": password_file, "additional_args": additional_args
        })

    @mcp.tool()
    def john_crack(hash_file: str, wordlist: str = "/usr/share/wordlists/rockyou.txt", format_type: str = "", additional_args: str = ""):
        return kali_client.safe_post("api/tools/john", {
            "hash_file": hash_file, "wordlist": wordlist, "format": format_type, "additional_args": additional_args
        })

    @mcp.tool()
    def wpscan_analyze(url: str, additional_args: str = ""):
        return kali_client.safe_post("api/tools/wpscan", {
            "url": url, "additional_args": additional_args
        })

    @mcp.tool()
    def enum4linux_scan(target: str, additional_args: str = "-a"):
        return kali_client.safe_post("api/tools/enum4linux", {
            "target": target, "additional_args": additional_args
        })
        
    @mcp.tool()
    def curl(target : str):
        return kali_client.safe_post("api/tools/curl", {
            "target": target
        })
        
    @mcp.tool()
    def trivy(file_path: str):
        return kali_client.safe_post("api/tools/trivy", {
            "file_path" : file_path
        })
        
    @mcp.tool()
    def syft(directory: str):
    	return kali_client.safe_post("api/tools/syft", {
    	    "directory" : directory
    	})

    @mcp.tool()
    def server_health():
        return kali_client.check_health()

    @mcp.tool()
    def execute_command(command: str):
        return kali_client.execute_command(command)

@mcp.tool()
async def sbom_scan(file_content: Any, filename: str):
    try:
        logger.info(f"Starting Trivy scan for file: {filename}")
        temp_path = f"/tmp/{filename}"

        with open(temp_path, "w") as f:
            if isinstance(file_content, dict):
                json.dump(file_content, f, indent=2)
            else:
                f.write(file_content)
        
        cmd = [ "trivy", "fs", "--format", "cyclonedx", "--scanners", "vuln", "--output", "sbom.json", temp_path]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        os.remove(temp_path)

        if process.returncode == 0:
            with open("sbom.json", "r") as f:
                return json.load(f)
        else:
            return {"error": stderr.decode()}

    except Exception as e:
        logger.error(f"Exception in sbom_scan: {str(e)}")
        return {"error": str(e)}
    
def parse_args():
    parser = argparse.ArgumentParser(description="Run the kali + sbom MCP Client")
    parser.add_argument("--server", type=str, default=DEFAULT_KALI_SERVER, help=f"Kali API server URL (default: {DEFAULT_KALI_SERVER})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_REQUEST_TIMEOUT, help=f"Request timeout in seconds (default: {DEFAULT_REQUEST_TIMEOUT})")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def main():
    args = parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    kali_client = KaliToolsClient(args.server, args.timeout)
    setup_kali_tools(kali_client)
    perplexity_server = os.getenv("PERPLEXITY_SERVER", DEFAULT_PERPLEXITY_SERVER)
    perplexity_client = PerplexityClient(perplexity_server, args.timeout)
    setup_perplexity_tools(perplexity_client)
    logger.info("Starting kali + sbom MCP server")
    logger.info(f"Starting Perplexity server")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()

# Not-Yet

This project consists of three distinct server applications: a Kali server, a MCP server, and a Perplexity server. Each server provides different functionalities, including screen capturing, executing commands, and interacting with the Perplexity API.

## Features

### Kali Server (`kali_server.py`)

*   *Tool-Specific Endpoints*: *Exposes widely-used tools like nmap, gobuster, sqlmap, metasploit, hydra,
         trivy, and syft through dedicated API endpoints (e.g., /api/tools/nmap).* 
*   *Generic Command Execution*: *Includes a flexible /api/command endpoint to run arbitrary shell commands.*
*   *Robustness*:*Implements a CommandExecutor class with a timeout mechanism to ensure the server remains
         stable and does not hang on long-running processes.* 

### MCP Server (`mcp_server.py`)

*   * Client Integration*:* Contains KaliToolsClient and PerplexityClient classes to communicate with the
         other two servers.* 
*   *Tool Abstraction*:* Uses the @mcp.tool() decorator to register functions from both kali_server (e.g.,
         nmap_scan) and perplexity_server (e.g., perplexity_search) into a common framework.* 

### Perplexity Server (`perplexity_server.py`)

*   * AI Search Endpoint*:*Offers a /api/perplexity/search endpoint that takes a natural language query and
         retrieves an answer from Perplexity AI.* 

## Installation

The Installation is based on kali-linux and [Claude-Desktop](Claude-Desktop.md)

1.  Install the miniconda
    ```bash
    mkdir -p ~/miniconda3
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
    rm ~/miniconda3/miniconda.sh
    ```
2.  Initialize Conda
    ```bash
    source ~/miniconda3/bin/activate
    conda init --all
    ```
3.  Create the virtual environment and activate
    ```bash
    conda create -n <your-env-name> python=3.12 -y
    conda activate <your-env-name>
    ```
4.  Clone the repository:
    ```bash
    git clone https://github.com/alphateam-mcp/Not-Yet.
    ```
5.  Install the dependencies
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Set the API Key

    ```bash
    conda env config vars set PERPLEXITY_API_KEY="<your-key>"
    ```

Each server can be run individually.

### Kali Server

To run the Kali server, execute the following command:

    ```bash
    python kali_server.py
    ```

The server will start on `0.0.0.0:5000`.

### MCP Server

To run the MCP server, configure the claude_desktop

    ```bash
    {
        "mcpServers": {
            "kali_mcp": {
                "command": "/home/<your-username>/miniconda3/envs/kali-MCP/bin/python3",
                "args": [
                    "/home/<your-username>/Desktop/MCP-Kali-Server/mcp_server.py",
                    "--server",
                    "http://10.0.2.15:5000/"
                ]
            }
        }
    }   
    ```

### Perplexity Server

To run the Perplexity server, execute the following command:

```bash
python perplexity_server.py
```

The server will start on `0.0.0.0:5050`.

## Tools

### Kali Server

*   `curl`: Runs the curl command to fetch content from a URL.
*   `nmap_scan`: Performs network scans using nmap. 
*   `gobuster_scan`: Uses gobuster for directory/file brute-forcing and DNS subdomain enumeration. 
*   `dirb_scan`: Scans web servers for hidden directories using dirb.
*   `nikto_scan`: Scans web servers for vulnerabilities using nikto. 
*   `sqlmap_scan`: Detects and exploits SQL injection vulnerabilities with sqlmap.
*   `metasploit_run` : Executes a specified Metasploit module by generating a temporary resource script.
*   `hydra_attack` : Performs brute-force password attacks using hydra.
*   `john_crack` : Cracks password hashes using John the Ripper.
*   `wpscan_analyze` : Scans WordPress sites for known vulnerabilities with wpscan.
*   `enum4linux_scan` : Enumerates information from Windows and Linux systems using enum4linux.
*   `trivy` : Generates a CycloneDX SBOM from a package-lock.json file and scans for vulnerabilities.

### MCP Server

*   `setup_tools`: Define Tools in kali and perplexity server. 
*   `Client.safe_post`: Communicates with kali and perplexity server. 

### Perplexity Server

*   `call_perplexity_api`: Call the perplexity for Searching PoC for Dependency Problem. 

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

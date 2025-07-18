simple usage

OS : Kali Linux 2025.2

## 콘다 설치
```bash
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh
```
## Trivy 설치
```bash
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor | sudo tee /usr/share/keyrings/trivy.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy
```

## 콘다 초기화
```bash
source ~/miniconda3/bin/activate
conda init --all
```
## 환경 설치 및 설정
```bash
conda create -n Kali-MCP python=3.12 -y
conda activate Kali-MCP
pip install requests flask flask-cors psutil python-nmap mcp aiohttp
export PERPLEXITY_API_KEY="your-key"
conda deactivate Kali-MCP
conda activate Kali-MCP
```
## 깃 클론
```bash
git clone https://github.com/alphateam-mcp/Not-Yet.git
cd Not-Yet
```

## 실행 방법 1 (터미널 2개 필요)
(Terminel 1)
```bash
python kali_server.py
```
(Terminel 2)
```bash
python perplexity_server.py
```
### claude_desktop_config.json 설정
```json
{
    "mcpServers": {
        "kali_mcp": {
            "command": "/home/{username}/miniconda3/envs/kali-MCP/bin/python3",
            "args": [
                "/home/{username}/Desktop/MCP-Kali-Server/mcp_server.py",
                "--server",
                "your kali_server IP:PORT"
            ]
        }
    }
}
```
## 실행 방법 2 (터미널 1개 필요)
```bash
git clone https://github.com/ppl-ai/modelcontextprotocol.git
cd modelcontextprotocol/perplexity-ask && npm install

python kali_server.py
```
### claude_desktop_config.json
``` json
{
    "mcpServers": {
        "kali_mcp": {
            "command": "/home/{username}/miniconda3/envs/kali-MCP/bin/python3",
            "args": [
                "/home/{username}/Desktop/MCP-Kali-Server/mcp_server.py",
                "--server",
                "your kali_server IP:PORT"
            ]
        },
        "perplexity-ask": {
        	"command": "npx",
        	"args": [
          	  "-y",
          	  "server-perplexity-ask"
        	],
        	"env" : {
          	  "PERPLEXITY_API_KEY": "your-key"
        	}
    	}
    }
}
```

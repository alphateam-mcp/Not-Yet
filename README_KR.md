simple usage

OS : Kali Linux 2025.2

# 콘다 설치

mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh

# 콘다 초기화

source ~/miniconda3/bin/activate
conda init --all

# 환경 설치 및 설정

conda create -n Kali-MCP python=3.12 -y
conda activate Kali-MCP
pip install requests flask flask-cors psutil python-nmap mcp aiohttp
export PERPLEXITY_API_KEY="your-key"
conda deactivate Kali-MCP
conda activate Kali-MCP

git clone https://github.com/alphateam-mcp/Not-Yet.git
cd Not-Yet

(Terminel 1)
python kali_server.py
(Terminel 2)
python perplexity_server.py

claude_desktop_config.json 설정
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

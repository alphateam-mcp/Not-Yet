# Claude Desktop

## Installation

1. Clone the repository
    ```bash
    git clone https://github.com/aaddrick/claude-desktop-debian.git
    ```
2. Set up the Node version
    ```bash
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
    sudo apt install -y nodejs
    node -v # Check Node version is up to 22.12.0
    ```
3. Create Claude-Desktop in linux
    ```bash
    cd claude-desktop-debian
    ./build.sh --build deb --clean yes # Check .deb file creation
    sudo dpkg -i ./claude-desktop_0.12.20_amd64.deb  # Check .deb file name
    ```

## Usage
    ```bash
    claude-desktop
    ```

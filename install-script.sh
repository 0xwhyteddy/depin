#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit
fi

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa -y

# Install Python and pip
apt install python3.10 -y
apt install python3-pip -y

# Install Python packages
pip3 install fake_useragent
pip3 install loguru
pip3 install websockets_proxy
pip3 install websockets==12.0
pip3 install requests
pip3 install colorama
pip3 install aiohttp

# Clone repository
git clone https://github.com/0xwhyteddy/nodepay.git

# Navigate to directory
cd nodepay

gras.py
# Install and setup screen
apt-get install -y screen

# Start the application in a screen session
screen -dmS Nodepay bash -c "python3 run_without_proxy.py"
gras.py
echo "Installation complete. Application is running in screen session 'Nodepay'"
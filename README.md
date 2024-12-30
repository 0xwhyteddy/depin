
- For Ubuntu 18.04 | 20.04 | 22.04 (VPS)
```
- Install Python 3.10
apt update && sudo apt upgrade -y
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa
apt install python3.10
apt install python3-pip
- Install Requirements
pip install requests
pip install asyncio
pip install aiohttp
pip install loguru
pip install cloudscraper
pip install curl_cffi
pip install fake_useragent==1.5.1
- Run
python3 run_without_proxy_multi_new.py
```

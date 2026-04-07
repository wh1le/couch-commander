import json
import os

TV_IP = "192.168.50.160"
KEY_FILE = os.path.expanduser("~/.config/lgtv/keys.json")


def load_key(ip=TV_IP):
    try:
        with open(KEY_FILE) as f:
            data = json.load(f)
            return data.get(ip)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_key(key, ip=TV_IP):
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    data = {}
    try:
        with open(KEY_FILE) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    data[ip] = key
    with open(KEY_FILE, "w") as f:
        json.dump(data, f, indent=2)

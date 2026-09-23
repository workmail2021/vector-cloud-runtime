#!/usr/bin/env python3
"""
ИИ-ВЕКТОР: УТИЛИТА СИНХРОНИЗАЦИИ ЗАМЕТОК И ДАННЫХ С ОБЛАКОМ 24/7
Использование:
  python3 sync_vector_data.py pull   - Скачать все заметки и задачи из облака на ноутбук
  python3 sync_vector_data.py push   - Отправить локальные заметки с ноутбука в облако
  python3 sync_vector_data.py status - Проверить статус облачного сервиса Вектор
"""

import os
import sys
import json
import urllib.request
import ssl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_FILE = os.path.join(BASE_DIR, "notes.json")
REMOTE_URL = "https://vector-ai-assistant.onrender.com"
SYNC_SECRET = "vec_sec_99a8b7c6d5e4f3a2b1029384756"

def check_status():
    ctx = ssl.create_default_context()
    url = f"{REMOTE_URL}/api/status"
    print(f"📡 Проверка статуса облачного Вектора: {url}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VectorSync/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"🟢 [ОБЛАКО ОНЛАЙН] Статус: {data.get('status')} | Бот: {data.get('bot')} | Сервис: {data.get('service')}")
            return True
    except Exception as e:
        print(f"🔴 [ОБЛАКО НЕДОСТУПНО] {e}")
        return False

def cmd_pull():
    ctx = ssl.create_default_context()
    url = f"{REMOTE_URL}/api/sync_notes?secret={SYNC_SECRET}"
    print(f"📥 [PULL] Скачивание заметок из облака...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VectorSync/1.0", "X-Sync-Secret": SYNC_SECRET})
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                notes = data.get("notes", [])
                with open(NOTES_FILE, "w", encoding="utf-8") as f:
                    json.dump(notes, f, ensure_ascii=False, indent=2)
                print(f"✅ [PULL УСПЕШНО] Заметок обновлено: {len(notes)}")
                return True
    except Exception as e:
        print(f"❌ [PULL СБОЙ] {e}")
        return False

def cmd_push():
    ctx = ssl.create_default_context()
    url = f"{REMOTE_URL}/api/sync_notes?secret={SYNC_SECRET}"
    notes = []
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                notes = json.load(f)
        except Exception:
            pass
    print(f"📤 [PUSH] Отправка {len(notes)} заметок в облако...")
    try:
        payload = json.dumps({"notes": notes}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "VectorSync/1.0", "X-Sync-Secret": SYNC_SECRET})
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                print("✅ [PUSH УСПЕШНО] Данные синхронизированы в облаке!")
                return True
    except Exception as e:
        print(f"❌ [PUSH СБОЙ] {e}")
        return False

if __name__ == "__main__":
    action = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    if action == "pull":
        cmd_pull()
    elif action == "push":
        cmd_push()
    else:
        check_status()

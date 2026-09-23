#!/usr/bin/env python3
import urllib.request
import urllib.parse
import json
import os
import sys
import time

CONFIG_PATH = os.path.expanduser("~/.config/antigravity-email/config.json")
AUTHORIZED_CHAT_ID = 6375883079 # Strict lock to Sergey Romanov ONLY

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def send_telegram_message(message_text, token=None, chat_id=None):
    config = load_config()
    bot_token = token or config.get("telegram_bot_token")
    target_chat_id = chat_id or config.get("telegram_chat_id") or AUTHORIZED_CHAT_ID

    if not bot_token or not target_chat_id:
        print("Telegram не настроен.")
        return False

    if int(target_chat_id) != AUTHORIZED_CHAT_ID:
        print(f"🔒 [БЕЗОПАСНОСТЬ ВЕКТОРА] Попытка отправки на неавторизованный ID {target_chat_id} заблокирована!")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": f"🎯 <b>ВЕКТОР (Ваш ИИ-Ассистент):</b>\n\n{message_text}",
        "parse_mode": "HTML"
    }

    for attempt in range(3):
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=12) as response:
                res = json.loads(response.read().decode("utf-8"))
                if res.get("ok"):
                    return True
                else:
                    print(f"Ошибка Telegram API: {res}")
                    return False
        except Exception as e:
            if attempt == 2:
                print(f"Ошибка отправки сообщения: {e}")
                return False
            time.sleep(1)
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
        send_telegram_message(msg)

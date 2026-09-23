#!/usr/bin/env python3
"""
ИИ-ВЕКТОР: АВТОНОМНЫЙ ДИСПЕТЧЕР И ИСПОЛНИТЕЛЬ ЗАДАЧ ИЗ TELEGRAM НА ПК (24/7)
Позволяет Сергею Романову голосом или текстом из Telegram ставить любые технические,
программные или инфраструктурные задачи, которые мгновенно и автономно исполняются на ПК.
"""

import os
import sys
import re
import json
import time
import subprocess
import threading
import urllib.request
import html

BASE_DIR = "/home/home/Документы/2"
AUTHORIZED_CHAT_ID = 6375883079

try:
    from autonomous_agent_bridge import is_agent_execution_request, execute_agent_task_on_pc
except ImportError:
    sys.path.insert(0, BASE_DIR)
    from autonomous_agent_bridge import is_agent_execution_request, execute_agent_task_on_pc

ACTION_KEYWORDS = [
    "исправь", "почини", "сделай", "добавь", "удали", "перезапусти", "проверь", 
    "проанализируй", "настрой", "запусти", "задача", "поставь задачу", "выполни",
    "обнови", "протестируй", "замени", "отремонтируй", "создай", "agy", "antigravity",
    "терминал", "консоль", "команда", "бэкап", "логи", "ошибки", "службы"
]

def get_bot_token():
    cfg_path = os.path.expanduser("~/.config/antigravity-email/config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f).get("telegram_bot_token")
        except Exception:
            pass
    return None

def send_telegram_msg(chat_id, text, reply_markup=None):
    token = get_bot_token()
    if not token:
        print("Telegram bot token not found")
        return {"ok": False}
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
        return {"ok": False, "error": str(e)}

def is_execution_directive(text: str) -> bool:
    """Определяет, является ли сообщение владельца прямой задачей к исполнению на ПК."""
    if not text:
        return False
    t = text.lower().strip()
    
    # Исключаем чисто информационные запросы
    if t.startswith(("напомни", "какая погода", "курс", "сколько ехать", "посчитай", "калькулятор", "/models", "/limits", "/help", "/start", "/menu")):
        return False
        
    if is_agent_execution_request(text):
        return True

    for kw in ACTION_KEYWORDS:
        if kw in t:
            return True
    return False

def execute_autonomous_task(task_text: str, chat_id: int = AUTHORIZED_CHAT_ID):
    """Фоновый исполнитель задачи на ПК с полным циклом реального исполнения и отчетности."""
    # 1. Отправляем подтверждение приема задачи
    ack = (
        "⚙️ <b>ЗАДАЧА ПРИНЯТА В АВТОНОМНУЮ ОБРАБОТКУ НА ПК</b>\n\n"
        f"🎯 <b>Суть:</b> «<i>{html.escape(task_text[:250])}</i>»\n"
        "⏳ <i>ИИ-Движок проводит анализ, исполнение команд и верификацию...</i>"
    )
    send_telegram_msg(chat_id, ack)
    
    # 2. Реальное выполнение задачи через исполнительный мост ПК
    result_report = execute_agent_task_on_pc(task_text, user_id=chat_id)
    
    # 3. Фиксация задачи в TASKS_REGISTRY.md
    try:
        tasks_file = os.path.join(BASE_DIR, "TASKS_REGISTRY.md")
        with open(tasks_file, "a", encoding="utf-8") as f:
            f.write(f"\n* 🟢 **[Telegram-Задача {time.strftime('%d.%m %H:%M')}]**: {task_text} — *Выполнено автономно*\n")
    except Exception as e:
        print(f"Ошибка записи в реестр: {e}")

    # 4. Отправка итогового детального отчета владельцу в Telegram
    send_telegram_msg(chat_id, result_report)

def dispatch_task_async(task_text: str, chat_id: int = AUTHORIZED_CHAT_ID):
    """Асинхронный запуск выполнения задачи в отдельном фоновом потоке."""
    th = threading.Thread(target=execute_autonomous_task, args=(task_text, chat_id), daemon=True)
    th.start()
    return True

if __name__ == "__main__":
    test_cmd = "Проверь статус всех служб и запусти сквозное тестирование 24 тестов"
    print("Directive check:", is_execution_directive(test_cmd))
    execute_autonomous_task(test_cmd, chat_id=6375883079)
    print("Done!")

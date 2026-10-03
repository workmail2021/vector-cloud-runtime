#!/usr/bin/env python3
"""
ИИ-ВЕКТОР: Raycast-Style Telegram Inline Mode (Inline Query Handler 1.0)
Позволяет вызывать бота прямо из любого чата через @vsr_guard_bot:
- @vsr_guard_bot 615 [объект] -> Статус объекта, открытые задачи и бюджет в 1 клик.
- @vsr_guard_bot pass [сервис] -> Быстрый защищенный доступ к паролям.
- @vsr_guard_bot note [поиск] -> Мгновенная отправка нужной заметки в чат.
- @vsr_guard_bot help -> Интерактивная подсказка быстрых команд.
"""

import os
import sys
import json
import hashlib
import time
import html
import urllib.request
import urllib.parse

PROJECT_ROOT = "/home/home/Документы/2"
CONFIG_FILE = os.path.expanduser("~/.config/antigravity-email/config.json")
AUTHORIZED_CHAT_ID = 6375883079

def _get_bot_token() -> str:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("telegram_bot_token", "")
    except Exception:
        return ""

def handle_inline_query(inline_query: dict):
    """
    Обрабатывает событие inline_query от Telegram Bot API и шлет answerInlineQuery.
    """
    query_id = inline_query.get("id")
    from_user = inline_query.get("from", {})
    user_id = from_user.get("id")
    raw_query = inline_query.get("query", "").strip()

    # Защита: инлайн-режим доступен только авторизованному владельцу
    if int(user_id) != AUTHORIZED_CHAT_ID:
        _send_empty_inline_response(query_id)
        return

    results = []
    q_lower = raw_query.lower()

    # ── 1. КОМАНДЫ ПО ОБЪЕКТАМ 615-ФЗ ─────────────────────────────
    if "615" in q_lower or any(obj in q_lower for obj in ["котово", "дубовк", "михайловк", "фролово"]):
        from rag_knowledge_engine import query_rag_knowledge
        summary = query_rag_knowledge(raw_query or "615 Котово")
        results.append({
            "type": "article",
            "id": "inline_615_" + hashlib.md5(raw_query.encode()).hexdigest()[:8],
            "title": "[615-ФЗ] Статус и расходы",
            "description": "Сводка бюджета, КС-2 и открытых задач по объекту",
            "input_message_content": {
                "message_text": summary.get("text", "Нет данных"),
                "parse_mode": "HTML"
            }
        })

    # ── 2. БЫСТРЫЙ ДОСТУП К ПАРОЛЯМ (VAULT) ───────────────────────
    elif q_lower.startswith("pass") or "парол" in q_lower:
        from vault_manager import get_vault_data
        vault = get_vault_data()
        services = vault.get("services", {})
        term = q_lower.replace("pass", "").replace("пароль", "").strip()
        
        for s_name, s_data in services.items():
            if not term or term in s_name.lower():
                login = s_data.get("login", "")
                note = s_data.get("note", "")
                pwd = s_data.get("password", "")
                masked_pwd = pwd[:2] + ("*" * (len(pwd) - 4)) + pwd[-2:] if len(pwd) > 4 else "****"
                
                msg_content = (
                    f"<b>Учетные данные: {html.escape(s_name)}</b>\n\n"
                    f"• Логин: <code>{html.escape(login)}</code>\n"
                    f"• Пароль: <code>{html.escape(pwd)}</code>\n"
                    f"• Примечание: <i>{html.escape(note)}</i>"
                )
                
                results.append({
                    "type": "article",
                    "id": f"inline_vault_{hashlib.md5(s_name.encode()).hexdigest()[:8]}",
                    "title": f"[VAULT] {s_name}",
                    "description": f"Логин: {login} | Пароль: {masked_pwd}",
                    "input_message_content": {
                        "message_text": msg_content,
                        "parse_mode": "HTML"
                    }
                })

    # ── 3. ПОИСК ПО БАЗЕ ЗАМЕТОК ─────────────────────────────────
    elif q_lower.startswith("note") or "заметк" in q_lower:
        from notes_module import get_all_notes
        term = q_lower.replace("note", "").replace("заметка", "").strip()
        notes = get_all_notes()
        count = 0
        for n in notes:
            txt = str(n.get("text", ""))
            cat = str(n.get("category", "Общее"))
            if not term or term in txt.lower() or term in cat.lower():
                nid = n.get("id", count + 1)
                results.append({
                    "type": "article",
                    "id": f"inline_note_{nid}",
                    "title": f"#{nid} [{cat}]",
                    "description": txt[:80],
                    "input_message_content": {
                        "message_text": f"<b>Заметка #{nid} [{html.escape(cat)}]</b>\n\n{html.escape(txt)}",
                        "parse_mode": "HTML"
                    }
                })
                count += 1
                if count >= 5:
                    break

    # ── 4. ДЕФОЛТНОЕ МЕНЮ БЫСТРЫХ ДЕЙСТВИЙ (RAYCAST HUD) ──────────
    if not results:
        results = [
            {
                "type": "article",
                "id": "inline_hud_615",
                "title": "[615-ФЗ] Объекты (Котово / Дубовка)",
                "description": "Напечатайте: @vsr_guard_bot 615",
                "input_message_content": {
                    "message_text": "<b>615-ФЗ:</b> Для сводки введите: <code>@vsr_guard_bot 615 Котово</code>",
                    "parse_mode": "HTML"
                }
            },
            {
                "type": "article",
                "id": "inline_hud_pass",
                "title": "[VAULT] Менеджер паролей",
                "description": "Напечатайте: @vsr_guard_bot pass почта",
                "input_message_content": {
                    "message_text": "<b>Пароли:</b> Введите: <code>@vsr_guard_bot pass Mail</code>",
                    "parse_mode": "HTML"
                }
            },
            {
                "type": "article",
                "id": "inline_hud_notes",
                "title": "[ЗАМЕТКИ] База знаний",
                "description": "Напечатайте: @vsr_guard_bot note [слово]",
                "input_message_content": {
                    "message_text": "<b>Заметки:</b> Введите: <code>@vsr_guard_bot note бокс</code>",
                    "parse_mode": "HTML"
                }
            }
        ]

    _send_inline_results(query_id, results)

def _send_inline_results(query_id: str, results: list):
    token = _get_bot_token()
    if not token or not query_id:
        return
    try:
        url = f"https://api.telegram.org/bot{token}/answerInlineQuery"
        payload = json.dumps({
            "inline_query_id": query_id,
            "results": results[:10],
            "cache_time": 5,
            "is_personal": True
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            pass
    except Exception:
        pass

def _send_empty_inline_response(query_id: str):
    _send_inline_results(query_id, [])

#!/usr/bin/env python3
"""
ИИ-Вектор: Менеджер безопасно хранимых учетных данных (Логины и пароли 3.0)
с умным естественным разобором словосочетаний, сквозной нумерацией #1, #2, #3
и мгновенным копированием в 1 тач в Telegram.
"""

import os
import json
import re

def _get_vault_path():
    # 1. Local project file (in current script dir)
    local_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault.json")
    if os.path.exists(local_p):
        return local_p
    # 2. Project root in /home/home/Документы/2
    doc_p = "/home/home/Документы/2/vault.json"
    if os.path.exists(doc_p):
        return doc_p
    # 3. User config fallback
    cfg_p = os.path.expanduser("~/.config/antigravity-email/vault.json")
    if os.path.exists(cfg_p):
        return cfg_p
    return local_p

VAULT_PATH = _get_vault_path()

def _ensure_vault_exists():
    v_path = _get_vault_path()
    os.makedirs(os.path.dirname(v_path), exist_ok=True)
    if not os.path.exists(v_path):
        initial_data = {"version": "1.0", "services": {}}
        with open(v_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
        try:
            os.chmod(v_path, 0o600)
        except Exception:
            pass

def get_vault_data():
    _ensure_vault_exists()
    v_path = _get_vault_path()
    try:
        with open(v_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"services": {}}

def save_service_credential(service_name, login, password_or_token, note=""):
    _ensure_vault_exists()
    data = get_vault_data()
    data["services"][service_name] = {
        "login": login,
        "password": password_or_token,
        "note": note
    }
    
    # Сохраняем во все доступные локации для гарантии синхронизации ПК и Облака
    paths_to_save = set([
        _get_vault_path(),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault.json"),
        os.path.expanduser("~/.config/antigravity-email/vault.json"),
        "/home/home/Документы/2/vault.json"
    ])
    
    for p in paths_to_save:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            try:
                os.chmod(p, 0o600)
            except Exception:
                pass
        except Exception:
            pass
    return True

def smart_add_credential_from_text(text):
    text_clean = text.strip()
    text_lower = text_clean.lower()
    
    # Проверяем наличие ключевых маркеров категории паролей
    is_password_request = any(kw in text_lower for kw in [
        "пароль", "пароли", "паролей", "логин", "логины", "vault", 
        "папку пароли", "в пароли", "сохрани пароль", "добавь пароль", "учетка"
    ])

    if not is_password_request:
        return False, None, None, None

    # Очищаем префиксы («добавь в папку пароли», «сохрани пароль от», «пароли:» и т.д.)
    cleaned = re.sub(
        r'^(?:добавь|сохрани|запиши|внеси)?\s*(?:в|к)?\s*(?:папку|раздел|хранилище)?\s*(?:пароль|пароли|паролей|логины?|логин)\s*(?:от|для)?\s*:?\s*',
        '', text_clean, flags=re.I
    ).strip()

    # Дополнительная очистка начальных "от " / "для "
    cleaned = re.sub(r'^(?:от|для)\s+', '', cleaned, flags=re.I).strip()

    # 1. Забористое регулярное выражение с логином и паролем
    m_full = re.search(r'(.+?)\s+логин\s+([^\s]+)\s+пароль\s+([^\s]+)', cleaned, re.I)
    if m_full:
        s_name = m_full.group(1).strip().title()
        login = m_full.group(2).strip()
        pwd = m_full.group(3).strip()
        save_service_credential(s_name, login, pwd)
        return True, s_name, login, pwd

    # 2. Деление очищенного текста по пробелам
    parts = cleaned.split()
    if len(parts) >= 3:
        # Сервис (все слова кроме последних двух), Логин (предпоследнее), Пароль (последнее)
        s_name = " ".join(parts[:-2]).strip().title()
        login = parts[-2].strip()
        pwd = parts[-1].strip()
        if not s_name:
            s_name = "Общий Сервис"
        save_service_credential(s_name, login, pwd)
        return True, s_name, login, pwd
    elif len(parts) == 2:
        s_name = parts[0].strip().title()
        pwd = parts[1].strip()
        save_service_credential(s_name, "Не указан", pwd)
        return True, s_name, "Не указан", pwd
    elif len(parts) == 1:
        pwd = parts[0].strip()
        s_name = "Мой Пароль"
        save_service_credential(s_name, "Не указан", pwd)
        return True, s_name, "Не указан", pwd

    return False, None, None, None

def delete_vault_credential_smart(query):
    _ensure_vault_exists()
    data = get_vault_data()
    services = data.get("services", {})
    query_lower = query.lower().strip()

    # 1. Поиск ВСЕХ цифр в запросе (например, "удали 5, 6, 7" или "удали пароли 5 6")
    nums = [int(n) for n in re.findall(r'\b\d+\b', query)]
    deleted_keys = []

    if nums:
        keys_list = list(services.keys())
        # Сортируем в обратном порядке по индексам чтобы не смещались
        valid_indices = sorted(list(set([i for i in nums if 1 <= i <= len(keys_list)])), reverse=True)
        for idx in valid_indices:
            del_key = keys_list[idx - 1]
            if del_key in data["services"]:
                del data["services"][del_key]
                deleted_keys.append(del_key)

        if deleted_keys:
            with open(VAULT_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.chmod(VAULT_PATH, 0o600)
            return ", ".join(reversed(deleted_keys))

    # 2. Поиск по имени или псевдонимам
    aliases = {
        "инста": "Instagram", "инстаграм": "Instagram", "instagram": "Instagram",
        "почта": "Mail.ru", "mail": "Mail.ru", "телеграм": "Telegram Bot (Вектор)",
        "gemini": "Google Gemini Pro", "гугл": "Google Gemini Pro"
    }

    for alias_key, real_name in aliases.items():
        if alias_key in query_lower and real_name in services:
            del data["services"][real_name]
            with open(VAULT_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.chmod(VAULT_PATH, 0o600)
            return real_name

    for k in list(services.keys()):
        if k.lower() in query_lower or query_lower in k.lower():
            del data["services"][k]
            with open(VAULT_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.chmod(VAULT_PATH, 0o600)
            return k

    return None

def format_vault_summary_html():
    data = get_vault_data()
    services = data.get("services", {})
    
    if not services:
        return (
            "🔐 <b>БЕЗОПАСНОЕ ХРАНИЛИЩЕ ПАРОЛЕЙ (ВЕКТОР):</b>\n\n"
            "Хранилище сейчас пустое.\n\n"
            "💬 <b>Как добавить пароль:</b>\n"
            "Напишите или надиктуйте голосом:\n"
            "<code>Пароль от Госуслуги 79033156444 Pass123</code>"
        )

    lines = ["🔐 <b>БЕЗОПАСНОЕ ХРАНИЛИЩЕ ПАРОЛЕЙ ВЕКТОР 3.0:</b>\n"]
    lines.append("<i>Все логины и пароли копируются в 1 касание по коду!</i>\n")

    for idx, (s_name, s_info) in enumerate(services.items(), start=1):
        lines.append(f"<b>#{idx}. 📌 {s_name}</b>")
        login_val = s_info.get("login", "Не указан")
        pwd_val = s_info.get("password") or s_info.get("app_password") or s_info.get("bot_token") or "—"
        
        lines.append(f" • 👤 Логин: <code>{login_val}</code>")
        lines.append(f" • 🔑 Пароль: <code>{pwd_val}</code>\n")

    lines.append("💬 <i>Удаление: «Удали пароль #1» или «Удали пароль Instagram»</i>")
    return "\n".join(lines)

# Стандартные псевдонимы для совместимости
load_vault = get_vault_data
save_vault = save_service_credential

if __name__ == "__main__":
    _ensure_vault_exists()
    print(format_vault_summary_html())

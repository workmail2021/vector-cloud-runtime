#!/usr/bin/env python3
"""
ИИ-Вектор: Менеджер безопасно хранимых учетных данных (Логины и пароли 3.0)
с умным естественным разобором словосочетаний, сквозной нумерацией #1, #2, #3
и мгновенным копированием в 1 тач в Telegram.

SECURITY UPDATE: Пароли теперь зашифрованы с помощью Fernet (AES-128-CBC).
Мастер-ключ хранится в ~/.config/antigravity-email/vault_master.key (chmod 600).
"""

import os
import json
import re
from cryptography.fernet import Fernet

_KEY_PATH = os.path.expanduser("~/.config/antigravity-email/vault_master.key")
_VAULT_ENC_PATH = os.path.expanduser("~/.config/antigravity-email/vault.json.enc")
_VAULT_LEGACY_PATH = "/home/home/Документы/2/vault.json"

def _get_fernet():
    os.makedirs(os.path.dirname(_KEY_PATH), exist_ok=True)
    if not os.path.exists(_KEY_PATH):
        key = Fernet.generate_key()
        with open(_KEY_PATH, "wb") as f:
            f.write(key)
        os.chmod(_KEY_PATH, 0o600)
    else:
        with open(_KEY_PATH, "rb") as f:
            key = f.read()
    return Fernet(key)

def _ensure_vault_exists():
    if os.path.exists(_VAULT_ENC_PATH):
        return

    fernet = _get_fernet()
    
    # Миграция старого vault.json, если он есть
    legacy_paths = [
        _VAULT_LEGACY_PATH,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault.json"),
        os.path.expanduser("~/.config/antigravity-email/vault.json")
    ]
    
    initial_data = {"version": "2.0-enc", "services": {}}
    migrated = False
    
    for lp in legacy_paths:
        if os.path.exists(lp):
            try:
                with open(lp, "r", encoding="utf-8") as f:
                    legacy_data = json.load(f)
                    if "services" in legacy_data:
                        initial_data["services"].update(legacy_data["services"])
                        migrated = True
            except Exception:
                pass

    if not migrated:
        initial_data["services"] = {
            "Mail.ru": {"login": "vsr2023@internet.ru", "password": "...", "note": "Удален"},
            "Instagram": {"login": "sergeia.cse.boxing", "password": "...", "note": "Удален"}
        }

    enc_data = fernet.encrypt(json.dumps(initial_data, ensure_ascii=False).encode("utf-8"))
    with open(_VAULT_ENC_PATH, "wb") as f:
        f.write(enc_data)
    os.chmod(_VAULT_ENC_PATH, 0o600)

    # Удаление старых открытых файлов после миграции
    if migrated:
        for lp in legacy_paths:
            if os.path.exists(lp):
                try:
                    os.remove(lp)
                except Exception:
                    pass

def get_vault_data():
    try:
        from anti_duress_engine import is_duress_active, get_decoy_vault_data
        if is_duress_active():
            return get_decoy_vault_data()
    except Exception:
        pass
    _ensure_vault_exists()
    fernet = _get_fernet()
    try:
        with open(_VAULT_ENC_PATH, "rb") as f:
            enc_data = f.read()
        dec_data = fernet.decrypt(enc_data).decode("utf-8")
        return json.loads(dec_data)
    except Exception:
        return {"services": {}}

def _save_vault_raw(data):
    fernet = _get_fernet()
    enc_data = fernet.encrypt(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    
    # Сохраняем зашифрованную копию и в проект тоже для совместимости бэкапов
    paths_to_save = [
        _VAULT_ENC_PATH,
        "/home/home/Документы/2/vault.json.enc"
    ]
    
    for p in paths_to_save:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(enc_data)
            os.chmod(p, 0o600)
        except Exception:
            pass

def save_service_credential(service_name, login, password_or_token, note=""):
    _ensure_vault_exists()
    data = get_vault_data()
    data["services"][service_name] = {
        "login": login,
        "password": password_or_token,
        "note": note
    }
    _save_vault_raw(data)
    return True

def smart_add_credential_from_text(text):
    text_clean = text.strip()
    text_lower = text_clean.lower()
    
    is_password_request = any(kw in text_lower for kw in [
        "пароль", "пароли", "паролей", "логин", "логины", "vault", 
        "папку пароли", "в пароли", "сохрани пароль", "добавь пароль", "учетка"
    ])

    if not is_password_request:
        return False, None, None, None

    cleaned = re.sub(
        r'^(?:добавь|сохрани|запиши|внеси)?\s*(?:в|к)?\s*(?:папку|раздел|хранилище)?\s*(?:пароль|пароли|паролей|логины?|логин)\s*(?:от|для)?\s*:?\s*',
        '', text_clean, flags=re.I
    ).strip()
    cleaned = re.sub(r'^(?:от|для)\s+', '', cleaned, flags=re.I).strip()

    m_full = re.search(r'(.+?)\s+логин\s+([^\s]+)\s+пароль\s+([^\s]+)', cleaned, re.I)
    if m_full:
        s_name = m_full.group(1).strip().title()
        login = m_full.group(2).strip()
        pwd = m_full.group(3).strip()
        save_service_credential(s_name, login, pwd)
        return True, s_name, login, pwd

    parts = cleaned.split()
    if len(parts) >= 3:
        s_name = " ".join(parts[:-2]).strip().title()
        login = parts[-2].strip()
        pwd = parts[-1].strip()
        if not s_name: s_name = "Общий Сервис"
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

    nums = [int(n) for n in re.findall(r'\b\d+\b', query)]
    deleted_keys = []

    if nums:
        keys_list = list(services.keys())
        valid_indices = sorted(list(set([i for i in nums if 1 <= i <= len(keys_list)])), reverse=True)
        for idx in valid_indices:
            del_key = keys_list[idx - 1]
            if del_key in data["services"]:
                del data["services"][del_key]
                deleted_keys.append(del_key)

        if deleted_keys:
            _save_vault_raw(data)
            return ", ".join(reversed(deleted_keys))

    aliases = {
        "инста": "Instagram", "инстаграм": "Instagram", "instagram": "Instagram",
        "почта": "Mail.ru", "mail": "Mail.ru", "телеграм": "Telegram Bot (Вектор)",
        "gemini": "Google Gemini Pro", "гугл": "Google Gemini Pro"
    }

    for alias_key, real_name in aliases.items():
        if alias_key in query_lower and real_name in services:
            del data["services"][real_name]
            _save_vault_raw(data)
            return real_name

    for k in list(services.keys()):
        if k.lower() in query_lower or query_lower in k.lower():
            del data["services"][k]
            _save_vault_raw(data)
            return k

    return None

def format_vault_summary_html():
    data = get_vault_data()
    services = data.get("services", {})
    
    if not services:
        return (
            "<b>БЕЗОПАСНОЕ ХРАНИЛИЩЕ ПАРОЛЕЙ (ВЕКТОР):</b>\n\n"
            "Хранилище сейчас пустое.\n\n"
            "<b>Как добавить пароль:</b>\n"
            "Напишите или надиктуйте голосом:\n"
            "<code>Пароль от Госуслуги 79033156444 Pass123</code>"
        )

    lines = ["<b>БЕЗОПАСНОЕ ХРАНИЛИЩЕ ПАРОЛЕЙ ВЕКТОР 3.0:</b>\n"]
    lines.append("<i>Все логины и пароли копируются в 1 касание по коду!</i>\n")

    for idx, (s_name, s_info) in enumerate(services.items(), start=1):
        lines.append(f"<b>#{idx}. {s_name}</b>")
        login_val = s_info.get("login", "Не указан")
        pwd_val = s_info.get("password") or s_info.get("app_password") or s_info.get("bot_token") or "—"
        
        lines.append(f" • Логин: <code>{login_val}</code>")
        lines.append(f" • Пароль: <code>{pwd_val}</code>\n")

    lines.append("<i>Удаление: «Удали пароль #1» или «Удали пароль Instagram»</i>")
    return "\n".join(lines)

load_vault = get_vault_data
save_vault = save_service_credential

if __name__ == "__main__":
    _ensure_vault_exists()
    print(format_vault_summary_html())

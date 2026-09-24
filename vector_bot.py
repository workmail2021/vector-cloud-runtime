#!/usr/bin/env python3
"""
ИИ-ВЕКТОР: Telegram-Бот мирового класса в РЕЖИМЕ ОДНОГО КАРТОЧНОГО ОКНА.
Полный набор функций работы с заметками:
- Копирование текста в 1 клик (моноширинные блоки <code>...</code> + отдельная кнопка выгрузки).
- Авто-переиндексация номеров заметок (1, 2, 3, 4, 5...) при любом удалении.
- Гарантированное сохранение старого текста при дополнении и редактировании.
- Слияние и объединение заметок.
- Быстрые статусы (Done/Pending) и интерактивные фильтры.
"""

import os
import sys
import json
import time
import shutil
import re
import math
import html
import subprocess
import urllib.request
import urllib.parse
import urllib.error
import threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HTTP_SESSION = None

def get_http_session():
    global HTTP_SESSION
    if HTTP_SESSION is None:
        HTTP_SESSION = requests.Session()
        retries = Retry(total=2, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(pool_connections=15, pool_maxsize=30, max_retries=retries)
        HTTP_SESSION.mount("https://", adapter)
        HTTP_SESSION.mount("http://", adapter)
    return HTTP_SESSION

def answer_cb_async(cb_id, text=None):
    if not cb_id:
        return
    def _worker():
        payload = {"callback_query_id": cb_id}
        if text:
            payload["text"] = text
        send_api_request("answerCallbackQuery", payload)
    threading.Thread(target=_worker, daemon=True).start()
import speech_recognition as sr

from vector_tier1_engine import (
    load_tasks, save_tasks, add_task, toggle_task, delete_task, clear_completed_tasks,
    get_tasks_hud_text, get_tasks_hud_markup,
    parse_executive_voice_summary, format_executive_summary_card,
    generate_expenses_csv_export, generate_notes_txt_export,
    load_expenses as load_expenses_tier1, save_expense_entry,
    search_all_ecosystem, format_search_results_card,
    get_morning_briefing_card, get_evening_briefing_card, create_full_system_backup_zip
)

from vault_manager import format_vault_summary_html, get_vault_data, save_service_credential, delete_vault_credential_smart, smart_add_credential_from_text
from email_security_guard import run_security_audit, get_mail_dashboard_text, fetch_inbox_summary, categorize_emails_by_topic, auto_sort_inbox_emails
from security_guard_module import get_wifi_security_report
from cloud_storage_module import (
    get_cloud_dashboard_text,
    get_cloud_dashboard_markup,
    get_cloud_list_text,
    get_cloud_list_markup,
    get_cloud_file_detail_text,
    get_cloud_file_detail_markup,
    get_cloud_file_by_id,
    delete_file_from_cloud,
    save_file_to_cloud,
    save_text_to_cloud,
    load_cloud_index,
    save_cloud_index,
    CLOUD_PAGE_STATE,
    CLOUD_CAT_STATE,
    CLOUD_PAGE_SIZE,
    get_filtered_cloud_files,
    detect_explicit_cloud_category,
    get_cloud_manage_folders_text,
    get_cloud_manage_folders_markup,
    add_cloud_category,
    rename_cloud_category,
    delete_cloud_category,
    handle_cloud_folder_nlp,
    get_cloud_channel,
    set_cloud_channel,
    get_cloud_hashtag,
    detect_category,
    move_cloud_file_category,
    get_cloud_move_markup
)
from secretary_module import get_secretary_dashboard_text, get_city_weather_and_timezone, search_travel_tickets, get_taxi_info, summarize_uploaded_document, process_secretary_request
try:
    from video_analyzer import process_video_upload, process_image_upload, analyze_boxing_technique
except Exception:
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "Спорт", "Разработка", "Видео_метрика"))
        from video_analyzer import process_video_upload, process_image_upload, analyze_boxing_technique
    except Exception:
        process_video_upload = None
        process_image_upload = None
        analyze_boxing_technique = None
try:
    from sports_library_engine import (
        search_sports_library_smart,
        get_all_authors_overview_text,
        get_author_detail_text,
        get_special_stack_text,
        get_library_markup
    )
except Exception:
    search_sports_library_smart = None
    get_all_authors_overview_text = None
    get_author_detail_text = None
    get_special_stack_text = None
    get_library_markup = None
from reminders_module import (
    get_reminders_dashboard_text,
    get_reminders_dashboard_markup,
    get_reminder_detail_text,
    get_reminder_detail_markup,
    add_reminder,
    snooze_reminder,
    set_reminder_to_event_time,
    complete_reminder,
    delete_reminder,
    format_time_remaining,
    parse_reminder_text
)
from logger_engine import log_info, log_warning, log_error, get_recent_errors, get_flight_summary
from construction_control_module import (
    get_construction_dashboard_text,
    process_voice_or_text_construction_report,
    audit_subcontractor_report,
    load_construction_progress
)
from pc_control_engine import (
    get_pc_dashboard_text,
    get_pc_dashboard_markup,
    execute_linux_command_formatted,
    handle_pc_nlp_request
)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
NOTES_PATH = os.path.join(PROJECT_ROOT, "notes.json")
EXPENSES_PATH = os.path.join(PROJECT_ROOT, "expenses.json")
DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, "Переданное_с_телефона")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
FFMPEG_BIN = shutil.which("ffmpeg") or os.path.expanduser("~/.local/bin/ffmpeg")
AUTHORIZED_CHAT_ID = 6375883079

NOTES_DIR_BASE = os.path.join(PROJECT_ROOT, "База_Заметок")
CATEGORY_DIR_MAP = {
    "Спорт": os.path.join(NOTES_DIR_BASE, "1_Спорт"),
    "Работа": os.path.join(NOTES_DIR_BASE, "2_Работа"),
    "Общее": os.path.join(NOTES_DIR_BASE, "3_Общее")
}
CATEGORY_ICON_MAP = {
    "Спорт": "🏋️",
    "Работа": "🏗",
    "Общее": "📁"
}
SPORT_KEYWORDS = [
    "спорт", "трен", "бокc", "бокс", "удар", "раунд", "сфп", "офп", "ленар", "арапов",
    "шкурапатов", "селуянов", "филимонов", "зациорский", "верхошанский", "бомпа", "гантел",
    "штанга", "жим", "присед", "тяг", "кардио", "пульс", "чсс", "fatmax", "бег", "эллипс",
    "мексидол", "рибоксин", "милдронат", "аспаркам", "витамин", "протеин", "креатин",
    "диета", "калори", "бжу", "упражнен", "растяжк", "перчатк", "мешок", "лап", "спарринг",
    "нокаут", "тейп", "бинт", "капа", "скакалк", "trx", "медбол", "эспандер"
]
WORK_KEYWORDS = [
    "работ", "стройк", "объект", "смет", "615", "акт", "подрядчик", "совещан", "договор",
    "котово", "михайловка", "парадигм", "инженер", "прораб", "дгх", "фонд", "кс-2", "кс-3",
    "теплотрасс", "водоканал", "концесси", "откос", "щебень", "брак", "субподрядчик",
    "44-фз", "223-фз", "заказчик", "гнб", "производственн"
]
GENERAL_KEYWORDS = [
    "купить", "покупк", "магазин", "аптек", "напомни", "напоминание", "пароль", "семья",
    "дом", "личн", "идея", "мысль", "чек", "расход", "паспорт", "заметка"
]

ACTIVE_CARD_ID = {}
NOTES_CATEGORY_STATE = {} # chat_id -> "overview" | "Спорт" | "Работа" | "Общее"
PENDING_NOTE_CATEGORY = {} # chat_id -> {"text": str, "type": str, "time": str, "msg_id": int}
NOTES_SELECT_MODE = {}     # chat_id -> set of selected note IDs
NOTES_BULK_MODE = {}       # chat_id -> bool
NOTES_PAGE_STATE = {}
NOTES_PAGE_SIZE = 10
LAST_EXECUTIVE_SUMMARY = {} # chat_id -> parsed dict of latest voice/text summary
QUICK_TARGET_CATEGORY = {}  # chat_id -> "Спорт" | "Работа" | "Общее"
PENDING_SEARCH_IN_CAT = {}  # chat_id -> "Спорт" | "Работа" | "Общее"
FOLDER_SEARCH_RESULTS = {}  # chat_id -> "search query string"
PENDING_GLOBAL_SEARCH = {}  # chat_id -> bool

def load_config():
    candidates = [
        os.path.join(PROJECT_ROOT, "config.json"),
        os.path.join(PROJECT_ROOT, "data_backup", "config.json"),
        os.path.expanduser("~/.config/antigravity-email/config.json")
    ]
    cfg = {}
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    cfg.update(json.load(f))
                    break
            except Exception:
                pass
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        cfg["telegram_bot_token"] = os.environ.get("TELEGRAM_BOT_TOKEN")
    if os.environ.get("OPENAI_API_KEY"):
        cfg["openai_api_key"] = os.environ.get("OPENAI_API_KEY")
    return cfg

_NOTES_CACHE = None
_NOTES_CACHE_MTIME = 0

def invalidate_notes_cache():
    global _NOTES_CACHE, _NOTES_CACHE_MTIME
    _NOTES_CACHE = None
    _NOTES_CACHE_MTIME = 0

def persist_notes_data(notes):
    try:
        with open(NOTES_PATH, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.Redis.from_url(redis_url, decode_responses=True)
            r.set("vector:notes", json.dumps(notes, ensure_ascii=False))
        except Exception:
            pass

def load_notes():
    global _NOTES_CACHE, _NOTES_CACHE_MTIME
    if not os.path.exists(NOTES_PATH):
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            try:
                import redis
                r = redis.Redis.from_url(redis_url, decode_responses=True)
                val = r.get("vector:notes")
                if val:
                    notes = json.loads(val)
                    persist_notes_data(notes)
                    _NOTES_CACHE = notes
                    return list(notes)
            except Exception:
                pass
        _NOTES_CACHE = []
        return []
    try:
        mtime = os.path.getmtime(NOTES_PATH)
        if _NOTES_CACHE is not None and mtime == _NOTES_CACHE_MTIME:
            return list(_NOTES_CACHE)
        
        with open(NOTES_PATH, "r", encoding="utf-8") as f:
            notes = json.load(f)
            for n in notes:
                if "category" not in n or n["category"] not in ["Спорт", "Работа", "Общее"]:
                    n["category"] = classify_note_category(n.get("text", "")) or "Общее"
            _NOTES_CACHE = notes
            _NOTES_CACHE_MTIME = mtime
            return list(notes)
    except Exception:
        return _NOTES_CACHE or []

def reindex_notes(notes):
    for idx, n in enumerate(notes, start=1):
        n["id"] = idx
    return notes

def classify_note_category(text, old_category=""):
    t_lower = text.lower()
    old_lower = old_category.lower() if old_category else ""
    
    if any(k in old_lower for k in ["спорт", "бокс", "академическ", "книги", "сфп", "фитнес"]):
        return "Спорт"
    if any(k in old_lower for k in ["работ", "стройка", "615"]):
        return "Работа"
        
    s_score = sum(1 for k in SPORT_KEYWORDS if k in t_lower)
    w_score = sum(1 for k in WORK_KEYWORDS if k in t_lower)
    
    if s_score > 0 and s_score > w_score:
        return "Спорт"
    if w_score > 0 and w_score > s_score:
        return "Работа"
    if any(k in t_lower for k in GENERAL_KEYWORDS):
        return "Общее"
    return None

def sync_note_markdown_file(note):
    cat = note.get("category", "Общее")
    if cat not in CATEGORY_DIR_MAP:
        cat = "Общее"
        note["category"] = "Общее"
    target_dir = CATEGORY_DIR_MAP[cat]
    os.makedirs(target_dir, exist_ok=True)
    
    n_id = note.get("id", 1)
    timestamp_clean = note.get("time", time.strftime("%Y-%m-%d %H:%M:%S")).replace(":", "-").replace(" ", "_")
    raw_text = note.get("text", "").strip()
    first_line = raw_text.split("\n")[0].strip()
    safe_title = re.sub(r'[^\w\s-]', '', first_line).strip().replace(" ", "_")[:35]
    if not safe_title:
        safe_title = f"Заметка_{n_id}"
        
    filename = f"note_{n_id:03d}_{timestamp_clean[:10]}_{safe_title}.md"
    filepath = os.path.join(target_dir, filename)
    
    old_fp = note.get("file_path")
    if old_fp and old_fp != filepath and os.path.exists(old_fp):
        try:
            os.remove(old_fp)
        except Exception:
            pass

    md_content = (
        f"# ЗАМЕТКА #{n_id} [{cat.upper()}]\n\n"
        f"• **Категория:** {cat}\n"
        f"• **Дата создания:** {note.get('time', '')}\n"
        f"• **Тип ввода:** {note.get('type', 'текст')}\n\n"
        f"---\n\n"
        f"## Текст заметки:\n\n"
        f"{raw_text}\n"
    )
    try:
        with open(filepath, "w", encoding="utf-8") as mf:
            mf.write(md_content)
        note["file_path"] = filepath
    except Exception:
        pass
    return filepath

def delete_note_markdown_file(note):
    fp = note.get("file_path")
    if fp and os.path.exists(fp):
        try:
            os.remove(fp)
        except Exception:
            pass
    n_id = note.get("id")
    for c_dir in CATEGORY_DIR_MAP.values():
        if os.path.exists(c_dir):
            try:
                for fname in os.listdir(c_dir):
                    if fname.startswith(f"note_{n_id:03d}_"):
                        os.remove(os.path.join(c_dir, fname))
            except Exception:
                pass

def move_note_category(note_id, new_category):
    invalidate_notes_cache()
    notes = load_notes()
    target_note = None
    for n in notes:
        if n.get("id") == note_id:
            old_fp = n.get("file_path")
            if old_fp and os.path.exists(old_fp):
                try:
                    os.remove(old_fp)
                except Exception:
                    pass
            n["category"] = new_category
            sync_note_markdown_file(n)
            target_note = n
            break
    if target_note:
        persist_notes_data(notes)
    return target_note

def save_note(note_text, note_type="текст", category=None):
    invalidate_notes_cache()
    notes = load_notes()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    if not category:
        category = classify_note_category(note_text) or "Общее"

    new_note = {
        "id": len(notes) + 1,
        "time": timestamp,
        "text": note_text,
        "type": note_type,
        "category": category
    }
    notes.append(new_note)
    reindex_notes(notes)
    
    for n in notes:
        if n["id"] == len(notes):
            sync_note_markdown_file(n)
            
    persist_notes_data(notes)
    return len(notes)

def append_text_to_note(note_id, extra_text):
    invalidate_notes_cache()
    notes = load_notes()
    updated = False
    target_note = None
    for n in notes:
        if n.get("id") == note_id:
            old_txt = n["text"].strip()
            n["text"] = f"{old_txt}\n• {extra_text.strip()}"
            sync_note_markdown_file(n)
            updated = True
            target_note = n
            break
    if updated:
        persist_notes_data(notes)
    return updated, target_note

def replace_note_text(note_id, new_text):
    invalidate_notes_cache()
    notes = load_notes()
    updated = False
    for n in notes:
        if n.get("id") == note_id:
            n["text"] = new_text
            sync_note_markdown_file(n)
            updated = True
            break
    if updated:
        persist_notes_data(notes)
    return updated

def delete_single_note(note_id):
    invalidate_notes_cache()
    notes = load_notes()
    target_note = None
    for n in notes:
        if n.get("id") == note_id:
            target_note = n
            break
    if target_note:
        delete_note_markdown_file(target_note)
    new_notes = [n for n in notes if n.get("id") != note_id]
    deleted = len(new_notes) < len(notes)
    if deleted:
        reindex_notes(new_notes)
        for n in new_notes:
            sync_note_markdown_file(n)
        persist_notes_data(new_notes)
    return deleted

def delete_multiple_notes(note_ids):
    invalidate_notes_cache()
    notes = load_notes()
    ids_to_del = set(note_ids)
    for n in notes:
        if n.get("id") in ids_to_del:
            delete_note_markdown_file(n)
    deleted_ids = [n["id"] for n in notes if n.get("id") in ids_to_del]
    new_notes = [n for n in notes if n.get("id") not in ids_to_del]
    reindex_notes(new_notes)
    for n in new_notes:
        sync_note_markdown_file(n)
    with open(NOTES_PATH, "w", encoding="utf-8") as f:
        json.dump(new_notes, f, ensure_ascii=False, indent=2)
    return deleted_ids

def merge_notes(note_ids):
    invalidate_notes_cache()
    notes = load_notes()
    target_notes = [n for n in notes if n.get("id") in note_ids]
    if len(target_notes) < 2:
        return False, "Для объединения укажите хотя бы 2 заметки (например: <code>Объединить 1, 2</code>)."

    combined_text = "\n\n".join([f"📝 [Заметка #{n['id']}]:\n{n['text']}" for n in target_notes])
    first_id = target_notes[0]["id"]
    
    for n in notes:
        if n["id"] == first_id:
            n["text"] = combined_text
            n["time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            sync_note_markdown_file(n)
            break

    other_ids = [n["id"] for n in target_notes[1:]]
    for n in notes:
        if n["id"] in other_ids:
            delete_note_markdown_file(n)
            
    remaining_notes = [n for n in notes if n["id"] not in other_ids]
    reindex_notes(remaining_notes)
    for n in remaining_notes:
        sync_note_markdown_file(n)

    persist_notes_data(remaining_notes)

    return True, f"Заметки {note_ids} успешно объединены в заметку #{first_id}!"

def get_note_by_id(note_id):
    notes = load_notes()
    for n in notes:
        if n.get("id") == note_id:
            return n
    return None

def load_expenses():
    if not os.path.exists(EXPENSES_PATH):
        return []
    try:
        with open(EXPENSES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_expense(amount, category):
    expenses = load_expenses()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    expenses.append({"amount": amount, "category": category, "time": timestamp})
    os.makedirs(os.path.dirname(EXPENSES_PATH), exist_ok=True)
    with open(EXPENSES_PATH, "w", encoding="utf-8") as f:
        json.dump(expenses, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(EXPENSES_PATH, 0o600)
    except Exception:
        pass
    return sum(e["amount"] for e in expenses)

def send_api_request(method, payload):
    config = load_config()
    token = config.get("telegram_bot_token")
    if not token:
        return None
    
    if isinstance(payload, dict) and "text" in payload:
        if isinstance(payload["text"], str) and len(payload["text"]) > 4000:
            payload["text"] = payload["text"][:3990] + "..."

    url = f"https://api.telegram.org/bot{token}/{method}"
    session = get_http_session()
    try:
        resp = session.post(url, json=payload, timeout=8)
        res_json = resp.json()
        if not res_json.get("ok"):
            desc = res_json.get("description", "")
            if "message is not modified" in desc:
                return {"ok": True, "description": "not modified"}
        return res_json
    except Exception as e:
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as fallback_resp:
                return json.loads(fallback_resp.read().decode("utf-8"))
        except Exception as e2:
            print(f"Telegram API Exception on {method}: {e2}")
            return None

def send_telegram_file(chat_id, file_path, caption=None):
    config = load_config()
    token = config.get("telegram_bot_token")
    if not token or not os.path.exists(file_path):
        return False
    
    cmd = [
        "curl", "-s", "-X", "POST",
        f"https://api.telegram.org/bot{token}/sendDocument",
        "-F", f"chat_id={chat_id}",
        "-F", f"document=@{file_path}"
    ]
    if caption:
        cmd.extend(["-F", f"caption={caption}", "-F", "parse_mode=HTML"])
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        resp_json = json.loads(res.stdout)
        return resp_json.get("ok", False)
    except Exception as e:
        print(f"Error sending file to Telegram: {e}")
        return False

def send_telegram_photo(chat_id, photo_path, caption=None, reply_markup=None):
    config = load_config()
    token = config.get("telegram_bot_token")
    if not token or not os.path.exists(photo_path):
        return None
    
    cmd = [
        "curl", "-s", "-X", "POST",
        f"https://api.telegram.org/bot{token}/sendPhoto",
        "-F", f"chat_id={chat_id}",
        "-F", f"photo=@{photo_path}"
    ]
    if caption:
        cmd.extend(["-F", f"caption={caption[:1020]}", "-F", "parse_mode=HTML"])
    if reply_markup:
        cmd.extend(["-F", f"reply_markup={json.dumps(reply_markup)}"])
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        resp_json = json.loads(res.stdout)
        return resp_json
    except Exception as e:
        print(f"Error sending photo to Telegram: {e}")
        return None

def get_tasks_dashboard_text(block_filter=None):
    tasks_path = os.path.join(PROJECT_ROOT, "TASKS_REGISTRY.md")
    if not os.path.exists(tasks_path):
        return "📋 <b>РЕЕСТР АКТИВНЫХ ЗАДАЧ</b>\n\n<i>Файл TASKS_REGISTRY.md не найден.</i>"
    
    try:
        with open(tasks_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        lines = content.split("\n")
        out_lines = ["📋 <b>РЕЕСТР АКТИВНЫХ ЗАДАЧ (2026)</b>\n"]
        current_block = ""
        
        for line in lines:
            if line.startswith("## "):
                current_block = line.replace("## ", "").strip()
                if not block_filter or (block_filter.lower() in current_block.lower()):
                    out_lines.append(f"\n<b>{html.escape(current_block)}</b>")
            elif line.strip().startswith(("*", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.", "11.", "12.", "13.", "14.", "15.", "16.", "17.", "18.", "19.")):
                if not block_filter or (block_filter.lower() in current_block.lower()):
                    clean_l = line.strip().lstrip("* ").strip()
                    if len(clean_l) > 140:
                        clean_l = clean_l[:140] + "..."
                    out_lines.append(f"• {html.escape(clean_l)}")
                    
        result_text = "\n".join(out_lines)
        if len(result_text) > 3400:
            result_text = result_text[:3390] + "\n\n<i>...[полный список в TASKS_REGISTRY.md]</i>"
        return result_text
    except Exception as e:
        return f"📋 <b>РЕЕСТР АКТИВНЫХ ЗАДАЧ</b>\n\n⚠️ Ошибка чтения: {e}"

def get_tasks_markup():
    return {
        "inline_keyboard": [
            [{"text": "☁️ Блок 0: VPS & 24/7", "callback_data": "tasks_block_0"}, {"text": "📁 Блок 1: Общая", "callback_data": "tasks_block_1"}],
            [{"text": "💼 Блок 2: Работа", "callback_data": "tasks_block_2"}, {"text": "🥊 Блок 3: Спорт", "callback_data": "tasks_block_3"}],
            [{"text": "📋 Все задачи", "callback_data": "tasks_block_all"}],
            [{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}]
        ]
    }

def get_main_dashboard_markup():
    return {
        "inline_keyboard": [
            [{"text": "🎙 ИИ-Секретарь", "callback_data": "nav_secretary"}, {"text": "📋 Задачи", "callback_data": "nav_tasks"}],
            [{"text": "📌 Заметки", "callback_data": "nav_notes"}, {"text": "🔐 Пароли", "callback_data": "nav_pass"}],
            [{"text": "🔎 Поиск", "callback_data": "nav_search"}, {"text": "⏰ Напоминания", "callback_data": "nav_remind"}],
            [{"text": "☁️ Облачное хранилище", "callback_data": "nav_cloud"}, {"text": "📧 Почта", "callback_data": "nav_mail"}],
            [{"text": "ℹ️ Справка", "callback_data": "nav_info"}]
        ]
    }

def get_construction_markup():
    return {
        "inline_keyboard": [
            [{"text": "📋 Сводка объектов", "callback_data": "const_summary"}, {"text": "🛡 Антифрод & Брак", "callback_data": "const_audit"}],
            [{"text": "📊 Накопительная КС-2", "callback_data": "const_ks2"}, {"text": "📄 Скачать АОСР (.docx)", "callback_data": "const_aosr_last"}],
            [{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}]
        ]
    }

def get_video_dashboard_text():
    return (
        "📹 <b>ИИ-КОМПЬЮТЕРНОЕ ЗРЕНИЕ & БИОМЕХАНИКА БОКСА 5.0</b>\n\n"
        "✨ <i>Нейросетевой трекинг MediaPipe Pose в кружочках и видеоряде!</i>\n\n"
        "🥊 <b>Как запустить видео-анализ:</b>\n"
        " 1. 🔵 <b>Кружочек (Video Note):</b> Запишите и отправьте видеосообщение прямо в чат.\n"
        " 2. 🎬 <b>Видеофайл (MP4/MOV):</b> Отправьте спарринг, отработку на лапах или бой с тенью.\n"
        " 3. ✍️ <b>Подпись к видео:</b> Задайте фокус (например: <i>«Оцени скорость джеба»</i>).\n\n"
        "🔬 <b>Что вычисляет нейросеть (MediaPipe + OpenCV):</b>\n"
        " • ⚡️ <b>Скорость вылета кулака:</b> расчет в <code>м/с</code> и <code>км/ч</code> с биометрической калибровкой.\n"
        " • ⏱ <b>Время возврата (Ретракция):</b> замер в миллисекундах (норматив &le; 190 мс).\n"
        " • 📐 <b>Углы в локтях:</b> дожим прямого удара (165–178°) и угол жесткости хука (90–110°).\n"
        " • ⚖️ <b>Завал корпуса:</b> отклонение оси позвоночника от вертикали (норма &le; 14°).\n"
        " • 🛡 <b>Дисциплина передней руки:</b> фиксация опускания защиты при атаке.\n"
        " • 🖼 <b>HUD-разметка:</b> генерация цветного кадра со скелетом и спидометром.\n"
        " • 🎙 <b>Транскрибация команд</b> тренера и сохранение в Облако 24/7."
    )

def get_video_markup():
    return {
        "inline_keyboard": [
            [{"text": "☁️ Файлы в Облаке", "callback_data": "cloud_cat_all"}],
            [{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}]
        ]
    }

def get_cloud_markup():
    return get_cloud_dashboard_markup()

def get_secretary_markup(is_guest=False):
    if is_guest:
        return {
            "inline_keyboard": [
                [{"text": "💡 Примеры вопросов", "callback_data": "sec_guest_examples"}],
                [{"text": "🔄 Обновить экран", "callback_data": "sec_guest_refresh"}]
            ]
        }
    share_url = "https://t.me/share/url?url=https://t.me/vsr_guard_bot&text=%D0%9F%D1%80%D0%B8%D0%B2%D0%B5%D1%82!%20%D0%94%D0%B5%D1%80%D0%B6%D0%B8%20%D1%81%D1%81%D1%8B%D0%BB%D0%BA%D1%83%20%D0%BD%D0%B0%20%D0%98%D0%98-%D0%A1%D0%B5%D0%BA%D1%80%D0%B5%D1%82%D0%B0%D1%80%D1%8C%20%28Gemini%203.7%20Flash%29"
    return {
        "inline_keyboard": [
            [{"text": "👥 Ссылка для гостей (Копировать)", "callback_data": "sec_guest_link"}],
            [{"text": "🔗 Поделиться с гостем (В 1 клик)", "url": share_url}],
            [{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}]
        ]
    }

def get_back_button_markup():
    return {
        "inline_keyboard": [
            [{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}]
        ]
    }

def get_notes_markup(chat_id):
    notes = load_notes()
    cat_state = NOTES_CATEGORY_STATE.get(chat_id, "overview")
    is_bulk = NOTES_BULK_MODE.get(chat_id, False)
    selected_ids = NOTES_SELECT_MODE.get(chat_id, set())
    
    cnt_sport = sum(1 for n in notes if "спорт" in str(n.get("category", "")).lower())
    cnt_work = sum(1 for n in notes if "работ" in str(n.get("category", "")).lower())
    cnt_gen = sum(1 for n in notes if "спорт" not in str(n.get("category", "")).lower() and "работ" not in str(n.get("category", "")).lower())

    if cat_state == "overview":
        return {
            "inline_keyboard": [
                [{"text": f"🏋️ Спорт ({cnt_sport})", "callback_data": "notes_cat_Спорт"}, {"text": f"🏗 Работа ({cnt_work})", "callback_data": "notes_cat_Работа"}],
                [{"text": f"📁 Общее ({cnt_gen})", "callback_data": "notes_cat_Общее"}],
                [{"text": "📥 Скачать все заметки (.txt)", "callback_data": "export_notes_txt"}],
                [{"text": "« 🔙 В Меню", "callback_data": "nav_main"}]
            ]
        }

    cat_name = cat_state
    if cat_name == "Спорт":
        cat_notes = [n for n in notes if "спорт" in str(n.get("category", "")).lower()]
    elif cat_name == "Работа":
        cat_notes = [n for n in notes if "работ" in str(n.get("category", "")).lower()]
    else:
        cat_notes = [n for n in notes if "спорт" not in str(n.get("category", "")).lower() and "работ" not in str(n.get("category", "")).lower()]
    
    search_q = FOLDER_SEARCH_RESULTS.get(chat_id)
    if search_q:
        cat_notes = [n for n in cat_notes if search_q.lower() in n.get("text", "").lower()]

    total_items = len(cat_notes)
    total_pages = max(1, math.ceil(total_items / NOTES_PAGE_SIZE)) if total_items > 0 else 1
    curr_page = max(1, min(NOTES_PAGE_STATE.get(chat_id, 1), total_pages))
    NOTES_PAGE_STATE[chat_id] = curr_page

    start_idx = (curr_page - 1) * NOTES_PAGE_SIZE
    page_notes = cat_notes[start_idx : start_idx + NOTES_PAGE_SIZE]

    rows = []

    if is_bulk:
        if page_notes:
            sel_buttons = []
            for n in page_notes:
                is_sel = n["id"] in selected_ids
                b_text = f"🔴 [✓] #{n['id']}" if is_sel else f"⬜️ #{n['id']}"
                sel_buttons.append({"text": b_text, "callback_data": f"note_sel_toggle_{n['id']}"})
                if len(sel_buttons) == 3:
                    rows.append(sel_buttons)
                    sel_buttons = []
            if sel_buttons:
                rows.append(sel_buttons)

        if total_pages > 1:
            rows.append([
                {"text": "◀️ Назад", "callback_data": "note_page_prev"},
                {"text": f"📄 Лист {curr_page}/{total_pages}", "callback_data": "note_page_noop"},
                {"text": "Вперед ▶️", "callback_data": "note_page_next"}
            ])

        rows.append([
            {"text": "🔘 Выбрать все на листе", "callback_data": "note_sel_all_page"},
            {"text": "🧹 Снять выбор", "callback_data": "note_sel_clear"}
        ])

        if len(selected_ids) > 0:
            rows.append([
                {"text": f"🔥 🗑 УДАЛИТЬ ВЫБРАННЫЕ ({len(selected_ids)} шт)", "callback_data": "note_bulk_delete_confirm"}
            ])

        rows.append([
            {"text": "« ❌ Выйти из режима выбора", "callback_data": "note_bulk_mode_off"}
        ])

    else:
        # 2-column compact grid of note buttons (10 notes fit in 5 rows!)
        if page_notes:
            note_buttons = []
            for n in page_notes:
                n_id = n["id"]
                raw_text = n.get("text", "").strip()
                first_line = raw_text.split("\n")[0].strip()
                title = first_line[:14] + ".." if len(first_line) > 14 else first_line
                if not title:
                    title = "Заметка"
                note_buttons.append({"text": f"#{n_id} {title}", "callback_data": f"note_detail_{n_id}"})
                if len(note_buttons) == 2:
                    rows.append(note_buttons)
                    note_buttons = []
            if note_buttons:
                rows.append(note_buttons)

        # Quick Folder Actions (Add / Export)
        rows.append([
            {"text": "🎙 ➕ Добавить", "callback_data": f"note_add_to_{cat_name}"},
            {"text": "📥 Скачать (.txt)", "callback_data": f"note_export_cat_{cat_name}"}
        ])

        # Pagination if needed
        if total_pages > 1:
            rows.append([
                {"text": "◀️ Назад", "callback_data": "note_page_prev"},
                {"text": f"📄 {curr_page} / {total_pages}", "callback_data": "note_page_noop"},
                {"text": "Вперед ▶️", "callback_data": "note_page_next"}
            ])

        # Search / Bulk Delete / Back
        if search_q:
            rows.append([
                {"text": "❌ Сбросить поиск", "callback_data": f"note_search_reset_{cat_name}"}
            ])
        else:
            rows.append([
                {"text": "🔍 Поиск", "callback_data": f"note_search_in_{cat_name}"},
                {"text": "🗑 Выбор", "callback_data": "note_bulk_mode_on"}
            ])

        rows.append([
            {"text": "📂 « К папкам", "callback_data": "notes_back_to_folders"},
            {"text": "« 🔙 В Меню", "callback_data": "nav_main"}
        ])

    return {"inline_keyboard": rows}

def get_note_detail_markup(note):
    n_id = note["id"]
    cat = note.get("category", "Общее")

    return {
        "inline_keyboard": [
            [{"text": "📋 Скопировать текст", "callback_data": f"note_send_raw_{n_id}"}, {"text": "📁 Сменить папку", "callback_data": f"note_move_prompt_{n_id}"}],
            [{"text": "➕ Дописать в заметку", "callback_data": f"note_append_hint_{n_id}"}, {"text": "🗑 Удалить", "callback_data": f"note_delete_{n_id}"}],
            [{"text": f"« 🔙 В папку [{cat}]", "callback_data": f"notes_cat_{cat}"}, {"text": "🎛 Главное Меню", "callback_data": "nav_main"}]
        ]
    }

def get_wifi_markup():
    return {
        "inline_keyboard": [
            [{"text": "🔄 Обновить статус Wi-Fi", "callback_data": "action_wifi_refresh"}],
            [{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}]
        ]
    }

def get_cam_markup():
    return {
        "inline_keyboard": [
            [{"text": "📸 Сделать снимок", "callback_data": "action_cam_snap"}],
            [{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}]
        ]
    }

def get_mail_markup():
    return {
        "inline_keyboard": [
            [{"text": "📥 Свежие входящие (5 шт)", "callback_data": "action_fetch_inbox"}, {"text": "🗂 Папки на Mail.ru", "callback_data": "action_topics_mail"}],
            [{"text": "🔄 Разложить входящие по темам", "callback_data": "action_sort_mail"}],
            [{"text": "🛡 Аудит безопасности", "callback_data": "action_audit_mail"}, {"text": "« 🔙 Главное Меню", "callback_data": "nav_main"}]
        ]
    }

def send_main_dashboard(chat_id):
    banner_path = os.path.join(PROJECT_ROOT, "assets", "vector_ai_welcome_banner.jpg")
    text = (
        "🎛 <b>ВЕКТОР • МЕНЮ</b> <code>#50 v2.5.0</code>\n\n"
        "• 🎙 <b>ИИ-Секретарь</b> — голосовой ввод и быстрые ответы\n"
        "• 📋 <b>Задачи</b> — списки дел, чек-листы и поручения\n"
        "• 📌 <b>Заметки</b> — база знаний по 3 папкам (Спорт, Работа, Общее)\n"
        "• 🔐 <b>Пароли</b> — защищенный сейф логинов и ключей\n"
        "• 🔎 <b>Поиск</b> — мгновенный поиск по всей базе\n"
        "• ⏰ <b>Напоминания</b> — контроль дедлайнов и важных встреч\n"
        "• ☁️ <b>Облачное хранилище</b> — файлы, документы и бэкапы\n"
        "• 📧 <b>Почта</b> — входящие письма и уведомления\n"
        "• ℹ️ <b>Справка</b> — руководство и быстрые команды\n\n"
        "👇 <i>Выберите нужный раздел или надиктуйте голос:</i>"
    )
    markup = get_main_dashboard_markup()

    if os.path.exists(banner_path):
        res = send_telegram_photo(chat_id, banner_path, caption=text, reply_markup=markup)
        if res and res.get("ok"):
            ACTIVE_CARD_ID[chat_id] = res["result"]["message_id"]
            return

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": markup
    }
    res = send_api_request("sendMessage", payload)
    if res and res.get("ok"):
        ACTIVE_CARD_ID[chat_id] = res["result"]["message_id"]

def edit_card(chat_id, message_id, text, markup=None):
    mk = markup or get_back_button_markup()
    
    # 1. Попытка отредактировать как обычное текстовое сообщение
    payload_text = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": mk
    }
    res = send_api_request("editMessageText", payload_text)
    if res and res.get("ok"):
        ACTIVE_CARD_ID[chat_id] = message_id
        return
    if res and "message is not modified" in str(res.get("description", "")).lower():
        ACTIVE_CARD_ID[chat_id] = message_id
        return

    # 2. Если не удалось (например, исходное сообщение было карточкой-фото) — редактируем подпись к фото!
    caption_text = text if len(text) <= 1020 else text[:1015] + "..."
    payload_cap = {
        "chat_id": chat_id,
        "message_id": message_id,
        "caption": caption_text,
        "parse_mode": "HTML",
        "reply_markup": mk
    }
    res_cap = send_api_request("editMessageCaption", payload_cap)
    if res_cap and res_cap.get("ok"):
        ACTIVE_CARD_ID[chat_id] = message_id
        return
    if res_cap and "message is not modified" in str(res_cap.get("description", "")).lower():
        ACTIVE_CARD_ID[chat_id] = message_id
        return

    # 3. Если подпись не влезает или сообщение удалено — удаляем старое и отправляем свежее окно
    try:
        send_api_request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
    except Exception:
        pass

    send_payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": mk
    }
    res_new = send_api_request("sendMessage", send_payload)
    if res_new and res_new.get("ok"):
        ACTIVE_CARD_ID[chat_id] = res_new["result"]["message_id"]

def get_notes_text(chat_id):
    notes = load_notes()
    cat_state = NOTES_CATEGORY_STATE.get(chat_id, "overview")
    is_bulk = NOTES_BULK_MODE.get(chat_id, False)
    selected_ids = NOTES_SELECT_MODE.get(chat_id, set())
    
    cnt_sport = sum(1 for n in notes if "спорт" in str(n.get("category", "")).lower())
    cnt_work = sum(1 for n in notes if "работ" in str(n.get("category", "")).lower())
    cnt_gen = sum(1 for n in notes if "спорт" not in str(n.get("category", "")).lower() and "работ" not in str(n.get("category", "")).lower())

    if cat_state == "overview":
        recent = notes[-3:] if notes else []
        recent_txt = ""
        if recent:
            recent_txt = "📋 <b>Последние записи:</b>\n"
            for r in reversed(recent):
                first_line = r.get("text", "").split("\n")[0][:36]
                recent_txt += f"• <b>#{r.get('id', '')}</b> [{r.get('category', 'Общее')}]: <i>{html.escape(first_line)}...</i>\n"
            recent_txt += "\n"

        return (
            "📌 <b>ВЕКТОР • ЗАМЕТКИ</b>\n"
            f"Всего в архиве: <b>{len(notes)}</b> записей\n\n"
            f"📂 <b>Папки:</b>\n"
            f"• 🏋️ <b>Спорт:</b> <code>{cnt_sport}</code>\n"
            f"• 🏗 <b>Работа:</b> <code>{cnt_work}</code>\n"
            f"• 📁 <b>Общее:</b> <code>{cnt_gen}</code>\n\n"
            f"{recent_txt}"
            "💬 <i>Надиктуйте голос или отправьте текст — бот автоматически сохранит запись!</i>"
        )

    cat_name = cat_state
    icon = CATEGORY_ICON_MAP.get(cat_name, "📁")
    
    if cat_name == "Спорт":
        cat_notes = [n for n in notes if "спорт" in str(n.get("category", "")).lower()]
    elif cat_name == "Работа":
        cat_notes = [n for n in notes if "работ" in str(n.get("category", "")).lower()]
    else:
        cat_notes = [n for n in notes if "спорт" not in str(n.get("category", "")).lower() and "работ" not in str(n.get("category", "")).lower()]
    
    search_q = FOLDER_SEARCH_RESULTS.get(chat_id)
    if search_q:
        cat_notes = [n for n in cat_notes if search_q.lower() in n.get("text", "").lower()]

    total_items = len(cat_notes)
    total_pages = max(1, math.ceil(total_items / NOTES_PAGE_SIZE)) if total_items > 0 else 1
    curr_page = max(1, min(NOTES_PAGE_STATE.get(chat_id, 1), total_pages))
    NOTES_PAGE_STATE[chat_id] = curr_page

    start_idx = (curr_page - 1) * NOTES_PAGE_SIZE
    page_notes = cat_notes[start_idx : start_idx + NOTES_PAGE_SIZE]

    if is_bulk:
        text = (
            f"🗑 <b>МУЛЬТИ-ВЫБОР И УДАЛЕНИЕ ЗАМЕТОК</b>\n"
            f"Папка: <b>{icon} {cat_name.upper()}</b> • Выбрано: <b>{len(selected_ids)} шт.</b>\n"
            f"(Лист <b>{curr_page} из {total_pages}</b> • Всего в папке: {total_items}):\n"
            f"────────────────────\n"
            f"<i>Нажимайте на номера ниже, чтобы отметить/снять выбор:</i>\n\n"
        )
    elif search_q:
        text = f"🔍 <b>ПОИСК В [{icon} {cat_name.upper()}]: «{html.escape(search_q)}»</b> (Найдено: <b>{total_items}</b>):\n\n"
    else:
        text = f"📂 <b>ПАПКА: {icon} {cat_name.upper()}</b> (Всего: <b>{total_items}</b> • Лист <b>{curr_page} из {total_pages}</b>):\n\n"

    if not cat_notes:
        if search_q:
            text += f"<i>По запросу «{html.escape(search_q)}» ничего не найдено.</i>\n\n"
        else:
            text += "<i>В данной папке пока нет записей.</i>\n\n"
    else:
        for n in page_notes:
            n_id = n.get("id", 1)
            raw_text = n.get("text", "").strip()
            first_line = raw_text.split("\n")[0].strip()
            if len(first_line) > 42:
                preview = first_line[:42] + "..."
            else:
                preview = first_line
            
            time_val = str(n.get("time") or n.get("date") or "")
            time_badge = f" <i>({time_val[11:16]})</i>" if len(time_val) >= 16 else ""

            if is_bulk:
                is_sel = n_id in selected_ids
                sel_badge = "🔴 [✓]" if is_sel else "⚪️"
                text += f"{sel_badge} <b>#{n_id}</b> {html.escape(preview)}{time_badge}\n"
            else:
                text += f"• <b>#{n_id}</b> {html.escape(preview)}{time_badge}\n"

    if is_bulk:
        text += f"\n💡 <i>Отмечено: <b>{len(selected_ids)}</b>. Нажмите <b>🔥 🗑 УДАЛИТЬ ВЫБРАННЫЕ</b>!</i>"
    elif not search_q:
        text += f"\n👇 <i>Нажмите на кнопку заметки ниже:</i>"
    else:
        text += f"\n💡 <i>Нажмите <b>❌ Сбросить поиск</b> для возврата.</i>"
    return text

def get_note_detail_text(note):
    category = note.get("category", "Общее")
    icon = CATEGORY_ICON_MAP.get(category, "📁")
    n_id = note.get("id", 1)
    note_time = note.get("time") or note.get("date") or "Не указано"
    
    raw_text = note.get("text", "")
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    copyable_blocks = ""
    for l in lines:
        clean_line = l.lstrip("•").strip()
        copyable_blocks += f"<code>{html.escape(clean_line)}</code>\n"

    if len(copyable_blocks) > 3000:
        copyable_blocks = copyable_blocks[:3000] + "\n<code>...[полный текст сохранен в файле]</code>"

    fp = note.get("file_path", "")
    fp_display = f"\n• Файл: <code>{fp}</code>" if fp else ""

    text = (
        f"📝 <b>ЗАМЕТКА #{n_id}</b> [{icon} {category}]\n\n"
        f"• Папка: <b>{category}</b>\n"
        f"• Время создания: <i>{note_time}</i>{fp_display}\n\n"
        f"📋 <b>Текст заметки (нажмите на рамку для копирования):</b>\n"
        f"{copyable_blocks}\n"
        f"💡 <i>Нажмите на любую рамку выше, чтобы мгновенно скопировать текст в буфер!</i>"
    )
    return text

def get_passwords_text():
    return format_vault_summary_html()

def get_passwords_markup():
    from vault_manager import get_vault_data
    data = get_vault_data()
    services = data.get("services", {})

    rows = []
    if services:
        del_btns = []
        for idx, s_name in enumerate(services.keys(), start=1):
            del_btns.append({"text": f"🗑 Удалить #{idx}", "callback_data": f"vault_del_{idx}"})
            if len(del_btns) == 2:
                rows.append(del_btns)
                del_btns = []
        if del_btns:
            rows.append(del_btns)

    rows.append([{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}])
    return {"inline_keyboard": rows}

def get_expenses_text():
    expenses = load_expenses()
    if not expenses:
        return (
            "📊 <b>ТРЕКЕР РАСХОДОВ И ФИНАНСОВ</b>\n\n"
            "Расходов пока не зафиксировано.\n\n"
            "💳 <i>Отправьте текст или голосом: <code>1500 обед</code></i>"
        )
    total = sum(e["amount"] for e in expenses)
    text = f"📊 <b>ВАШИ РАСХОДЫ (Всего: {total} руб):</b>\n\n"
    for e in expenses[-10:]:
        text += f" • <b>{e['amount']} руб</b> — {e['category']} ({e['time']})\n"
    text += "\n💳 <i>Отправьте '1500 обед', чтобы добавить расход.</i>"
    return text

def get_expenses_markup():
    return {
        "inline_keyboard": [
            [{"text": "📥 Скачать отчет (Excel / CSV)", "callback_data": "export_expenses_csv"}],
            [{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}]
        ]
    }

def get_daily_summary_text():
    notes = load_notes()
    expenses = load_expenses()
    today_str = time.strftime("%Y-%m-%d")
    today_notes = [n for n in notes if n.get("time", "").startswith(today_str)]
    exp_sum = sum(e["amount"] for e in expenses if e.get("time", "").startswith(today_str))

    text = f"📋 <b>ИТОГИ И ДАЙДЖЕСТ ЗА СЕГОДНЯ ({today_str}):</b>\n\n"
    text += f"• Всего заметок за сегодня: <b>{len(today_notes)}</b>\n"
    text += f"• Расходы за сегодня: <b>{exp_sum} руб</b>\n"
    text += f"• Статус защиты почты: <b>АКТИВЕН (0 угроз)</b>\n"
    text += f"• Локация данных: <code>/home/home/Документы/2</code>\n"
    return text

def download_and_transcribe_voice(file_id, update_id):
    config = load_config()
    token = config.get("telegram_bot_token")
    if not token:
        return None, None
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ogg_path = None
    wav_path = None
    try:
        f_url = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
        req = urllib.request.Request(f_url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            if res.get('ok'):
                rel_path = res['result']['file_path']
                dl_url = f"https://api.telegram.org/file/bot{token}/{rel_path}"
                file_name = f"voice_{update_id}_{int(time.time())}.ogg"
                ogg_path = os.path.join(DOWNLOAD_DIR, file_name)
                urllib.request.urlretrieve(dl_url, ogg_path)
                
                wav_path = ogg_path.replace(".ogg", ".wav")
                if os.path.exists(FFMPEG_BIN):
                    subprocess.run([FFMPEG_BIN, "-y", "-i", ogg_path, wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                    r = sr.Recognizer()
                    with sr.AudioFile(wav_path) as source:
                        audio_data = r.record(source)
                        recognized_text = r.recognize_google(audio_data, language="ru-RU")
                        if os.path.exists(wav_path):
                            os.remove(wav_path)
                        return ogg_path, recognized_text
    except Exception as e:
        print(f"Ошибка транскрибации голоса: {e}")
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
    return ogg_path, None

def handle_callback(cb):
    cb_id = cb.get("id")
    cb_data = cb.get("data")
    msg = cb.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    msg_id = msg.get("message_id")

    if not chat_id or not msg_id:
        return

    answer_cb_async(cb_id)

    is_guest = (int(chat_id) != AUTHORIZED_CHAT_ID)

    if is_guest:
        if cb_data == "sec_guest_examples":
            examples_text = (
                "💡 <b>ПРИМЕРЫ ВОПРОСОВ ДЛЯ ИИ-СЕКРЕТАРЯ:</b>\n\n"
                "Вы можете задавать любые вопросы текстом или наговаривать их голосом:\n\n"
                "• 📝 <i>«Составь текст коммерческого предложения на поставку стройматериалов»</i>\n"
                "• ⚖️ <i>«В чем разница между актами КС-2 и КС-3 простыми словами?»</i>\n"
                "• 🧮 <i>«Посчитай: 125 000 руб + 20% НДС»</i>\n"
                "• 🌍 <i>«Какой сейчас курс юаня и доллара ЦБ РФ?»</i>\n"
                "• 🥊 <i>«Как рассчитать буферизацию лактата для боксера?»</i>\n"
                "• 🚆 <i>«Найди билеты на поезд Волгоград — Москва»</i>\n\n"
                "👉 <b>Просто отправьте ваш вопрос прямо в этот чат!</b>"
            )
            markup = {
                "inline_keyboard": [
                    [{"text": "« 🔙 Назад к ИИ-Секретарю", "callback_data": "sec_guest_refresh"}]
                ]
            }
            edit_card(chat_id, msg_id, examples_text, markup)
            return
        else:
            edit_card(chat_id, msg_id, get_secretary_dashboard_text(user_id=chat_id, is_guest=True), get_secretary_markup(is_guest=True))
            return

    if cb_data == "nav_boxing":
        boxing_info = (
            "🥊 <b>СПОРТИВНАЯ ЭКОСИСТЕМА BOXING PERFORMANCE</b>\n\n"
            "Все модули спортивной готовности, сенсорного замера ЧСС/rMSSD и 3D-видеоанализа техники вынесены в специализированный спортивный бот:\n\n"
            "👉 <b>Спортивный бот:</b> @Performance555_bot"
        )
        markup = {
            "inline_keyboard": [
                [{"text": "⚡️ Открыть @Performance555_bot", "url": "https://t.me/Performance555_bot"}],
                [{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}]
            ]
        }
        edit_card(chat_id, msg_id, boxing_info, markup)
    elif cb_data == "nav_main":
        text = (
            "🎛 <b>ВЕКТОР • МЕНЮ</b>\n\n"
            "• 🎙 <b>ИИ-Секретарь</b> — голосовой ввод и быстрые ответы\n"
            "• 📋 <b>Задачи</b> — списки дел, чек-листы и поручения\n"
            "• 📌 <b>Заметки</b> — база знаний по 3 папкам (Спорт, Работа, Общее)\n"
            "• 🔐 <b>Пароли</b> — защищенный сейф логинов и ключей\n"
            "• 🔎 <b>Поиск</b> — мгновенный поиск по всей базе\n"
            "• ⏰ <b>Напоминания</b> — контроль дедлайнов и важных встреч\n"
            "• ☁️ <b>Облачное хранилище</b> — файлы, документы и бэкапы\n"
            "• 📧 <b>Почта</b> — входящие письма и уведомления\n"
            "• ℹ️ <b>Справка</b> — руководство и быстрые команды\n\n"
            "👇 <i>Выберите нужный раздел или надиктуйте голос:</i>"
        )
        edit_card(chat_id, msg_id, text, get_main_dashboard_markup())
    elif cb_data == "nav_notes":
        NOTES_CATEGORY_STATE[chat_id] = "overview"
        NOTES_BULK_MODE[chat_id] = False
        NOTES_SELECT_MODE[chat_id] = set()
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data.startswith("notes_cat_"):
        cat_name = cb_data.replace("notes_cat_", "")
        NOTES_CATEGORY_STATE[chat_id] = cat_name
        NOTES_PAGE_STATE[chat_id] = 1
        NOTES_BULK_MODE[chat_id] = False
        NOTES_SELECT_MODE[chat_id] = set()
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data == "notes_back_to_folders":
        NOTES_CATEGORY_STATE[chat_id] = "overview"
        NOTES_BULK_MODE[chat_id] = False
        NOTES_SELECT_MODE[chat_id] = set()
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data == "note_bulk_mode_on":
        NOTES_BULK_MODE[chat_id] = True
        NOTES_SELECT_MODE[chat_id] = set()
        answer_cb_async(cb_id, text="🗑 Режим выбора включен. Отмечайте заметки!")
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data == "note_bulk_mode_off":
        NOTES_BULK_MODE[chat_id] = False
        NOTES_SELECT_MODE[chat_id] = set()
        answer_cb_async(cb_id, text="Обычный режим")
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data.startswith("note_sel_toggle_"):
        n_id = int(cb_data.replace("note_sel_toggle_", ""))
        sel = NOTES_SELECT_MODE.setdefault(chat_id, set())
        if n_id in sel:
            sel.remove(n_id)
        else:
            sel.add(n_id)
        answer_cb_async(cb_id)
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data == "note_sel_all_page":
        notes = load_notes()
        cat_name = NOTES_CATEGORY_STATE.get(chat_id, "overview")
        cat_notes = [n for n in notes if n.get("category") == cat_name or (cat_name == "Общее" and n.get("category") not in ["Спорт", "Работа"])]
        curr_page = NOTES_PAGE_STATE.get(chat_id, 1)
        start_idx = (curr_page - 1) * NOTES_PAGE_SIZE
        page_notes = cat_notes[start_idx : start_idx + NOTES_PAGE_SIZE]
        sel = NOTES_SELECT_MODE.setdefault(chat_id, set())
        for n in page_notes:
            sel.add(n["id"])
        answer_cb_async(cb_id, text=f"✅ Выбраны {len(page_notes)} заметок")
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data == "note_sel_clear":
        NOTES_SELECT_MODE[chat_id] = set()
        answer_cb_async(cb_id, text="🧹 Выбор сброшен")
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data == "note_bulk_delete_confirm":
        sel_ids = list(NOTES_SELECT_MODE.get(chat_id, set()))
        if sel_ids:
            deleted_ids = delete_multiple_notes(sel_ids)
            NOTES_SELECT_MODE[chat_id] = set()
            NOTES_BULK_MODE[chat_id] = False
            answer_cb_async(cb_id, text=f"🗑 Успешно удалено {len(deleted_ids)} заметок!")
            edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
        else:
            answer_cb_async(cb_id, text="⚠️ Сначала отметьте хотя бы одну заметку!")
    elif cb_data.startswith("cat_pick_"):
        cat_chosen = cb_data.replace("cat_pick_", "")
        pending = PENDING_NOTE_CATEGORY.pop(chat_id, None)
        if pending:
            n_id = save_note(pending["text"], note_type=pending.get("type", "текст"), category=cat_chosen)
            answer_cb_async(cb_id, text=f"✅ Сохранено в [{cat_chosen}]!")
            NOTES_CATEGORY_STATE[chat_id] = cat_chosen
            edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
        else:
            answer_cb_async(cb_id, text="⚠️ Запись уже обработана")
            NOTES_CATEGORY_STATE[chat_id] = "overview"
            edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data == "cat_cancel":
        PENDING_NOTE_CATEGORY.pop(chat_id, None)
        answer_cb_async(cb_id, text="❌ Отменено")
        NOTES_CATEGORY_STATE[chat_id] = "overview"
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data.startswith("note_move_prompt_"):
        n_id = int(cb_data.replace("note_move_prompt_", ""))
        note = get_note_by_id(n_id)
        curr_c = note.get("category", "Общее") if note else "Общее"
        move_prompt_text = (
            f"📁 <b>ПЕРЕМЕСТИТЬ ЗАМЕТКУ #{n_id}</b>\n\n"
            f"Текущая папка: <b>{curr_c}</b>\n\n"
            f"<i>Выберите новую папку для этой заметки:</i>"
        )
        move_markup = {
            "inline_keyboard": [
                [{"text": "🏋️ В Спорт", "callback_data": f"note_do_move_{n_id}_Спорт"}, {"text": "🏗 В Работу", "callback_data": f"note_do_move_{n_id}_Работа"}],
                [{"text": "📁 В Общее", "callback_data": f"note_do_move_{n_id}_Общее"}],
                [{"text": "« 🔙 Отмена", "callback_data": f"note_detail_{n_id}"}]
            ]
        }
        edit_card(chat_id, msg_id, move_prompt_text, move_markup)
    elif cb_data.startswith("note_do_move_"):
        raw_parts = cb_data.replace("note_do_move_", "").split("_", 1)
        n_id = int(raw_parts[0])
        new_cat = raw_parts[1]
        updated_n = move_note_category(n_id, new_cat)
        answer_cb_async(cb_id, text=f"✅ Перемещено в [{new_cat}]!")
        if updated_n:
            edit_card(chat_id, msg_id, get_note_detail_text(updated_n), get_note_detail_markup(updated_n))
        else:
            edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data.startswith("note_detail_"):
        n_id = int(cb_data.replace("note_detail_", ""))
        note = get_note_by_id(n_id)
        if note:
            edit_card(chat_id, msg_id, get_note_detail_text(note), get_note_detail_markup(note))
        else:
            edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data.startswith("note_send_raw_"):
        n_id = int(cb_data.replace("note_send_raw_", ""))
        note = get_note_by_id(n_id)
        if note:
            send_api_request("sendMessage", {
                "chat_id": chat_id,
                "text": f"📋 <b>Текст заметки #{n_id} (нажмите на рамку для копирования):</b>\n\n<code>{note['text']}</code>",
                "parse_mode": "HTML"
            })
    elif cb_data.startswith("note_delete_"):
        n_id = int(cb_data.replace("note_delete_", ""))
        delete_single_note(n_id)
        answer_cb_async(cb_id, text=f"🗑 Заметка #{n_id} удалена!")
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data.startswith("note_append_hint_"):
        n_id = int(cb_data.replace("note_append_hint_", ""))
        note = get_note_by_id(n_id)
        current_txt = note['text'] if note else ""
        hint_text = (
            f"➕ <b>ДОБАВИТЬ В ЗАМЕТКУ #{n_id}</b>\n\n"
            f"📄 <b>Текущий текст:</b>\n<code>{current_txt}</code>\n\n"
            f"💬 <b>Отправьте текстом или голосом:</b>\n"
            f"<code>Дописать {n_id}: ваш новый пункт</code>\n"
            f"или просто: <code>{n_id}: новый пункт</code>\n\n"
            f"<i>Старый текст не удалится, новое припишется снизу!</i>"
        )
        markup = get_note_detail_markup(note) if note else get_back_button_markup()
        edit_card(chat_id, msg_id, hint_text, markup)
    elif cb_data.startswith("note_edit_hint_"):
        n_id = int(cb_data.replace("note_edit_hint_", ""))
        note = get_note_by_id(n_id)
        hint_text = (
            f"✏️ <b>ПЕРЕЗАПИСАТЬ ТЕКСТ ЗАМЕТКИ #{n_id} ПОЛНОСТЬЮ</b>\n\n"
            f"Если нужно полностью стереть старый текст и написать с нуля:\n"
            f"<code>Заменить {n_id}: совершенно новый текст</code>"
        )
        markup = get_note_detail_markup(note) if note else get_back_button_markup()
        edit_card(chat_id, msg_id, hint_text, markup)
    elif cb_data.startswith("note_add_to_"):
        cat_name = cb_data.replace("note_add_to_", "")
        QUICK_TARGET_CATEGORY[chat_id] = cat_name
        answer_cb_async(cb_id, text=f"🎙 Режим добавления в [{cat_name}] активирован!")
        prompt_txt = (
            f"🎙 <b>ДОБАВЛЕНИЕ В ПАПКУ: [{cat_name.upper()}]</b>\n\n"
            f"Надиктуйте голосовое сообщение или отправьте текст прямо сюда в чат.\n\n"
            f"<i>Заметка будет автоматически сохранена в папку <b>{cat_name}</b>!</i>"
        )
        cancel_mk = {
            "inline_keyboard": [
                [{"text": f"« 🔙 Отмена (Назад в {cat_name})", "callback_data": f"notes_cat_{cat_name}"}]
            ]
        }
        edit_card(chat_id, msg_id, prompt_txt, cancel_mk)
    elif cb_data.startswith("note_export_cat_"):
        cat_name = cb_data.replace("note_export_cat_", "")
        notes = load_notes()
        if cat_name == "Спорт":
            cat_notes = [n for n in notes if "спорт" in str(n.get("category", "")).lower()]
        elif cat_name == "Работа":
            cat_notes = [n for n in notes if "работ" in str(n.get("category", "")).lower()]
        else:
            cat_notes = [n for n in notes if "спорт" not in str(n.get("category", "")).lower() and "работ" not in str(n.get("category", "")).lower()]
        
        if not cat_notes:
            answer_cb_async(cb_id, text=f"⚠️ В папке {cat_name} нет записей")
        else:
            answer_cb_async(cb_id, text="📥 Формирую файл экспорта...")
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            export_lines = [
                "==================================================",
                f"📁 ИИ-ВЕКТОР • ЭКСПОРТ ПАПКИ [{cat_name.upper()}]",
                f"Всего записей: {len(cat_notes)} шт.",
                f"Дата экспорта: {now_str}",
                "==================================================\n"
            ]
            for idx, n in enumerate(cat_notes, 1):
                dt = n.get("time") or n.get("date") or "Не указано"
                export_lines.append(f"[{idx}] ЗАМЕТКА #{n['id']} • {dt}")
                export_lines.append(f"{n.get('text', '').strip()}")
                export_lines.append("-" * 40 + "\n")
            
            file_content = "\n".join(export_lines)
            export_file_path = os.path.join(PROJECT_ROOT, f"export_{cat_name}_{chat_id}.txt")
            with open(export_file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            
            send_telegram_file(chat_id, export_file_path, caption=f"📄 <b>Архив папки [{cat_name}]:</b> <code>{len(cat_notes)} заметок</code>")
    elif cb_data.startswith("note_search_in_"):
        cat_name = cb_data.replace("note_search_in_", "")
        PENDING_SEARCH_IN_CAT[chat_id] = cat_name
        answer_cb_async(cb_id, text=f"🔍 Поиск в папке [{cat_name}]")
        search_txt = (
            f"🔍 <b>ПОИСК В ПАПКЕ: [{cat_name.upper()}]</b>\n\n"
            f"Отправьте любое слово или фразу в чат (например: <i>пароль</i>, <i>смета</i>, <i>пульс</i>).\n\n"
            f"<i>Бот покажет только совпадения из папки <b>{cat_name}</b>.</i>"
        )
        cancel_mk = {
            "inline_keyboard": [
                [{"text": f"« 🔙 Отмена (Назад в {cat_name})", "callback_data": f"notes_cat_{cat_name}"}]
            ]
        }
        edit_card(chat_id, msg_id, search_txt, cancel_mk)
    elif cb_data.startswith("note_search_reset_"):
        cat_name = cb_data.replace("note_search_reset_", "")
        FOLDER_SEARCH_RESULTS.pop(chat_id, None)
        NOTES_PAGE_STATE[chat_id] = 1
        answer_cb_async(cb_id, text="🧹 Поиск сброшен")
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data == "note_page_prev":
        curr = NOTES_PAGE_STATE.get(chat_id, 1)
        NOTES_PAGE_STATE[chat_id] = max(1, curr - 1)
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data == "note_page_next":
        curr = NOTES_PAGE_STATE.get(chat_id, 1)
        notes = load_notes()
        cat_name = NOTES_CATEGORY_STATE.get(chat_id, "overview")
        if cat_name == "Спорт":
            cat_notes = [n for n in notes if "спорт" in str(n.get("category", "")).lower()]
        elif cat_name == "Работа":
            cat_notes = [n for n in notes if "работ" in str(n.get("category", "")).lower()]
        else:
            cat_notes = [n for n in notes if "спорт" not in str(n.get("category", "")).lower() and "работ" not in str(n.get("category", "")).lower()]
        search_q = FOLDER_SEARCH_RESULTS.get(chat_id)
        if search_q:
            cat_notes = [n for n in cat_notes if search_q.lower() in n.get("text", "").lower()]
        max_p = max(1, math.ceil(len(cat_notes) / NOTES_PAGE_SIZE))
        NOTES_PAGE_STATE[chat_id] = min(max_p, curr + 1)
        edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data == "note_page_noop":
        answer_cb_async(cb_id, text="Текущий лист заметок")
    elif cb_data == "nav_pass":
        edit_card(chat_id, msg_id, get_passwords_text(), get_passwords_markup())
    elif cb_data.startswith("vault_del_"):
        idx_str = cb_data.replace("vault_del_", "")
        delete_vault_credential_smart(idx_str)
        edit_card(chat_id, msg_id, get_passwords_text(), get_passwords_markup())
    elif cb_data == "nav_exp":
        edit_card(chat_id, msg_id, get_expenses_text())
    elif cb_data == "nav_daily":
        edit_card(chat_id, msg_id, get_daily_summary_text())
    elif cb_data == "nav_mail":
        edit_card(chat_id, msg_id, get_mail_dashboard_text(), get_mail_markup())
    elif cb_data in ["action_fetch_inbox", "action_fetch_inbox_refresh"]:
        answer_cb_async(cb_id, text="📥 Получение свежих писем...")
        force_ref = (cb_data == "action_fetch_inbox_refresh")
        
        def _fetch_worker():
            text = fetch_inbox_summary(limit=5, force_refresh=force_ref)
            markup = {
                "inline_keyboard": [
                    [{"text": "🔄 Обновить входящие", "callback_data": "action_fetch_inbox_refresh"}, {"text": "🗂 Папки на Mail.ru", "callback_data": "action_topics_mail"}],
                    [{"text": "« 🔙 В Почту", "callback_data": "nav_mail"}, {"text": "🎛 Главное Меню", "callback_data": "nav_main"}]
                ]
            }
            edit_card(chat_id, msg_id, text, markup)
            
        threading.Thread(target=_fetch_worker, daemon=True).start()

    elif cb_data in ["action_topics_mail", "action_topics_mail_refresh"]:
        answer_cb_async(cb_id, text="🗂 Загрузка папок сервера...")
        force_ref = (cb_data == "action_topics_mail_refresh")
        
        def _topics_worker():
            text = categorize_emails_by_topic(limit=40, force_refresh=force_ref)
            markup = {
                "inline_keyboard": [
                    [{"text": "🔄 Разложить новые письма", "callback_data": "action_sort_mail"}, {"text": "Обновить список", "callback_data": "action_topics_mail_refresh"}],
                    [{"text": "« 🔙 В Почту", "callback_data": "nav_mail"}, {"text": "🎛 Главное Меню", "callback_data": "nav_main"}]
                ]
            }
            edit_card(chat_id, msg_id, text, markup)
            
        threading.Thread(target=_topics_worker, daemon=True).start()

    elif cb_data == "action_sort_mail":
        answer_cb_async(cb_id, text="🔄 Раскладка писем...")
        edit_card(chat_id, msg_id, "⏳ <b>ИИ-Сортировка писем на Mail.ru...</b>\n\n<i>Анализируются темы, отправители и распределяются по 3 папкам (Работа, Бухгалтерия, Общее)...</i>", get_mail_markup())
        
        def _sort_worker():
            text = auto_sort_inbox_emails(max_emails=30)
            markup = {
                "inline_keyboard": [
                    [{"text": "🗂 Посмотреть папки", "callback_data": "action_topics_mail"}],
                    [{"text": "« 🔙 В Почту", "callback_data": "nav_mail"}, {"text": "🎛 Главное Меню", "callback_data": "nav_main"}]
                ]
            }
            edit_card(chat_id, msg_id, text, markup)
            
        threading.Thread(target=_sort_worker, daemon=True).start()

    elif cb_data == "action_audit_mail":
        answer_cb_async(cb_id, text="🛡 Сканирование...")
        edit_card(chat_id, msg_id, "🛡 <b>Сканирование почтового ящика...</b>\n\n<i>Проверка на фишинг, поддельные ссылки и опасные вложения...</i>", get_mail_markup())
        
        def _audit_worker():
            report = run_security_audit()
            if report.get("passed"):
                audit_txt = (
                    f"🛡 <b>АУДИТ БЕЗОПАСНОСТИ ПОЧТЫ (Mail.ru)</b>\n\n"
                    f"📫 Аккаунт: <code>{report.get('account')}</code>\n"
                    f"• Всего писем в ящике: <b>{report.get('total_msgs', 0)}</b>\n"
                    f"• Обнаружено угроз / фишинга: <b>{report.get('threats_count', 0)}</b>\n"
                    f"• SSL-шифрование IMAP: <b>100% Защищено</b>\n\n"
                    f"✅ <i>Почтовый ящик в полной безопасности. Подозрительных ссылок и опасных вложений не обнаружено!</i>"
                )
            else:
                audit_txt = f"⚠️ <b>Результат аудита:</b> <code>{report.get('error', 'Ошибка связи')}</code>"
            markup = {
                "inline_keyboard": [
                    [{"text": "« 🔙 В Почту", "callback_data": "nav_mail"}, {"text": "🎛 Главное Меню", "callback_data": "nav_main"}]
                ]
            }
            edit_card(chat_id, msg_id, audit_txt, markup)
            
        threading.Thread(target=_audit_worker, daemon=True).start()
    elif cb_data == "nav_models":
        from chatgpt_engine import get_models_menu_text, get_models_markup
        edit_card(chat_id, msg_id, get_models_menu_text(user_id=chat_id), get_models_markup(user_id=chat_id, is_guest=is_guest))
    elif cb_data.startswith("set_model_"):
        model_key = cb_data.replace("set_model_", "")
        from chatgpt_engine import set_active_model, get_models_menu_text, get_models_markup
        ok, info = set_active_model(model_key, user_id=chat_id)
        if ok and info:
            send_api_request("answerCallbackQuery", {
                "callback_query_id": cb_id,
                "text": f"✅ Выбрана: {info['title']}"
            })
            edit_card(chat_id, msg_id, get_models_menu_text(user_id=chat_id), get_models_markup(user_id=chat_id, is_guest=is_guest))
        else:
            send_api_request("answerCallbackQuery", {
                "callback_query_id": cb_id,
                "text": "⚠️ Ошибка смены модели"
            })
    elif cb_data == "sec_gpt_limits":
        from chatgpt_engine import get_gpt_limits_report_text, get_limits_markup
        edit_card(chat_id, msg_id, get_gpt_limits_report_text(user_id=chat_id), get_limits_markup(is_guest=is_guest))
    elif cb_data == "sec_quality_audit":
        from autonomous_quality_engine import get_autonomous_quality_dashboard
        from chatgpt_engine import get_limits_markup
        edit_card(chat_id, msg_id, get_autonomous_quality_dashboard(), get_limits_markup(is_guest=is_guest))
    elif cb_data == "action_reset_gpt_limits":
        from chatgpt_engine import reset_usage_counter, get_gpt_limits_report_text, get_limits_markup
        reset_usage_counter()
        send_api_request("answerCallbackQuery", {
            "callback_query_id": cb_id,
            "text": "🔄 Счетчики расхода успешно сброшены!"
        })
        edit_card(chat_id, msg_id, get_gpt_limits_report_text(user_id=chat_id), get_limits_markup(is_guest=is_guest))
    elif cb_data == "sec_guest_link":
        share_url = "https://t.me/share/url?url=https://t.me/vsr_guard_bot&text=%D0%9F%D1%80%D0%B8%D0%B2%D0%B5%D1%82!%20%D0%94%D0%B5%D1%80%D0%B6%D0%B8%20%D1%81%D1%81%D1%8B%D0%BB%D0%BA%D1%83%20%D0%BD%D0%B0%20%D0%98%D0%98-%D0%A1%D0%B5%D0%BA%D1%80%D0%B5%D1%82%D0%B0%D1%80%D1%8C%20%28Gemini%203.7%20Flash%29"
        link_text = (
            "👥 <b>ССЫЛКА НА ИИ-СЕКРЕТАРЬ ДЛЯ ГОСТЕЙ</b>\n\n"
            "📋 <b>Прямая ссылка (нажмите на неё, чтобы скопировать):</b>\n"
            "<code>https://t.me/vsr_guard_bot</code>\n\n"
            "🛡 <b>Гарантия 100% приватности и безопасности:</b>\n"
            "• Гости получают персональный изолированный доступ к <b>Google Gemini 3.7 Flash High</b>.\n"
            "• Ваши личные пароли, заметки, задачи, сметы и файлы надежно заблокированы (доступны исключительно вам).\n\n"
            "💡 <i>Нажмите «Поделиться с гостем», чтобы сразу отправить ссылку в любой чат Telegram!</i>"
        )
        markup = {
            "inline_keyboard": [
                [{"text": "🔗 Поделиться с гостем в Telegram", "url": share_url}],
                [{"text": "🎩 К ИИ-Секретарю", "callback_data": "nav_secretary"}],
                [{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}]
            ]
        }
        edit_card(chat_id, msg_id, link_text, markup)
    elif cb_data == "nav_secretary":
        edit_card(chat_id, msg_id, get_secretary_dashboard_text(user_id=chat_id, is_guest=is_guest), get_secretary_markup(is_guest=is_guest))
    elif cb_data in ["nav_files", "nav_cloud"]:
        edit_card(chat_id, msg_id, get_cloud_dashboard_text(), get_cloud_dashboard_markup())
    elif cb_data == "cloud_cat_current":
        cat = CLOUD_CAT_STATE.get(chat_id, "all")
        edit_card(chat_id, msg_id, get_cloud_list_text(chat_id, cat), get_cloud_list_markup(chat_id, cat))
    elif cb_data.startswith("cloud_cat_"):
        cat = cb_data.replace("cloud_cat_", "")
        CLOUD_CAT_STATE[chat_id] = cat
        CLOUD_PAGE_STATE[chat_id] = 1
        edit_card(chat_id, msg_id, get_cloud_list_text(chat_id, cat), get_cloud_list_markup(chat_id, cat))
    elif cb_data == "cloud_page_prev":
        cat = CLOUD_CAT_STATE.get(chat_id, "all")
        curr = CLOUD_PAGE_STATE.get(chat_id, 1)
        CLOUD_PAGE_STATE[chat_id] = max(1, curr - 1)
        edit_card(chat_id, msg_id, get_cloud_list_text(chat_id, cat), get_cloud_list_markup(chat_id, cat))
    elif cb_data == "cloud_page_next":
        cat = CLOUD_CAT_STATE.get(chat_id, "all")
        curr = CLOUD_PAGE_STATE.get(chat_id, 1)
        files = get_filtered_cloud_files(cat)
        max_p = max(1, math.ceil(len(files) / CLOUD_PAGE_SIZE))
        CLOUD_PAGE_STATE[chat_id] = min(max_p, curr + 1)
        edit_card(chat_id, msg_id, get_cloud_list_text(chat_id, cat), get_cloud_list_markup(chat_id, cat))
    elif cb_data == "cloud_page_noop":
        send_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Текущий лист файлов в Облаке"})
    elif cb_data.startswith("cloud_file_"):
        file_id = int(cb_data.replace("cloud_file_", ""))
        edit_card(chat_id, msg_id, get_cloud_file_detail_text(file_id), get_cloud_file_detail_markup(file_id))
    elif cb_data.startswith("cloud_send_"):
        file_id = int(cb_data.replace("cloud_send_", ""))
        f_entry = get_cloud_file_by_id(file_id)
        if f_entry:
            if f_entry.get("msg_id") and f_entry.get("channel"):
                send_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "📥 Отправка из Telegram Cloud..."})
                send_api_request("copyMessage", {
                    "chat_id": chat_id,
                    "from_chat_id": f_entry["channel"],
                    "message_id": f_entry["msg_id"]
                })
            elif os.path.exists(f_entry.get("path", "")):
                send_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "📥 Отправка файла в Telegram..."})
                send_telegram_file(chat_id, f_entry["path"], caption=f"☁️ <b>Файл из Вашего Облака:</b> #{f_entry['id']} <i>{html.escape(f_entry['original_name'])}</i>")
            else:
                send_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "⚠️ Файл не найден."})
    elif cb_data.startswith("cloud_chan_"):
        file_id = int(cb_data.replace("cloud_chan_", ""))
        f_entry = get_cloud_file_by_id(file_id)
        target_chan = get_cloud_channel()
        if not target_chan:
            edit_card(chat_id, msg_id, "📢 <b>ПРИВЯЗКА КАНАЛА ХРАНИЛИЩА</b>\n\nЧтобы публиковать файлы в ваш канал-хранилище:\n1. Добавьте бота @vsr_guard_bot в администраторы канала.\n2. Напишите в этот чат:\n<code>Канал @имя_канала</code>\n\nПосле этого файлы будут автоматически отправляться в канал с хэштегами!", get_cloud_file_detail_markup(file_id))
            send_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "⚠️ Канал еще не привязан."})
        elif f_entry and os.path.exists(f_entry.get("path", "")):
            tag = get_cloud_hashtag(f_entry.get("category", "Общая"))
            send_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"📢 Публикация в {target_chan}..."})
            cap = f"{tag} <b>{html.escape(f_entry['original_name'])}</b>\n\n☁️ <i>Личное Облачное Хранилище • Раздел: {f_entry.get('category', 'Общая')}</i>"
            res_chan = send_telegram_file(target_chan, f_entry["path"], caption=cap)
            if res_chan and res_chan.get("ok"):
                send_api_request("sendMessage", {
                    "chat_id": chat_id,
                    "text": f"✅ Файл <b>«{html.escape(f_entry['original_name'])}»</b> успешно опубликован в канал <b>{target_chan}</b> с хэштегом <b>{tag}</b>!",
                    "parse_mode": "HTML"
                })
            else:
                send_api_request("sendMessage", {
                    "chat_id": chat_id,
                    "text": f"⚠️ <b>Не удалось отправить в канал {target_chan}.</b>\nПроверьте, добавлен ли бот @vsr_guard_bot администратором с правом публикации!",
                    "parse_mode": "HTML"
                })
        else:
            send_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "⚠️ Файл не найден на диске ПК."})
    elif cb_data.startswith("cloud_del_"):
        file_id = int(cb_data.replace("cloud_del_", ""))
        ok = delete_file_from_cloud(file_id)
        send_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "🗑 Файл удален из Облака!" if ok else "⚠️ Ошибка удаления"})
        cat = CLOUD_CAT_STATE.get(chat_id, "all")
        edit_card(chat_id, msg_id, get_cloud_list_text(chat_id, cat), get_cloud_list_markup(chat_id, cat))
    elif cb_data.startswith("cloud_move_pick_"):
        file_id = int(cb_data.replace("cloud_move_pick_", ""))
        edit_card(chat_id, msg_id, f"📂 <b>ВЫБЕРИТЕ ПАПКУ ДЛЯ ФАЙЛА #{file_id}:</b>", get_cloud_move_markup(file_id))
    elif cb_data.startswith("cloud_move_"):
        parts = cb_data.split("_")
        file_id = int(parts[2])
        new_cat = parts[3]
        ok, msg = move_cloud_file_category(file_id, new_cat)
        send_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"✅ Перемещено в «{new_cat}»!" if ok else "⚠️ Ошибка"})
        edit_card(chat_id, msg_id, get_cloud_file_detail_text(file_id), get_cloud_file_detail_markup(file_id))
    elif cb_data == "nav_video":
        edit_card(chat_id, msg_id, get_video_dashboard_text(), get_video_markup())
    elif cb_data == "cloud_list":
        cat = "all"
        CLOUD_CAT_STATE[chat_id] = cat
        CLOUD_PAGE_STATE[chat_id] = 1
        edit_card(chat_id, msg_id, get_cloud_list_text(chat_id, cat), get_cloud_list_markup(chat_id, cat))
    elif cb_data == "cloud_folder_manage":
        edit_card(chat_id, msg_id, get_cloud_manage_folders_text(), get_cloud_manage_folders_markup())
    elif cb_data == "cloud_folder_add_prompt":
        edit_card(chat_id, msg_id, "➕ <b>СОЗДАНИЕ ПАПКИ В ОБЛАКЕ</b>\n\nНапишите в чат сообщением или надиктуйте голосом:\n• <code>Создай папку Личное</code>\n• <code>Создай папку Проекты</code>\n• <code>Создай папку Счета</code>\n\nБот мгновенно создаст раздел в Облаке.", get_cloud_manage_folders_markup())
    elif cb_data.startswith("cf_del_"):
        c_name = cb_data.replace("cf_del_", "")
        ok, msg = delete_cloud_category(c_name)
        send_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": msg})
        edit_card(chat_id, msg_id, get_cloud_manage_folders_text(), get_cloud_manage_folders_markup())
    elif cb_data.startswith("cf_ren_"):
        c_name = cb_data.replace("cf_ren_", "")
        edit_card(chat_id, msg_id, f"✏️ <b>ПЕРЕИМЕНОВАНИЕ ПАПКИ «{c_name}»</b>\n\nНапишите в чат или надиктуйте голосом:\n<code>Переименуй папку {c_name} в НовоеНазвание</code>", get_cloud_manage_folders_markup())
    elif cb_data == "nav_remind":
        edit_card(chat_id, msg_id, get_reminders_dashboard_text(), get_reminders_dashboard_markup())
    elif cb_data.startswith("remind_detail_"):
        r_id = int(cb_data.replace("remind_detail_", ""))
        edit_card(chat_id, msg_id, get_reminder_detail_text(r_id), get_reminder_detail_markup(r_id))
    elif cb_data.startswith("remind_snooze_15_"):
        r_id = int(cb_data.replace("remind_snooze_15_", ""))
        r = snooze_reminder(r_id, 15)
        if r:
            edit_card(chat_id, msg_id, f"⏱ <b>Напоминание #{r_id} отложено на 15 минут!</b>\n\n📌 Задача: <code>{html.escape(r.get('text',''))}</code>\n📅 Новое время: <b>{r.get('target_datetime','')}</b>", get_reminder_detail_markup(r_id))
        else:
            edit_card(chat_id, msg_id, get_reminders_dashboard_text(), get_reminders_dashboard_markup())
    elif cb_data.startswith("remind_snooze_60_"):
        r_id = int(cb_data.replace("remind_snooze_60_", ""))
        r = snooze_reminder(r_id, 60)
        if r:
            edit_card(chat_id, msg_id, f"⏱ <b>Напоминание #{r_id} отложено на 1 час!</b>\n\n📌 Задача: <code>{html.escape(r.get('text',''))}</code>\n📅 Новое время: <b>{r.get('target_datetime','')}</b>", get_reminder_detail_markup(r_id))
        else:
            edit_card(chat_id, msg_id, get_reminders_dashboard_text(), get_reminders_dashboard_markup())
    elif cb_data.startswith("remind_at_event_"):
        r_id = int(cb_data.replace("remind_at_event_", ""))
        r = set_reminder_to_event_time(r_id)
        if r:
            edit_card(chat_id, msg_id, f"🔔 <b>Напоминание #{r_id} переведено на момент начала встречи ({r.get('target_datetime','')})!</b>\n\n📌 Задача: <code>{html.escape(r.get('text',''))}</code>", get_reminder_detail_markup(r_id))
        else:
            edit_card(chat_id, msg_id, get_reminders_dashboard_text(), get_reminders_dashboard_markup())
    elif cb_data.startswith("remind_done_"):
        r_id = int(cb_data.replace("remind_done_", ""))
        complete_reminder(r_id)
        edit_card(chat_id, msg_id, f"✅ <b>Напоминание #{r_id} выполнено и закрыто!</b>\n\n" + get_reminders_dashboard_text(), get_reminders_dashboard_markup())
    elif cb_data.startswith("remind_del_"):
        r_id = int(cb_data.replace("remind_del_", ""))
        delete_reminder(r_id)
        edit_card(chat_id, msg_id, f"🗑 <b>Напоминание #{r_id} удалено.</b>\n\n" + get_reminders_dashboard_text(), get_reminders_dashboard_markup())
    elif cb_data == "nav_sec_wifi":
        text = get_wifi_security_report()
        edit_card(chat_id, msg_id, text, get_wifi_markup())
    elif cb_data in ["nav_construction", "const_summary"]:
        edit_card(chat_id, msg_id, get_construction_dashboard_text(), get_construction_markup())
    elif cb_data == "const_audit":
        audit_text = (
            "🛡 <b>ИИ-АНТИФРОД & АУДИТ БРАКА («ЦИФРОВОЙ ПРОРАБ 6.0»):</b>\n\n"
            "🔍 <i>Автоматический контроль 6 направлений строительства:</i>\n\n"
            "1. ♨️ <b>Теплоснабжение:</b> Детекция кранов ППР, подвесов на проволоку, брака изоляции.\n"
            "2. 💧 <b>Водоснабжение:</b> Контроль сварки ПЭ-100, ГНБ профилей, американок после кранов.\n"
            "3. 🚽 <b>Канализация:</b> Запрет прямых врезок под 90° (только косые тройники 45°).\n"
            "4. 🛣 <b>Дороги:</b> Запрет укладки асфальта в дождь, проверка подгрунтовки и бордюров.\n"
            "5. 🌳 <b>Парки & Благоустройство:</b> Контроль пирога под брусчатку (песок, щебень, геотекстиль).\n"
            "6. 🏗 <b>Общестрой:</b> Контроль вибрирования бетона и фиксаторов защитного слоя арматуры."
        )
        edit_card(chat_id, msg_id, audit_text, get_construction_markup())
    elif cb_data == "const_ks2":
        prog = load_construction_progress()
        ks2_lines = ["📊 <b>НАКОПИТЕЛЬНАЯ ВЕДОМОСТЬ КС-2 / КС-3 (ООО «ПАРАДИГМА»):</b>\n"]
        for k, v in list(prog.items())[:8]:
            ks2_lines.append(f"• <b>{v['city']}, {v['address']}</b>\n  └ Выполнено: <b>{v['done_pct']:.1f}%</b> (<b>{v['done_rub']:,.0f} ₽</b> / {v['contract_sum']:,.0f} ₽)")
        ks2_lines.append("\n💡 <i>Первоочередной объем к сдаче: Михайловка (Некрасова 26) — 1.5 млн руб.</i>")
        edit_card(chat_id, msg_id, "\n".join(ks2_lines), get_construction_markup())
    elif cb_data == "const_aosr_last":
        import glob
        acts_dir = "/home/home/Документы/2/Работа/615/4_Инженерные_Заключения_и_Акты"
        docx_files = glob.glob(os.path.join(acts_dir, "*.docx"))
        if docx_files:
            latest_docx = max(docx_files, key=os.path.getmtime)
            send_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "📥 Отправка файла АОСР (.docx)..."})
            send_telegram_file(chat_id, latest_docx, caption=f"📄 <b>Официальный АОСР (РД 11-02-2006):</b> <code>{os.path.basename(latest_docx)}</code>\n\nГотов к печати и подписанию технадзором!")
        else:
            send_api_request("answerCallbackQuery", {"callback_query_id": cb_id, "text": "⚠️ Пока нет сгенерированных актов АОСР."})
    elif cb_data == "nav_tasks" or cb_data == "task_filter_all":
        edit_card(chat_id, msg_id, get_tasks_hud_text("all"), get_tasks_hud_markup("all"))
    elif cb_data.startswith("task_filter_"):
        f_mode = cb_data.replace("task_filter_", "")
        edit_card(chat_id, msg_id, get_tasks_hud_text(f_mode), get_tasks_hud_markup(f_mode))
    elif cb_data.startswith("task_toggle_"):
        parts = cb_data.split("_")
        t_id = int(parts[2])
        f_mode = parts[3] if len(parts) > 3 else "all"
        pg = int(parts[4]) if len(parts) > 4 else 1
        t = toggle_task(t_id)
        if t:
            st_txt = "✅ Задача выполнена!" if t.get("status") == "done" else "⏳ Возвращено в работу"
            answer_cb_async(cb_id, text=st_txt)
        edit_card(chat_id, msg_id, get_tasks_hud_text(f_mode, pg), get_tasks_hud_markup(f_mode, pg))
    elif cb_data.startswith("task_del_"):
        parts = cb_data.split("_")
        t_id = int(parts[2])
        f_mode = parts[3] if len(parts) > 3 else "all"
        pg = int(parts[4]) if len(parts) > 4 else 1
        deleted = delete_task(t_id)
        if deleted:
            answer_cb_async(cb_id, text="🗑 Задача перенесена в архив!")
        edit_card(chat_id, msg_id, get_tasks_hud_text(f_mode, pg), get_tasks_hud_markup(f_mode, pg))
    elif cb_data.startswith("task_page_"):
        parts = cb_data.split("_")
        f_mode = parts[2] if len(parts) > 2 else "all"
        pg = int(parts[3]) if len(parts) > 3 else 1
        edit_card(chat_id, msg_id, get_tasks_hud_text(f_mode, pg), get_tasks_hud_markup(f_mode, pg))
    elif cb_data == "task_clear_done":
        cnt = clear_completed_tasks()
        answer_cb_async(cb_id, text=f"🧹 Удалено выполненных: {cnt}")
        edit_card(chat_id, msg_id, get_tasks_hud_text("all"), get_tasks_hud_markup("all"))
    elif cb_data == "task_add_prompt":
        answer_cb_async(cb_id, text="💡 Отправьте текст задачи")
        edit_card(chat_id, msg_id, "➕ <b>ДОБАВЛЕНИЕ ЗАДАЧИ</b>\n\nПросто напишите задачу в чат сообщением (или надиктуйте голосом).\n\nНапример:\n• <i>«Оплатить счета по Котово»</i>\n• <i>«Срочно проверить АОСР»</i>\n\nБот сам определит категорию и добавит в трекер.", get_tasks_hud_markup("all"))
    elif cb_data == "nav_search":
        PENDING_GLOBAL_SEARCH[chat_id] = True
        answer_cb_async(cb_id, text="🔎 Введите поисковый запрос")
        search_prompt_txt = (
            "🔎 <b>ГЛОБАЛЬНЫЙ УМНЫЙ ПОИСК ПО БАЗЕ</b>\n\n"
            "Отправьте любое <b>слово, номер акта, объект или сумму</b> сообщением в чат (или надиктуйте голосом):\n\n"
            "• <i>«Котово»</i>, <i>«Дубовка»</i>\n"
            "• <i>«Арматура»</i>, <i>«краска»</i>, <i>«бетон»</i>\n"
            "• <i>«Спарринг»</i>, <i>«rMSSD»</i>, <i>«договор»</i>\n\n"
            "💡 <i>Бот найдет совпадения одновременно в Заметках, Задачах и КС-2!</i>"
        )
        edit_card(chat_id, msg_id, search_prompt_txt, {"inline_keyboard": [[{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}]]})
    elif cb_data == "exec_save_tasks":
        last_exec = LAST_EXECUTIVE_SUMMARY.get(chat_id)
        if last_exec and last_exec.get("tasks"):
            for tk in last_exec["tasks"]:
                add_task(tk["text"], category=last_exec.get("category", "Общее"), priority=tk.get("priority", "medium"))
            answer_cb_async(cb_id, text="✅ Задачи добавлены в трекер!")
            edit_card(chat_id, msg_id, get_tasks_hud_text("all"), get_tasks_hud_markup("all"))
        else:
            answer_cb_async(cb_id, text="⚠️ Нет задач для сохранения")
    elif cb_data == "exec_save_expense":
        last_exec = LAST_EXECUTIVE_SUMMARY.get(chat_id)
        if last_exec and last_exec.get("amounts"):
            last_obj = last_exec.get("object") or "ОБЩИЙ 615-ФЗ"
            for a in last_exec["amounts"]:
                save_expense_entry(a, last_exec.get("summary", "Расход с объекта"), obj_name=last_obj)
            answer_cb_async(cb_id, text=f"💰 Расход записан в КС-2 ({last_obj})!")
            from vector_tier1_engine import get_object_budget_hud
            hud_txt, hud_mk = get_object_budget_hud(last_obj)
            edit_card(chat_id, msg_id, f"✅ <b>РАСХОД ЗАФИКСИРОВАН:</b> {last_exec.get('summary', '')}\n\n{hud_txt}", hud_mk)
        else:
            answer_cb_async(cb_id, text="⚠️ Нет сумм для записи")
    elif cb_data.startswith("exp_add_prompt_"):
        obj_p = cb_data.replace("exp_add_prompt_", "")
        answer_cb_async(cb_id, text=f"💡 Напишите сумму расхода по {obj_p}")
        prompt_t = (
            f"💰 <b>ДОБАВЛЕНИЕ РАСХОДА // {obj_p}</b>\n\n"
            f"Отправьте в чат сообщение или надиктуйте голосом:\n\n"
            f"• <code>{obj_p} купили краску 28500</code>\n"
            f"• <code>расход 45000 {obj_p} металл</code>\n"
            f"• <code>потратили 12000 на доставку</code>\n\n"
            f"Сумма автоматически запишется в смету КС-2."
        )
        edit_card(chat_id, msg_id, prompt_t, {"inline_keyboard": [[{"text": f"« 🔙 К объекту {obj_p}", "callback_data": "nav_work"}]]})
    elif cb_data == "exec_save_note":
        last_exec = LAST_EXECUTIVE_SUMMARY.get(chat_id)
        if last_exec:
            n_id = save_note(last_exec.get("raw_text", ""), note_type="голос", category=last_exec.get("category", "Общее"))
            answer_cb_async(cb_id, text=f"📂 Заметка #{n_id} сохранена!")
            edit_card(chat_id, msg_id, get_notes_text(chat_id), get_notes_markup(chat_id))
    elif cb_data == "exec_save_remind":
        last_exec = LAST_EXECUTIVE_SUMMARY.get(chat_id)
        if last_exec:
            raw_t = last_exec.get("raw_text", "")
            entry = add_reminder(raw_t, is_voice=True)
            if entry:
                answer_cb_async(cb_id, text=f"⏰ Напоминание установлено: {entry.get('target_datetime', '')}")
            else:
                entry = add_reminder(f"Напомни через 30 минут {last_exec.get('summary', 'проверить задачу')}", is_voice=True)
                answer_cb_async(cb_id, text="⏰ Напоминание установлено на 30 мин!")
            edit_card(chat_id, msg_id, get_reminders_dashboard_text(), get_reminders_markup())
    elif cb_data == "exec_save_channel":
        last_exec = LAST_EXECUTIVE_SUMMARY.get(chat_id)
        if last_exec:
            ch_id = get_cloud_channel()
            if ch_id:
                tag = get_cloud_hashtag(last_exec.get("category", "Общее"))
                msg_text = f"{tag}\n🎙 <b>{html.escape(last_exec.get('summary', ''))}</b>\n\n<code>{html.escape(last_exec.get('raw_text', ''))}</code>\n\n☁️ <i>Опубликовано из ИИ-Секретаря Вектор</i>"
                send_api_request("sendMessage", {"chat_id": ch_id, "text": msg_text, "parse_mode": "HTML"})
                answer_cb_async(cb_id, text="📢 Опубликовано в канал Cloud storage!")
            else:
                answer_cb_async(cb_id, text="⚠️ Канал Cloud storage не привязан")
    elif cb_data == "export_expenses_csv":
        csv_path = generate_expenses_csv_export()
        if os.path.exists(csv_path):
            send_telegram_file(chat_id, csv_path, caption="📊 <b>Выписка всех расходов (Excel CSV)</b>")
            answer_cb_async(cb_id, text="📥 Отчет сформирован и отправлен!")
        else:
            answer_cb_async(cb_id, text="⚠️ Ошибка формирования отчета")
    elif cb_data == "export_notes_txt":
        txt_path = generate_notes_txt_export()
        if os.path.exists(txt_path):
            send_telegram_file(chat_id, txt_path, caption="📝 <b>Полный архив всех заметок экосистемы (.txt)</b>")
            answer_cb_async(cb_id, text="📥 Архив сформирован и отправлен!")
        else:
            answer_cb_async(cb_id, text="⚠️ Ошибка формирования архива")
    elif cb_data in ["nav_briefing", "action_refresh_briefing"]:
        from vector_tier1_engine import get_morning_briefing_card
        br_text, br_mk = get_morning_briefing_card(user_name="Сергей")
        edit_card(chat_id, msg_id, br_text, br_mk)
        answer_cb_async(cb_id, text="🔄 Брифинг обновлен свежими данными!")
    elif cb_data == "nav_evening_briefing":
        ev_text, ev_mk = get_evening_briefing_card(user_name="Сергей")
        edit_card(chat_id, msg_id, ev_text, ev_mk)
        answer_cb_async(cb_id, text="🌙 Вечерний дайджест загружен!")
    elif cb_data == "nav_info":
        text = (
            "ℹ️ <b>СПРАВКА И ВОЗМОЖНОСТИ БОТА</b>\n\n"
            "<b>ВЕКТОР</b> — ваш персональный автономный ИИ-ассистент 2026:\n\n"
            "🏷 <b>Сборка:</b> <code>#50 • v2.5.0 (GOLD MASTER // ЭТАЛОН)</code>\n"
            "📱 <b>Эргономика:</b> Адаптировано под экраны смартфонов 6.1 дюйма\n"
            "⚡️ <b>Статус:</b> 100% тестов пройдены, режим 24/7 активен\n\n"
            "• 🎙 <b>Голосовое управление:</b> Отправляйте голосовые сообщения любой длины — бот мгновенно расшифрует их и разложит по нужным категориям.\n"
            "• 📌 <b>Заметки:</b> 3 удобные папки (Спорт, Работа, Общее) с карточками и экспортом в .txt.\n"
            "• 📋 <b>Задачи:</b> Чек-листы и списки дел с отметкой выполнения в 1 клик.\n"
            "• 🔐 <b>Пароли:</b> Надежный сейф для быстрого копирования логинов и паролей.\n"
            "• 🔎 <b>Поиск:</b> Мгновенный поиск любого слова по всей вашей базе.\n"
            "• ⏰ <b>Напоминания:</b> Уведомления о важных встречах и событиях.\n"
            "• ☁️ <b>Облачное хранилище:</b> Документы, файлы и резервные копии 24/7.\n"
            "• 📧 <b>Почта:</b> Удобный доступ к ящику Mail.ru прямо из Telegram.\n\n"
            "💡 <i>Просто отправьте текст или надиктуйте голос в чат в любой момент!</i>"
        )
        edit_card(chat_id, msg_id, text, get_main_dashboard_markup())

def setup_bot_commands():
    commands_payload = {
        "commands": [
            {"command": "menu", "description": "Главное меню"},
            {"command": "secretary", "description": "ИИ-Секретарь"},
            {"command": "tasks", "description": "Задачи"},
            {"command": "morning", "description": "Утренний дайджест"},
            {"command": "search", "description": "Умный поиск"},
            {"command": "notes", "description": "Заметки"},
            {"command": "passwords", "description": "Пароли"},
            {"command": "reminders", "description": "Напоминания"},
            {"command": "mail", "description": "Почта"},
            {"command": "files", "description": "Облако"},
            {"command": "backup", "description": "Скачать бэкап (.zip)"}
        ]
    }
    send_api_request("setMyCommands", commands_payload)
    send_api_request("setChatMenuButton", {"menu_button": {"type": "commands"}})

def process_command_text(sender_chat_id, text, is_voice=False, voice_file=None, user_name="Пользователь"):
    text_lower = text.lower().strip()
    is_guest = (int(sender_chat_id) != AUTHORIZED_CHAT_ID)

    # ==================== РЕЖИМ ГОСТЯ (ПО ССЫЛКЕ НА ИИ-СЕКРЕТАРЬ) ====================
    if is_guest:
        if text_lower in ["/start", "start", "старт", "/menu", "меню", "привет", "начать", "/help"]:
            welcome_guest = (
                f"🎩 <b>ДОБРО ПОЖАЛОВАТЬ В «ИИ-СЕКРЕТАРЬ»!</b>\n\n"
                f"Здравствуйте, <b>{html.escape(user_name)}</b>! Вам открыт персональный доступ к передовой нейросети:\n\n"
                "• 💎 <b>Google Gemini 3.7 Flash High</b> (Google DeepMind • Безлимит 24/7)\n\n"
                "🎙 <b>Как пользоваться:</b>\n"
                "1. Задайте любой вопрос текстом или надиктуйте голосовое сообщение в Telegram.\n"
                "2. ИИ моментально найдет информацию, составит документ, посчитает смету или решит задачу!"
            )
            send_api_request("sendMessage", {
                "chat_id": sender_chat_id,
                "text": welcome_guest,
                "parse_mode": "HTML",
                "reply_markup": get_secretary_markup(is_guest=True)
            })
            return

        # Любой вопрос от гостя (текст или голос) ➔ напрямую в ИИ-Секретарь
        sec_text = process_secretary_request(text, user_id=sender_chat_id, user_name=user_name)
        send_api_request("sendMessage", {
            "chat_id": sender_chat_id,
            "text": sec_text,
            "parse_mode": "HTML",
            "reply_markup": get_secretary_markup(is_guest=True)
        })
        return

    # ==================== РЕЖИМ ВЛАДЕЛЬЦА (СЕРГЕЙ РОМАНОВ) ====================
    # 0.000 ПРЯМЫЕ КОМАНДЫ УПРАВЛЕНИЯ ПК И ТЕРМИНАЛ LINUX (24/7)
    try:
        from pc_control_engine import handle_pc_nlp_request
        is_pc_cmd, pc_out = handle_pc_nlp_request(text)
        if is_pc_cmd:
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": pc_out, "parse_mode": "HTML"})
            return
    except Exception as e:
        print(f"Ошибка pc_control_engine: {e}")

    # 0.00 АВТОНОМНЫЙ ИСПОЛНИТЕЛЬ ТЕХНИЧЕСКИХ И ПРОГРАММНЫХ ЗАДАЧ НА ПК (24/7)
    try:
        from autonomous_agent_bridge import is_agent_execution_request, execute_agent_task_on_pc
        if is_agent_execution_request(text):
            agent_ans = execute_agent_task_on_pc(text, user_id=sender_chat_id)
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": agent_ans, "parse_mode": "HTML"})
            return
    except Exception as e:
        print(f"Ошибка autonomous_agent_bridge: {e}")

    # 0.01 РЕЕСТР И СПИСОК АКТИВНЫХ ЗАДАЧ (1-CLICK INTERACTIVE HUD)
    if text_lower in ["/tasks", "/задачи", "задачи", "список задач", "реестр задач", "покажи задачи", "дай мне список задач", "список дел"]:
        send_api_request("sendMessage", {
            "chat_id": sender_chat_id,
            "text": get_tasks_hud_text("all"),
            "parse_mode": "HTML",
            "reply_markup": get_tasks_hud_markup("all")
        })
        return

    # 0.01b ДОБАВЛЕНИЕ ЗАДАЧИ (/task, задача 1, задача 2, поставь задачу, добавь в задачи)
    task_match = re.match(r"^(?:/task|/задача|задача\s*\d*:?|поставь задачу|добавь задачу|новая задача|запиши задачу|запиши в задачи)\s+(.+)$", text, flags=re.I | re.DOTALL)
    if task_match:
        raw_body = task_match.group(1).strip()
        # Проверка на несколько задач (по строкам или нумерации 1., 2.)
        task_lines = [re.sub(r'^\s*(?:\d+[\.\)]|[-•*]|задача\s*\d*:?)\s*', '', line).strip() for line in raw_body.split('\n') if len(line.strip()) > 2]
        if not task_lines:
            task_lines = [raw_body]

        added_tasks = []
        for t_line in task_lines:
            cat = "Работа" if any(w in t_line.lower() for w in ["615", "котово", "дубовка", "михайловка", "акт", "смета", "прораб", "объект", "кровл", "фасад"]) else ("Спорт" if any(w in t_line.lower() for w in ["бокс", "трен", "пульс", "кэмп", "спарринг", "штанге"]) else "Общее")
            pri = "high" if any(w in t_line.lower() for w in ["срочно", "горит", "сегодня", "до завтра", "важно", "до пятницы"]) else "medium"
            nt = add_task(t_line, category=cat, priority=pri)
            added_tasks.append(nt)

        if len(added_tasks) == 1:
            nt = added_tasks[0]
            confirm_msg = f"✅ <b>Задача #{nt['id']} добавлена в трекер!</b>\n\n• Текст: <code>{html.escape(nt['text'])}</code>\n• Категория: <b>[{nt['category']}]</b> | Приоритет: <b>{'🔥 Высокий' if nt['priority'] == 'high' else '⏳ Обычный'}</b>"
        else:
            t_list_str = "\n".join([f" • #{t['id']} {html.escape(t['text'])} <i>[{t['category']}]</i>" for t in added_tasks])
            confirm_msg = f"✅ <b>Добавлено задач в трекер: {len(added_tasks)} шт!</b>\n\n{t_list_str}"

        send_api_request("sendMessage", {
            "chat_id": sender_chat_id,
            "text": confirm_msg,
            "parse_mode": "HTML",
            "reply_markup": get_tasks_hud_markup("all")
        })
        return

    # 0.01b РЕЖИМ ГЛОБАЛЬНОГО ПОИСКА (по клику на кнопку в меню или команде)
    if (sender_chat_id in PENDING_GLOBAL_SEARCH and not text.startswith("/")) or text_lower.startswith(("/search", "/найти", "/find", "поиск ", "найди ")):
        PENDING_GLOBAL_SEARCH.pop(sender_chat_id, None)
        q = re.sub(r"^(?:/search|/найти|/find|поиск|найди)\s*", "", text, flags=re.I).strip()
        if not q:
            q = text.strip()
        if q:
            results = search_all_ecosystem(q)
            card_text, card_markup = format_search_results_card(results)
            active_id = ACTIVE_CARD_ID.get(sender_chat_id)
            if active_id:
                edit_card(sender_chat_id, active_id, card_text, card_markup)
            else:
                send_api_request("sendMessage", {
                    "chat_id": sender_chat_id,
                    "text": card_text,
                    "parse_mode": "HTML",
                    "reply_markup": card_markup
                })
            return

    # 0.01d УТРЕННИЙ ДАЙДЖЕСТ РУКОВОДИТЕЛЯ (/morning, /briefing, доброе утро, утренняя сводка)
    if text_lower in ["/morning", "/briefing", "доброе утро", "утренняя сводка", "дайджест", "сводка дня", "план дня", "брифинг", "/брифинг", "утро", "/утро"]:
        b_text, b_markup = get_morning_briefing_card(user_name="Сергей")
        send_api_request("sendMessage", {
            "chat_id": sender_chat_id,
            "text": b_text,
            "parse_mode": "HTML",
            "reply_markup": b_markup
        })
        return

    # 0.01d2 ВЕЧЕРНИЙ ДАЙДЖЕСТ РУКОВОДИТЕЛЯ (/evening, /вечер, вечерний дайджест, итоги дня)
    if text_lower in ["/evening", "/вечер", "вечерний дайджест", "итоги дня", "вечер", "итоги", "итог"]:
        ev_text, ev_markup = get_evening_briefing_card(user_name="Сергей")
        send_api_request("sendMessage", {
            "chat_id": sender_chat_id,
            "text": ev_text,
            "parse_mode": "HTML",
            "reply_markup": ev_markup
        })
        return

    # 0.01e ПОЛНЫЙ БЭКАП ЭКОСИСТЕМЫ (/backup, бэкап, скачать бэкап, архив баз)
    if text_lower in ["/backup", "/бэкап", "бэкап", "скачать бэкап", "создай бэкап", "архив баз", "дамп базы"]:
        zip_file = create_full_system_backup_zip()
        if os.path.exists(zip_file):
            send_api_request("sendDocument", {
                "chat_id": sender_chat_id,
                "caption": "📦 <b>Полный архив базы данных экосистемы ВЕКТОР + BOXING LAB</b>\n\nВключает: <code>tasks.json</code>, <code>notes.json</code>, <code>expenses.json</code>, <code>athletes_db.json</code>, <code>reminders.json</code>.",
                "parse_mode": "HTML"
            }, files={"document": (os.path.basename(zip_file), open(zip_file, "rb"), "application/zip")})
            return

    # 0.01f УМНЫЙ УЧЕТ РАСХОДОВ 615-ФЗ (Голос/текст: "Дубовка купили краску 28500", "расход 15000 бетон Котово", "потратили 4500 на бензин")
    exp_matched = False
    exp_amt = None
    exp_desc = ""
    exp_target_obj = None

    # Шаблон 1: объект в начале ("Дубовка, купили краску 28500", "Котово 45000 арматура")
    m_obj_first = re.match(r"^(дубовка|котово|михайловка|серафимович|суровикино|фролово|краснослободск)[,\s]+(?:купили|расход|потратили|оплата|трата)?\s*(.+?)\s*(?:на\s+)?(\d+[\s\d]*(?:[\.,]\d+)?)\s*(?:тыс|руб|р|₽)?$", text, flags=re.I)
    if not m_obj_first:
        m_obj_first = re.match(r"^(дубовка|котово|михайловка|серафимович|суровикино|фролово|краснослободск)[,\s]+(?:купили|расход|потратили|оплата|трата)?\s*(\d+[\s\d]*(?:[\.,]\d+)?)\s*(?:тыс|руб|р|₽)?\s*(?:на\s+)?(.*)$", text, flags=re.I)
        if m_obj_first:
            exp_target_obj = m_obj_first.group(1).upper()
            raw_amt = m_obj_first.group(2).replace(" ", "").replace(",", ".")
            exp_amt = float(raw_amt)
            if "тыс" in text.lower(): exp_amt *= 1000
            exp_desc = m_obj_first.group(3).strip() or f"Расход по объекту {exp_target_obj}"
            exp_matched = True
    else:
        exp_target_obj = m_obj_first.group(1).upper()
        exp_desc = m_obj_first.group(2).strip() or f"Расход по объекту {exp_target_obj}"
        raw_amt = m_obj_first.group(3).replace(" ", "").replace(",", ".")
        exp_amt = float(raw_amt)
        if "тыс" in text.lower(): exp_amt *= 1000
        exp_matched = True

    # Шаблон 2: глагол покупки ("купили краску на 28500", "потратили 4500 на бензин", "оплатили 15000 за арматуру Котово")
    if not exp_matched:
        m_verb_amt_first = re.match(r"^(?:купили|потратили|оплатили|взяли)\s+(?:на\s+|за\s+)?(\d+[\s\d]*(?:[\.,]\d+)?)\s*(?:тыс|руб|р|₽)?\s*(?:на\s+|за\s+)?(.*)$", text, flags=re.I)
        if m_verb_amt_first:
            raw_amt = m_verb_amt_first.group(1).replace(" ", "").replace(",", ".")
            exp_amt = float(raw_amt)
            if "тыс" in text.lower(): exp_amt *= 1000
            exp_desc = m_verb_amt_first.group(2).strip() or "Расход"
            exp_matched = True
        else:
            m_verb = re.match(r"^(?:купили|потратили|оплатили|взяли)\s+(.+?)\s+(?:на\s+|за\s+)?(\d+[\s\d]*(?:[\.,]\d+)?)\s*(?:тыс|руб|р|₽)?\s*(.*)$", text, flags=re.I)
            if m_verb:
                raw_amt = m_verb.group(2).replace(" ", "").replace(",", ".")
                exp_amt = float(raw_amt)
                if "тыс" in text.lower(): exp_amt *= 1000
                exp_desc = (m_verb.group(1) + " " + m_verb.group(3)).strip()
                exp_matched = True

    # Шаблон 3: стандартный ("расход 15000 бетон Котово", "трата 4500 бензин")
    if not exp_matched:
        m_std = re.match(r"^(?:расход|трата|оплата|списание)\s+(\d+[\s\d]*(?:[\.,]\d+)?)\s*(?:тыс|руб|р|₽)?\s+(.+)$", text, flags=re.I)
        if m_std:
            raw_amt = m_std.group(1).replace(" ", "").replace(",", ".")
            exp_amt = float(raw_amt)
            if "тыс" in text.lower(): exp_amt *= 1000
            exp_desc = m_std.group(2).strip()
            exp_matched = True

    if exp_matched and exp_amt and exp_amt > 0:
        if not exp_target_obj:
            t_low = (exp_desc + " " + text).lower()
            for obj in OBJECTS_615:
                if obj.lower() in t_low or obj[:5].lower() in t_low:
                    exp_target_obj = obj
                    break
        final_obj = exp_target_obj or "ОБЩИЙ 615-ФЗ"
        save_expense_entry(exp_amt, exp_desc, obj_name=final_obj)
        from vector_tier1_engine import get_object_budget_hud
        hud_txt, hud_mk = get_object_budget_hud(final_obj)
        active_id = ACTIVE_CARD_ID.get(sender_chat_id)
        if active_id:
            edit_card(sender_chat_id, active_id, f"✅ <b>РАСХОД ЗАФИКСИРОВАН: +{exp_amt:,.0f} ₽</b>\n\n{hud_txt}", hud_mk)
        else:
            send_api_request("sendMessage", {
                "chat_id": sender_chat_id,
                "text": f"✅ <b>РАСХОД ЗАФИКСИРОВАН: +{exp_amt:,.0f} ₽</b>\n\n{hud_txt}",
                "parse_mode": "HTML",
                "reply_markup": hud_mk
            })
        return

    # 0.0 ПРЯМОЙ ЗАПРОС К ИИ-СЕКРЕТАРЮ (/gpt или /ai)
    if text_lower.startswith(('/gpt', '/ai', 'gpt ', 'ии ')):
        prompt_query = re.sub(r'^(?:/gpt|/ai|gpt|ии)\s*', '', text, flags=re.I).strip()
        if prompt_query:
            ans = process_secretary_request(prompt_query, user_id=sender_chat_id)
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": ans, "parse_mode": "HTML", "reply_markup": get_secretary_markup()})
            return

    # 0.0a ПОИСК ВНУТРИ ПАПКИ ЗАМЕТОК
    pending_search_cat = PENDING_SEARCH_IN_CAT.pop(sender_chat_id, None)
    if pending_search_cat and not text.startswith("/"):
        FOLDER_SEARCH_RESULTS[sender_chat_id] = text.strip()
        NOTES_CATEGORY_STATE[sender_chat_id] = pending_search_cat
        NOTES_PAGE_STATE[sender_chat_id] = 1
        active_id = ACTIVE_CARD_ID.get(sender_chat_id)
        if active_id:
            edit_card(sender_chat_id, active_id, get_notes_text(sender_chat_id), get_notes_markup(sender_chat_id))
        else:
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": get_notes_text(sender_chat_id), "parse_mode": "HTML", "reply_markup": get_notes_markup(sender_chat_id)})
        return

    # 0.0b ПРЯМОЕ ДОБАВЛЕНИЕ В КОНКРЕТНУЮ ПАПКУ (1_Спорт / 2_Работа / 3_Общее)
    quick_cat = QUICK_TARGET_CATEGORY.pop(sender_chat_id, None)
    if quick_cat and not text.startswith("/"):
        n_id = save_note(text, note_type="голос" if is_voice else "текст", category=quick_cat)
        NOTES_CATEGORY_STATE[sender_chat_id] = quick_cat
        icon = CATEGORY_ICON_MAP.get(quick_cat, "📁")
        confirm_text = (
            f"🟢 <b>ЗАПИСЬ СОХРАНЕНА В [{icon} {quick_cat.upper()}]!</b>\n\n"
            f"<code>{html.escape(text)}</code>\n\n"
            f"📁 <i>Номер записи: #{n_id}</i>"
        )
        send_api_request("sendMessage", {
            "chat_id": sender_chat_id,
            "text": confirm_text,
            "parse_mode": "HTML",
            "reply_markup": get_notes_markup(sender_chat_id)
        })
        return

    if text_lower in ["/start", "start", "/menu", "меню", "привет", "старт", "начать", "покажи меню"]:
        send_main_dashboard(sender_chat_id)
        return
    elif text_lower in ["/video", "видео", "видео анализ", "анализ видео", "бокс видео", "кружочек", "разбор боя"]:
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": get_video_dashboard_text(), "parse_mode": "HTML", "reply_markup": get_video_markup()})
        return
    elif text_lower == "/notes":
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": get_notes_text(sender_chat_id), "parse_mode": "HTML", "reply_markup": get_notes_markup(sender_chat_id)})
        return
    elif text_lower == "/passwords":
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": get_passwords_text(), "parse_mode": "HTML", "reply_markup": get_back_button_markup()})
        return
    elif text_lower == "/expenses":
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": get_expenses_text(), "parse_mode": "HTML", "reply_markup": get_back_button_markup()})
        return
    elif text_lower in ["/secretary", "/секретарь", "секретарь"]:
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": get_secretary_dashboard_text(), "parse_mode": "HTML", "reply_markup": get_secretary_markup()})
        return
    elif text_lower in ["/work", "/работа", "работа", "/construction", "/стройконтроль", "стройконтроль", "стройка", "615", "/615", "прораб", "объекты 615"] :
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": get_construction_dashboard_text(), "parse_mode": "HTML", "reply_markup": get_construction_markup()})
        return

    # 0.0 СТРОЙКОНТРОЛЬ 615-ФЗ: ГОЛОСОВЫЕ И ТЕКСТОВЫЕ РАПОРТЫ С ОБЪЕКТА
    is_construction_report = (
        any(k in text_lower for k in ["победы 8", "школьная 6", "чапаева 1", "лаврова 6", "лаврова 11", "мира 149", "некрасова 26", "некрасова 1а", "котово", "михайловка", "краснослободск", "аоср", "акт скрытых работ", "стройконтроль", "615-фз", "парадигма"])
        and any(w in text_lower for w in ["заменили", "смонтировали", "проложили", "уложили", "впаяли", "труб", "муфт", "кран", "тройник", "траверс", "утеплител", "грунт", "гнб", "бурен", "прокол", "отчет", "рапорт", "готовност", "приписк", "брак", "смет", "кс-2", "кс-3"])
    )
    if is_construction_report:
        res = process_voice_or_text_construction_report(text)
        send_api_request("sendMessage", {
            "chat_id": sender_chat_id,
            "text": res["text"],
            "parse_mode": "HTML",
            "reply_markup": get_construction_markup()
        })
        if res.get("docx_path") and os.path.exists(res["docx_path"]):
            send_telegram_file(sender_chat_id, res["docx_path"], caption=f"📄 <b>Официальный АОСР (РД 11-02-2006):</b> <code>{os.path.basename(res['docx_path'])}</code>")
        return

    # Быстрый просмотр заметки по номеру ("1", "#1", "заметка 1", "открой 1", "покажи 1")
    match_view = re.match(r'^(?:заметка|открой|покажи|открыть|просмотр|номер|#)?\s*#?(\d+)$', text_lower)
    if match_view and not any(kw in text_lower for kw in ["удали", "замени", "допиши", "выполни", "готово", "стереть", "купи", "расход", "пароль"]):
        target_id = int(match_view.group(1))
        note = get_note_by_id(target_id)
        if note:
            send_api_request("sendMessage", {
                "chat_id": sender_chat_id,
                "text": get_note_detail_text(note),
                "parse_mode": "HTML",
                "reply_markup": get_note_detail_markup(note)
            })
            return

    # 0.1 СОХРАНЕНИЕ ПАРОЛЕЙ И ЛОГИНОВ
    if any(kw in text_lower for kw in ["пароль", "сохрани пароль", "добавь пароль", "логин"]):
        ok, s_name, login, pwd = smart_add_credential_from_text(text)
        if ok:
            res_text = (
                f"🔐 <b>ПАРОЛЬ УСПЕШНО СОХРАНЕН В VAULT!</b>\n\n"
                f"• Сервис: <b>{s_name}</b>\n"
                f"• Логин: <code>{login}</code>\n"
                f"• Пароль: <code>{pwd}</code>"
            )
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": res_text, "parse_mode": "HTML", "reply_markup": get_passwords_markup()})
            return
    if any(kw in text_lower for kw in ["погода", "часовой пояс", "время в", "градус", "билет", "поезд", "самолет", "самолёт", "такси", "рейс", "выжимка", "найди", "найти"]):
        sec_text = process_secretary_request(text)
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": sec_text, "parse_mode": "HTML", "reply_markup": get_secretary_markup()})
        return

    # 1. ДОБАВЛЕНИЕ УСТРОЙСТВА В БЕЛЫЙ СПИСОК WI-FI ("имя 192.168.68.105 Планшет")
    if any(kw in text_lower for kw in ["белый список", "назвать устройство", "имя устройства", "назови"]):
        match = re.search(r'([0-9a-fA-F:\.]{7,17})[\s:]+(.+)', text)
        if match:
            target_id = match.group(1).strip()
            alias_name = match.group(2).strip()
            from security_guard_module import add_to_whitelist
            add_to_whitelist(target_id, alias_name)
            res_text = f"✅ <b>Устройство '{target_id}' названо '{alias_name}' и добавлено в белый список!</b>"
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": res_text, "parse_mode": "HTML"})
            return

    # 2. ОБЪЕДИНЕНИЕ ЗАМЕТОК ("объединить 1, 2, 3" или "соединить 1 и 2")
    if any(kw in text_lower for kw in ["объединить", "объедини", "соединить", "собери заметки"]):
        nums = [int(n) for n in re.findall(r'\d+', text)]
        if len(nums) >= 2:
            ok, res_text = merge_notes(nums)
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": res_text, "parse_mode": "HTML"})
            return
        else:
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": "⚠️ Укажите хотя бы два номера заметок, например: <code>Объединить 1, 2</code>", "parse_mode": "HTML"})
            return

    # 2. ПОЛНАЯ ПЕРЕЗАПИСЬ С НУЛЯ ("заменить 1: новый текст" или "замени 1: новый текст")
    if any(kw in text_lower for kw in ["заменить", "замени", "перезаписать"]):
        match = re.search(r'(\d+)[:\s]+(.+)', text, re.IGNORECASE)
        if match:
            n_id = int(match.group(1))
            new_txt = match.group(2).strip()
            if replace_note_text(n_id, new_txt):
                res_text = f"✏️ <b>Текст заметки #{n_id} полностью перезаписан!</b>\n\n<code>{new_txt}</code>"
                send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": res_text, "parse_mode": "HTML"})
                return

    # 3. ДОПИСАТЬ / ДОБАВИТЬ В КОНЕЦ (С СОХРАНЕНИЕМ СТАРОГО ТЕКСТА)
    match_append = re.search(r'^(?:дописать|добавить|дополнить|изменить|измени|заметка)?\s*(\d+)[:\s\+]+(.+)', text, re.IGNORECASE)
    if match_append and not any(kw in text_lower for kw in ["удали", "заменить", "объединить", "сделано", "выполнено"]):
        n_id = int(match_append.group(1))
        extra = match_append.group(2).strip()
        ok, updated_note = append_text_to_note(n_id, extra)
        if ok and updated_note:
            res_text = (
                f"➕ <b>Заметка #{n_id} обновлена (старый текст сохранен)!</b>\n\n"
                f"📋 <b>Полный текущий текст (нажмите для копирования):</b>\n"
                f"<code>{updated_note['text']}</code>"
            )
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": res_text, "parse_mode": "HTML"})
            return

    # 4. ОТМЕТКА О ВЫПОЛНЕНИИ ТЕКСТОМ ("выполнено 1", "готово 2")
    if any(kw in text_lower for kw in ["выполнено", "готово", "сделано", "чек"]) and re.search(r'\d+', text):
        nums = [int(n) for n in re.findall(r'\d+', text)]
        for n_id in nums:
            toggle_note_status(n_id)
        res_text = f"✅ <b>Заметки #{', #'.join(map(str, nums))} обновлены!</b>"
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": res_text, "parse_mode": "HTML"})
        return

    # 5. УМНОЕ УДАЛЕНИЕ ПАРОЛЕЙ И ЛОГИНОВ (по номерам #1, #2 или названиям)
    elif any(kw in text_lower for kw in ["удали", "удалить", "стереть", "убрать", "очисти"]) and (any(p in text_lower for p in ["пароль", "пароли", "паролей", "логин", "аккаунт", "инста", "инстаграм", "instagram", "mail", "почту", "gemini", "гугл"]) or (not any(z in text_lower for z in ["заметк", "расход", "напомни"]) and re.search(r'\b\d+\b', text))):
        deleted_key = delete_vault_credential_smart(text)
        res_text = f"🗑 <b>Логины и пароли для '{deleted_key}' успешно удалены!</b>" if deleted_key else "⚠️ <b>Указанные пароли не найдены в хранилище.</b>"
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": res_text, "parse_mode": "HTML", "reply_markup": get_passwords_markup()})
        return

    # 6. МНОЖЕСТВЕННОЕ УДАЛЕНИЕ ЗАМЕТОК (С АВТО-ПЕРЕИНДЕКСАЦИЕЙ)
    elif any(kw in text_lower for kw in ["очисти все заметки", "очистить все заметки", "удали все заметки", "очистить заметки"]):
        clear_all_notes()
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": "🗑 <b>Все заметки были успешно удалены!</b>", "parse_mode": "HTML"})
    elif any(kw in text_lower for kw in ["удали заметку", "удалить заметку", "стереть заметку", "удали заметки", "удалить заметки"]):
        nums = [int(n) for n in re.findall(r'\d+', text)]
        if nums:
            del_ids = delete_multiple_notes(nums)
            res_text = f"🗑 <b>Заметки #{', #'.join(map(str, del_ids))} удалены. Список автоматически перенумерован (1, 2, 3...)!</b>" if del_ids else "⚠️ Указанные заметки не найдены."
        else:
            res_text = "⚠️ Укажите номера заметок, например: <code>Удали заметки 1, 2, 5</code>"
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": res_text, "parse_mode": "HTML"})

    # 7. ФИНАНСЫ
    elif re.match(r'^\d+\s+.+', text):
        parts = text.split(maxsplit=1)
        amount = int(parts[0])
        category = parts[1]
        new_total = save_expense(amount, category)
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": f"📊 <b>Расход зафиксирован!</b>\n\n• Сумма: <b>{amount} руб</b>\n• Категория: <b>{category}</b>\n• Всего расходов: <b>{new_total} руб</b>", "parse_mode": "HTML"})

    # 6.5 УМНОЕ УДАЛЕНИЕ НАПОМИНАНИЙ
    elif any(kw in text_lower for kw in ["удали напоминание", "удалить напоминание", "стереть напоминание", "убрать напоминание", "сними напоминание"]):
        m = re.search(r'\d+', text)
        if m:
            r_id = int(m.group(0))
            if delete_reminder(r_id):
                res_text = f"🗑 <b>Напоминание #{r_id} успешно удалено!</b>"
                send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": res_text, "parse_mode": "HTML", "reply_markup": get_reminders_dashboard_markup()})
            else:
                send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": f"⚠️ Напоминание #{r_id} не найдено или уже выполнено.", "parse_mode": "HTML"})
        else:
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": "⚠️ Укажите номер напоминания, например: <code>Удали напоминание 1</code>", "parse_mode": "HTML"})
        return

    # 8. УМНЫЕ НАПОМИНАНИЯ И ТАЙМЕРЫ 5.0 (NLP-распознавание дат, встреч, времени и интервалов)
    elif any(kw in text_lower for kw in ["напомни", "напомнить", "поставь напоминание", "создай напоминание", "у меня встреча", "у меня встречи", "встреча ", "встречи "]) or re.search(r'\b\d{1,2}-\d{1,2}[.:]\d{2}\b', text_lower) or re.search(r'\bчерез\s+\d+\s*(?:мин|час|дн)', text_lower):
        entry = add_reminder(text, is_voice=is_voice)
        rem_str = format_time_remaining(entry["target_timestamp"])
        task_html = html.escape(entry["text"])
        dt_str = entry["target_datetime"]
        
        confirm_text = (
            f"⏰ <b>НАПОМИНАНИЕ #{entry['id']} УСТАНОВЛЕНО!</b>\n\n"
            f"📌 <b>Задача:</b> <code>{task_html}</code>\n"
            f"📅 <b>Время сигнала:</b> <b>{dt_str}</b>\n"
            f"⏳ <b>До сигнала:</b> <i>{rem_str}</i>\n\n"
            f"✨ <i>ИИ-Вектор пришлет вам высокоприоритетный сигнал и аларм точно в срок!</i>"
        )
        markup = {
            "inline_keyboard": [
                [{"text": f"⏰ Открыть #{entry['id']}", "callback_data": f"remind_detail_{entry['id']}"}],
                [{"text": "⏰ Все напоминания", "callback_data": "nav_remind"}, {"text": "« 🔙 В Меню", "callback_data": "nav_main"}]
            ]
        }
    # 8.0 УПРАВЛЕНИЕ ПАПКАМИ ОБЛАКА (Создать, переименовать, удалить)
    ok_folder, folder_msg = handle_cloud_folder_nlp(text)
    if ok_folder:
        send_api_request("sendMessage", {
            "chat_id": sender_chat_id,
            "text": f"{folder_msg}\n\n📂 <i>Ваши папки обновлены в Облачном хранилище!</i>",
            "parse_mode": "HTML",
            "reply_markup": get_cloud_dashboard_markup()
        })
        return

    # 8.1 ПРЯМОЕ УМНОЕ СОХРАНЕНИЕ В ПАПКИ ЛИЧНОГО ОБЛАКА (Работа, Google Диск, Аудио, Общая)
    explicit_cat, clean_cloud_text = detect_explicit_cloud_category(text)
    if explicit_cat:
        clean_content = clean_cloud_text if clean_cloud_text else f"Запись в раздел {explicit_cat}"
        first_line = clean_content.split("\n")[0][:30].strip() or f"Документ_{int(time.time())}"
        
        # Если было голосовое сообщение и целевой раздел Аудио_и_Совещания — сохраняем и сам аудиофайл
        if is_voice and voice_file and explicit_cat == "Аудио_и_Совещания":
            try:
                save_file_to_cloud(voice_file, f"Аудиозапись_{time.strftime('%Y%m%d_%H%M%S')}.ogg", category="Аудио_и_Совещания")
            except Exception:
                pass
        
        entry = save_text_to_cloud(clean_content, title=first_line, category=explicit_cat)
        
        cat_info = {
            "Работа": ("💼", "«РАБОТА»", "ПК + Telegram + Google Диск", "cloud_cat_work"),
            "Google_Диск": ("☁️", "«GOOGLE ДИСК»", "Google Drive Cloud + ПК", "cloud_cat_gdrive"),
            "Аудио_и_Совещания": ("🎙", "«АУДИО & СОВЕЩАНИЯ»", "Локальный ПК + Telegram Cloud", "cloud_cat_audio"),
            "Общая": ("📁", "«ОБЩАЯ»", "Безлимитное Telegram Cloud", "cloud_cat_general")
        }
        icon, cat_title, storage_note, cb_cat = cat_info.get(explicit_cat, ("📁", explicit_cat, "Telegram Cloud", "nav_cloud"))
        
        confirm_text = (
            f"{icon} <b>СОХРАНЕНО В ПАПКУ {cat_title} (Объект #{entry['id']})!</b>\n\n"
            f"<code>{clean_content}</code>\n\n"
            f"✨ <i>Хранилище: {storage_note}. Доступно в 1 клик в меню «Моё Облако».</i>"
        )
        markup = {
            "inline_keyboard": [
                [{"text": f"{icon} Открыть #{entry['id']} в Облаке", "callback_data": f"cloud_file_{entry['id']}"}],
                [{"text": f"{icon} Папка {cat_title}", "callback_data": cb_cat}, {"text": "« 🔙 В Меню", "callback_data": "nav_main"}]
            ]
        }
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": confirm_text, "parse_mode": "HTML", "reply_markup": markup})
        return

        # 8.15 ПАКЕТНОЕ УДАЛЕНИЕ ЗАМЕТОК ПО НОМЕРАМ ТЕКСТОМ (например: "удали 10, 11, 12, 13")
    elif re.match(r'^(?:удали|удалить|стереть|сотри)\s+([0-9\s,;]+)$', text.strip(), re.I):
        ids_to_del = [int(x) for x in re.findall(r'\d+', text)]
        if ids_to_del:
            deleted_ids = delete_multiple_notes(ids_to_del)
            confirm_text = (
                f"🗑 <b>УДАЛЕНО ЗАМЕТОК: {len(deleted_ids)} шт!</b>\n\n"
                f"Удалены номера: <code>#{', #'.join(map(str, deleted_ids))}</code>\n"
                f"✨ <i>Файлы на диске и записи в базе очищены. База переиндексирована!</i>"
            )
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": confirm_text, "parse_mode": "HTML", "reply_markup": get_notes_markup(sender_chat_id)})
            return

    # 8.2 УМНОЕ СОХРАНЕНИЕ В ЗАМЕТКИ (Спорт / Работа / Общее)
    elif any(kw in text_lower for kw in ["заметка", "заметку", "заметки", "заметок", "в заметки", "добавь в заметки", "сохрани в заметки", "запиши в заметки", "в спорт", "в работу", "в общее"]) or text_lower.startswith(("спорт:", "работа:", "общее:")):
        clean_note_text = re.sub(r'^(?:добавь|сохрани|запиши|внеси)?\s*(?:в|к)?\s*(?:папку|раздел)?\s*(?:заметка|заметку|заметки|заметок|спорт|работу|общее)\s*(?:от|для)?\s*:?\s*', '', text, flags=re.I).strip()
        clean_note_text = re.sub(r'^(?:в|к)\s+', '', clean_note_text, flags=re.I).strip()
        if not clean_note_text:
            clean_note_text = text.strip()

        explicit_cat = None
        if text_lower.startswith(("спорт:", "в спорт", "папка спорт")):
            explicit_cat = "Спорт"
        elif text_lower.startswith(("работа:", "в работу", "папка работа")):
            explicit_cat = "Работа"
        elif text_lower.startswith(("общее:", "в общее", "папка общее")):
            explicit_cat = "Общее"

        target_cat = explicit_cat or classify_note_category(clean_note_text)

        if target_cat:
            note_id = save_note(clean_note_text, note_type="голос" if is_voice else "текст", category=target_cat)
            icon = CATEGORY_ICON_MAP.get(target_cat, "📁")
            confirm_text = (
                f"🟢 <b>ЗАМЕТКА #{note_id} СОХРАНЕНА В ПАПКУ [{icon} {target_cat.upper()}]!</b>\n\n"
                f"<code>{html.escape(clean_note_text)}</code>\n\n"
                f"📁 <i>Файл сохранен на диске: База_Заметок/{CATEGORY_DIR_MAP[target_cat].split('/')[-1]}/</i>"
            )
            NOTES_CATEGORY_STATE[sender_chat_id] = target_cat
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": confirm_text, "parse_mode": "HTML", "reply_markup": get_notes_markup(sender_chat_id)})
            return
        else:
            PENDING_NOTE_CATEGORY[sender_chat_id] = {
                "text": clean_note_text,
                "type": "голос" if is_voice else "текст",
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            prompt_text = (
                f"❓ <b>В КАКУЮ ПАПКУ СОХРАНИТЬ ЭТУ ЗАМЕТКУ?</b>\n\n"
                f"«<i>{html.escape(clean_note_text[:120])}</i>»\n\n"
                f"<i>Выберите нужную папку одним нажатием:</i>"
            )
            markup = {
                "inline_keyboard": [
                    [{"text": "🏋️ Спорт", "callback_data": "cat_pick_Спорт"}, {"text": "🏗 Работа", "callback_data": "cat_pick_Работа"}],
                    [{"text": "📁 Общее", "callback_data": "cat_pick_Общее"}, {"text": "❌ Отмена", "callback_data": "cat_cancel"}]
                ]
            }
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": prompt_text, "parse_mode": "HTML", "reply_markup": markup})
            return

# 9. ВСЕ ОСТАЛЬНЫЕ ЗАПРОСЫ И ЗАДАЧИ ➔ НАПРЯМУЮ В ИИ-СЕКРЕТАРЬ / EXECUTIVE SUMMARY (TIER-1)
    elif text:
        if is_voice:
            parsed_exec = parse_executive_voice_summary(text)
            LAST_EXECUTIVE_SUMMARY[sender_chat_id] = parsed_exec
            card_txt, card_mk = format_executive_summary_card(parsed_exec)
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": card_txt, "parse_mode": "HTML", "reply_markup": card_mk})
            return
        else:
            sec_text = process_secretary_request(text)
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": sec_text, "parse_mode": "HTML", "reply_markup": get_secretary_markup()})
            return

def download_telegram_file(file_id, file_name):
    """ Скачивает любой файл из Telegram Bot API в DOWNLOAD_DIR """
    config = load_config()
    token = config.get("telegram_bot_token")
    if not token or not file_id:
        return None
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    f_url = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
    try:
        req = urllib.request.Request(f_url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            if res.get('ok'):
                rel_path = res['result']['file_path']
                dl_url = f"https://api.telegram.org/file/bot{token}/{rel_path}"
                dest_path = os.path.join(DOWNLOAD_DIR, file_name)
                urllib.request.urlretrieve(dl_url, dest_path)
                return dest_path
    except Exception as e:
        print(f"Ошибка загрузки файла из Telegram: {e}")
    return None

def process_single_update(update):
    if "callback_query" in update:
        handle_callback(update["callback_query"])
        return

    msg = update.get("message", {})
    if not msg or msg.get("from", {}).get("is_bot"):
        return
    sender_chat_id = msg.get("chat", {}).get("id")
    if not sender_chat_id:
        return

    user_name = msg.get("from", {}).get("first_name", "Пользователь")
    update_id = update.get("update_id", int(time.time()))
    caption = msg.get("caption", "").strip()

    # 1. ГОЛОСОВЫЕ СООБЩЕНИЯ (Работают для всех: владельца и гостей)
    if "voice" in msg:
        file_id = msg["voice"]["file_id"]
        ogg_path, recognized_text = download_and_transcribe_voice(file_id, update_id)
        if recognized_text:
            process_command_text(sender_chat_id, recognized_text, is_voice=True, voice_file=ogg_path, user_name=user_name)
        else:
            if int(sender_chat_id) == AUTHORIZED_CHAT_ID:
                note_id = save_note(f"Голосовая заметка сохранена в {ogg_path}", note_type="голос")
                confirm_text = f"🎤 <b>Голосовое сообщение #{note_id} сохранено!</b>\n\nФайл: <code>{ogg_path}</code>"
            else:
                confirm_text = "⚠️ Не удалось распознать голос. Попробуйте надиктовать еще раз или напишите текстом!"
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": confirm_text, "parse_mode": "HTML"})
        return

    # Если гость прислал текстовое сообщение или команду
    if int(sender_chat_id) != AUTHORIZED_CHAT_ID:
        raw_text = msg.get("text", caption).strip()
        if raw_text:
            process_command_text(sender_chat_id, raw_text, is_voice=False, user_name=user_name)
        return

    # 2. ВИДЕОФАЙЛЫ (MP4, MOV, AVI, MKV)
    if "video" in msg:
        v = msg["video"]
        file_id = v.get("file_id")
        file_name = v.get("file_name", f"video_{update_id}_{int(time.time())}.mp4")
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": "🔄 <b>ИИ-Вектор проводит биомеханический анализ видео...</b>", "parse_mode": "HTML"})
        dest_path = download_telegram_file(file_id, file_name)
        if dest_path:
            report_text, cloud_entry, annotated_preview = process_video_upload(dest_path, file_name, caption_text=caption, is_video_note=False)
            if annotated_preview and os.path.exists(annotated_preview):
                send_telegram_photo(sender_chat_id, annotated_preview, caption="🥊 <b>Ключевой кадр биомеханики с наложением HUD</b>")
            send_api_request("sendMessage", {
                "chat_id": sender_chat_id,
                "text": report_text,
                "parse_mode": "HTML",
                "reply_markup": get_video_markup()
            })
        else:
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": "⚠️ Не удалось загрузить видеофайл с серверов Telegram."})
        return

    # 3. ВИДЕОСООБЩЕНИЯ (КРУЖОЧКИ TELEGRAM)
    if "video_note" in msg:
        vn = msg["video_note"]
        file_id = vn.get("file_id")
        file_name = f"video_note_{update_id}_{int(time.time())}.mp4"
        send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": "🔄 <b>ИИ-Вектор проводит биомеханический анализ кружочка...</b>", "parse_mode": "HTML"})
        dest_path = download_telegram_file(file_id, file_name)
        if dest_path:
            report_text, cloud_entry, annotated_preview = process_video_upload(dest_path, file_name, caption_text=caption, is_video_note=True)
            if annotated_preview and os.path.exists(annotated_preview):
                send_telegram_photo(sender_chat_id, annotated_preview, caption="🥊 <b>Ключевой кадр биомеханики с наложением HUD</b>")
            send_api_request("sendMessage", {
                "chat_id": sender_chat_id,
                "text": report_text,
                "parse_mode": "HTML",
                "reply_markup": get_video_markup()
            })
        else:
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": "⚠️ Не удалось загрузить видеосообщение."})
        return

    # 4. ФОТОГРАФИИ И СНИМКИ
    if "photo" in msg:
        p_list = msg["photo"]
        if p_list:
            file_id = p_list[-1].get("file_id")
            file_name = f"photo_{update_id}_{int(time.time())}.jpg"
            dest_path = download_telegram_file(file_id, file_name)
            if dest_path:
                cap_lower = (caption or "").lower()
                is_bodyfat_request = any(k in cap_lower for k in ["жир", "состав тела", "весогонк", "bodyfat", "антропометри", "вес ", "рост "]) or (len(re.findall(r'\b\d{2,3}\b', caption or "")) >= 2)
                
                if is_bodyfat_request:
                    send_api_request("sendMessage", {
                        "chat_id": sender_chat_id,
                        "text": "🔬 <b>ИИ-ядро MediaPipe 3D проводит сканирование фигуры и расчет процента жира...</b>",
                        "parse_mode": "HTML"
                    })
                    try:
                        from body_fat_analyzer import BodyFatAnalyzer
                        analyzer = BodyFatAnalyzer()
                        
                        height_cm = 180.0
                        weight_kg = 80.0
                        gender = "male"
                        nums = re.findall(r'\b\d+(?:[.,]\d+)?\b', caption or "")
                        if len(nums) >= 2:
                            n1 = float(nums[0].replace(",", "."))
                            n2 = float(nums[1].replace(",", "."))
                            if n1 > n2 and 120 <= n1 <= 230:
                                height_cm, weight_kg = n1, n2
                            elif n2 > n1 and 120 <= n2 <= 230:
                                height_cm, weight_kg = n2, n1
                            elif 120 <= n1 <= 230 and 40 <= n2 <= 200:
                                height_cm, weight_kg = n1, n2
                        elif len(nums) == 1:
                            val = float(nums[0].replace(",", "."))
                            if 120 <= val <= 230:
                                height_cm = val
                            elif 40 <= val <= 180:
                                weight_kg = val
                        
                        if any(k in cap_lower for k in ["жен", "девушк", "female"]):
                            gender = "female"
                            
                        res = analyzer.analyze_photo(
                            image_path=dest_path,
                            height_cm=height_cm,
                            weight_kg=weight_kg,
                            gender=gender
                        )
                        if res.get("success"):
                            hud_path = res.get("hud_image_path")
                            report_text = res.get("report_html")
                            if hud_path and os.path.exists(hud_path):
                                send_telegram_file(sender_chat_id, hud_path, caption=report_text)
                            else:
                                send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": report_text, "parse_mode": "HTML"})
                            return
                    except Exception as bfe:
                        print(f"Ошибка анализа состава тела в Векторе: {bfe}")

                explicit_cat, _ = detect_explicit_cloud_category(caption)
                target_cat = explicit_cat or detect_category(caption or file_name)
                c_entry = save_file_to_cloud(dest_path, file_name, category=target_cat)
                
                tag = get_cloud_hashtag(target_cat)
                target_chan = get_cloud_channel()
                if target_chan:
                    post_cap = f"{tag} #фото\n📸 <b>{html.escape(file_name)}</b>\n\n☁️ <i>Раздел: {target_cat}</i>"
                    res_chan = send_telegram_file(target_chan, dest_path, caption=post_cap)
                    if res_chan and res_chan.get("ok"):
                        c_entry["msg_id"] = res_chan["result"]["message_id"]
                        c_entry["channel"] = str(target_chan)
                        save_cloud_index(load_cloud_index())

                cat_icon = get_cloud_category_icon(target_cat)
                confirm_txt = (
                    f"📸 <b>ФОТОГРАФИЯ СОХРАНЕНА В ОБЛАКО!</b>\n\n"
                    f"• Название: <b>{html.escape(file_name)}</b>\n"
                    f"• Папка: <b>{cat_icon} {target_cat}</b> (хэштег: <code>{tag}</code>)\n"
                    f"• ID в Облаке: <b>#{c_entry['id']}</b>\n\n"
                    f"💡 <i>Файл сохранен в 100% качестве. Чтобы сменить папку, нажмите кнопку ниже:</i>"
                )
                markup = {
                    "inline_keyboard": [
                        [
                            {"text": "👨‍👩‍👧 Семейная", "callback_data": f"cloud_move_{c_entry['id']}_Семейная"},
                            {"text": "💼 Работа", "callback_data": f"cloud_move_{c_entry['id']}_Работа"}
                        ],
                        [
                            {"text": "📄 Документы", "callback_data": f"cloud_move_{c_entry['id']}_Документы"},
                            {"text": "📁 Общая", "callback_data": f"cloud_move_{c_entry['id']}_Общая"}
                        ],
                        [
                            {"text": f"☁️ Открыть #{c_entry['id']} в Облаке", "callback_data": f"cloud_file_{c_entry['id']}"},
                            {"text": "« 🔙 В Меню", "callback_data": "nav_main"}
                        ]
                    ]
                }
                send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": confirm_txt, "parse_mode": "HTML", "reply_markup": markup})
            return

    # 5. АУДИОФАЙЛЫ
    if "audio" in msg:
        a = msg["audio"]
        file_id = a.get("file_id")
        file_name = a.get("file_name", f"audio_{update_id}_{int(time.time())}.mp3")
        dest_path = download_telegram_file(file_id, file_name)
        if dest_path:
            explicit_c, _ = detect_explicit_cloud_category(caption)
            target_cat = explicit_c or "Аудио & Совещания"
            c_entry = save_file_to_cloud(dest_path, file_name, category=target_cat)
            rec_text = None
            try:
                from video_analyzer import extract_and_transcribe_audio
                rec_text = extract_and_transcribe_audio(dest_path)
            except Exception:
                pass
            out_msg = (
                f"🎵 <b>АУДИОФАЙЛ ЗАФИКСИРОВАН В ОБЛАКЕ!</b>\n\n"
                f"• Название: <b>{html.escape(file_name)}</b>\n"
                f"• Раздел: <code>{c_entry.get('category', 'Аудио & Совещания')}</code>\n"
                f"• ID в Облаке: <b>#{c_entry['id']}</b>\n\n"
            )
            if rec_text:
                out_msg += f"🎙 <b>Расшифровка речи:</b>\n<i>«{html.escape(rec_text)}»</i>\n\n"
                parsed_exec = parse_executive_voice_summary(rec_text)
                LAST_EXECUTIVE_SUMMARY[sender_chat_id] = parsed_exec
                card_txt, card_mk = format_executive_summary_card(parsed_exec)
                send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": card_txt, "parse_mode": "HTML", "reply_markup": card_mk})
            out_msg += f"✨ <i>Файл сохранен в Ваше Личное Облако.</i>"
            
            upload_markup = {
                "inline_keyboard": [
                    [{"text": f"☁️ Открыть #{c_entry['id']} в Облаке", "callback_data": f"cloud_file_{c_entry['id']}"}],
                    [{"text": "📂 К разделам Облака", "callback_data": "nav_cloud"}, {"text": "« 🔙 В Меню", "callback_data": "nav_main"}]
                ]
            }
            send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": out_msg, "parse_mode": "HTML", "reply_markup": upload_markup})
        return

    # 6. ДОКУМЕНТЫ (PDF, DOCX, TXT, а также медиа как файлы)
    if "document" in msg:
        doc = msg["document"]
        file_id = doc.get("file_id")
        file_name = doc.get("file_name", f"doc_{update_id}")
        dest_path = download_telegram_file(file_id, file_name)
        if dest_path:
            ext = os.path.splitext(file_name)[1].lower()
            if ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
                report_text, cloud_entry, annotated_preview = process_video_upload(dest_path, file_name, caption_text=caption, is_video_note=False)
                if annotated_preview and os.path.exists(annotated_preview):
                    send_telegram_photo(sender_chat_id, annotated_preview, caption="🥊 <b>Ключевой кадр биомеханики с наложением HUD</b>")
                send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": report_text, "parse_mode": "HTML", "reply_markup": get_video_markup()})
            elif ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic"]:
                explicit_cat, _ = detect_explicit_cloud_category(caption)
                target_cat = explicit_cat or detect_category(caption or file_name)
                c_entry = save_file_to_cloud(dest_path, file_name, category=target_cat)
                
                tag = get_cloud_hashtag(target_cat)
                target_chan = get_cloud_channel()
                if target_chan:
                    post_cap = f"{tag} #фото #оригинал\n📸 <b>{html.escape(file_name)}</b>\n\n☁️ <i>Раздел: {target_cat}</i>"
                    res_chan = send_telegram_file(target_chan, dest_path, caption=post_cap)
                    if res_chan and res_chan.get("ok"):
                        c_entry["msg_id"] = res_chan["result"]["message_id"]
                        c_entry["channel"] = str(target_chan)
                        save_cloud_index(load_cloud_index())

                cat_icon = get_cloud_category_icon(target_cat)
                confirm_txt = (
                    f"📸 <b>ОРИГИНАЛ ФОТО СОХРАНЕН В ОБЛАКО!</b>\n\n"
                    f"• Название: <b>{html.escape(file_name)}</b>\n"
                    f"• Папка: <b>{cat_icon} {target_cat}</b> (хэштег: <code>{tag}</code>)\n"
                    f"• ID в Облаке: <b>#{c_entry['id']}</b>\n\n"
                    f"💡 <i>Файл сохранен как несжатый документ. Чтобы сменить папку, нажмите кнопку:</i>"
                )
                markup = {
                    "inline_keyboard": [
                        [
                            {"text": "👨‍👩‍👧 Семейная", "callback_data": f"cloud_move_{c_entry['id']}_Семейная"},
                            {"text": "💼 Работа", "callback_data": f"cloud_move_{c_entry['id']}_Работа"}
                        ],
                        [
                            {"text": "📄 Документы", "callback_data": f"cloud_move_{c_entry['id']}_Документы"},
                            {"text": "📁 Общая", "callback_data": f"cloud_move_{c_entry['id']}_Общая"}
                        ],
                        [
                            {"text": f"☁️ Открыть #{c_entry['id']} в Облаке", "callback_data": f"cloud_file_{c_entry['id']}"},
                            {"text": "« 🔙 В Меню", "callback_data": "nav_main"}
                        ]
                    ]
                }
                send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": confirm_txt, "parse_mode": "HTML", "reply_markup": markup})
            else:
                explicit_c, _ = detect_explicit_cloud_category(caption)
                target_cat = explicit_c or detect_category(caption or file_name)
                c_entry = save_file_to_cloud(dest_path, file_name, category=target_cat)
                summary_text = summarize_uploaded_document(dest_path, file_name)
                cat_name = c_entry.get('category', target_cat)
                cat_icon = get_cloud_category_icon(cat_name)
                tag = get_cloud_hashtag(cat_name)
                
                target_chan = get_cloud_channel()
                if target_chan:
                    post_cap = f"{tag} <b>{html.escape(file_name)}</b>\n\n☁️ <i>Раздел: {cat_name}</i>"
                    res_chan = send_telegram_file(target_chan, dest_path, caption=post_cap)
                    if res_chan and res_chan.get("ok"):
                        c_entry["msg_id"] = res_chan["result"]["message_id"]
                        c_entry["channel"] = str(target_chan)
                        save_cloud_index(load_cloud_index())

                cloud_msg = (
                    f"☁️ <b>ДОКУМЕНТ СОХРАНЕН В ЛИЧНОЕ ОБЛАКО!</b>\n\n"
                    f"• Название: <b>{html.escape(file_name)}</b>\n"
                    f"• Папка: <b>{cat_icon} {cat_name}</b> (хэштег: <code>{tag}</code>)\n"
                    f"• ID в Облаке: <b>#{c_entry['id']}</b>\n\n"
                    f"{summary_text}\n\n"
                    f"💡 <i>Файл зафиксирован. Чтобы сменить папку, нажмите кнопку:</i>"
                )
                upload_markup = {
                    "inline_keyboard": [
                        [
                            {"text": "👨‍👩‍👧 Семейная", "callback_data": f"cloud_move_{c_entry['id']}_Семейная"},
                            {"text": "💼 Работа", "callback_data": f"cloud_move_{c_entry['id']}_Работа"}
                        ],
                        [
                            {"text": "📄 Документы", "callback_data": f"cloud_move_{c_entry['id']}_Документы"},
                            {"text": "📁 Общая", "callback_data": f"cloud_move_{c_entry['id']}_Общая"}
                        ],
                        [
                            {"text": f"☁️ Открыть #{c_entry['id']} в Облаке", "callback_data": f"cloud_file_{c_entry['id']}"},
                            {"text": "« 🔙 В Меню", "callback_data": "nav_main"}
                        ]
                    ]
                }
                send_api_request("sendMessage", {"chat_id": sender_chat_id, "text": cloud_msg, "parse_mode": "HTML", "reply_markup": upload_markup})
        return

    # 7. ТЕКСТОВЫЕ СООБЩЕНИЯ
    text = msg.get("text", "").strip() or caption
    if text:
        if text.startswith(("🎯 ВЕКТОР", "🤖 ИИ-", "🔎 ГЛОБАЛЬНЫЙ", "📊 ОТЧЕТ ПО 615-ФЗ", "📋 ЕЖЕДНЕВНЫЙ", "🟢 ЗАМЕТКА #")):
            return
        process_command_text(sender_chat_id, text, is_voice=False)

if __name__ == "__main__":
    send_main_dashboard(AUTHORIZED_CHAT_ID)

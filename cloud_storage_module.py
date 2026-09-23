#!/usr/bin/env python3
"""
ИИ-ВЕКТОР: Модуль Приватного Облачного Хранилища 4.0 (Private Cloud Vault 4.0).
Обеспечивает 100% независимое личное облако на ПК + интеграция с Telegram и Google Диском:
- 💼 Работа (ПК + Telegram + Google Диск) — ООО «Компания Парадигма», 615-ФЗ, сметы, акты.
- 🎙 Аудио_и_Совещания (ПК + Telegram) — Аудиозаписи планерок, встреч и звонков.
- ☁️ Google_Диск — Зеркало облачных документов Google Drive.
- 📁 Общее (Telegram Cloud) — Универсальное безлимитное хранилище документов и файлов в Telegram.
- Постраничная навигация (пагинация), фильтрация по 4 целевым разделам.
- Отправка любого файла из облака в Telegram в 1 клик.
"""

import os
import sys
import json
import time
import shutil
import html
import math

CLOUD_BASE_DIR = os.path.expanduser("~/Документы/Облачное_Хранилище")
INDEX_FILE = os.path.join(CLOUD_BASE_DIR, "cloud_index.json")
GDRIVE_BASE_DIR = os.path.expanduser("~/GoogleDrive")
CLOUD_PAGE_SIZE = 5

# Хранилище состояний для каждого чата
CLOUD_PAGE_STATE = {}
CLOUD_CAT_STATE = {}

CATEGORIES_FILE = os.path.join(CLOUD_BASE_DIR, "cloud_categories.json")

def get_cloud_categories():
    candidate_paths = [
        CATEGORIES_FILE,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_categories.json"),
        os.path.join(os.path.dirname(__file__), "cloud_categories.json"),
        "/home/home/Документы/2/cloud_categories.json"
    ]
    for cp in candidate_paths:
        if os.path.exists(cp):
            try:
                with open(cp, "r", encoding="utf-8") as f:
                    cats = json.load(f)
                    if isinstance(cats, list) and cats:
                        return cats
            except Exception:
                pass
    return ["Семейная", "Шестьсот пятнадцать", "Все про бокс", "Документы", "Общее", "Разное", "General"]

def save_cloud_categories(cats):
    os.makedirs(CLOUD_BASE_DIR, exist_ok=True)
    with open(CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)

def add_cloud_category(name):
    name_clean = name.strip()
    if not name_clean:
        return False, "⚠️ Название папки не может быть пустым."
    cats = get_cloud_categories()
    if name_clean in cats:
        return False, f"⚠️ Папка «{name_clean}» уже существует."
    cats.append(name_clean)
    save_cloud_categories(cats)
    os.makedirs(os.path.join(CLOUD_BASE_DIR, name_clean), exist_ok=True)
    return True, f"✅ Папка «{name_clean}» успешно создана!"

def rename_cloud_category(old_name, new_name):
    cats = get_cloud_categories()
    old_clean = old_name.strip()
    new_clean = new_name.strip()
    matched = [c for c in cats if c.lower() == old_clean.lower()]
    if not matched:
        return False, f"⚠️ Папка «{old_name}» не найдена."
    real_old = matched[0]
    cats = [new_clean if c == real_old else c for c in cats]
    save_cloud_categories(cats)
    
    index = load_cloud_index()
    for e in index:
        if e.get("category") == real_old:
            e["category"] = new_clean
    save_cloud_index(index)
    
    old_dir = os.path.join(CLOUD_BASE_DIR, real_old)
    new_dir = os.path.join(CLOUD_BASE_DIR, new_clean)
    if os.path.exists(old_dir):
        try:
            os.rename(old_dir, new_dir)
        except Exception:
            pass
    return True, f"✅ Папка «{real_old}» успешно переименована в «{new_clean}»!"

def delete_cloud_category(name):
    cats = get_cloud_categories()
    name_clean = name.strip()
    matched = [c for c in cats if c.lower() == name_clean.lower()]
    if not matched:
        return False, f"⚠️ Папка «{name}» не найдена."
    real_name = matched[0]
    if len(cats) <= 1:
        return False, "⚠️ Нельзя удалить последнюю оставшуюся папку."
    cats = [c for c in cats if c != real_name]
    save_cloud_categories(cats)
    
    fallback_cat = "Разное" if "Разное" in cats else cats[0]
    index = load_cloud_index()
    for e in index:
        if e.get("category") == real_name:
            e["category"] = fallback_cat
    save_cloud_index(index)
    return True, f"🗑 Папка «{real_name}» удалена (файлы сохранены в «{fallback_cat}»)."

def init_cloud():
    for d in get_cloud_categories():
        os.makedirs(os.path.join(CLOUD_BASE_DIR, d), exist_ok=True)
    if not os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def load_cloud_index():
    candidate_paths = [
        INDEX_FILE,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_index.json"),
        os.path.join(os.path.dirname(__file__), "cloud_index.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "Работа", "cloud_index.json"),
        "/home/home/Документы/2/cloud_index.json",
        "/home/home/Документы/Облачное_Хранилище/cloud_index.json"
    ]
    for cp in candidate_paths:
        if os.path.exists(cp):
            try:
                with open(cp, "r", encoding="utf-8") as f:
                    index = json.load(f)
                    if isinstance(index, list) and len(index) > 0:
                        for idx, entry in enumerate(index, start=1):
                            if "id" not in entry:
                                entry["id"] = idx
                        return index
            except Exception:
                pass
    return []

def save_cloud_index(index_data):
    init_cloud()
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(INDEX_FILE, 0o600)
    except Exception:
        pass

def detect_category(file_name, default_category="Разное"):
    name_lower = file_name.lower()
    ext = os.path.splitext(file_name)[1].lower()
    
    # 1. Шестьсот пятнадцать (615-ФЗ, Котово, сметы, акты, стройка)
    if any(kw in name_lower for kw in ["615", "шестьсот", "парадигм", "котово", "михайловк", "лавров", "дубовк", "смета", "кс-2", "кс-3", "технадзор", "работ", "договор", "объект", "дефект", "акт", "орлов", "распоряжен", "капремонт"]):
        return "Шестьсот пятнадцать"
    
    # 2. Семейная (фотографии, альбомы, семейные снимки)
    elif ext in [".jpg", ".jpeg", ".png", ".heic", ".webp", ".bmp", ".gif", ".raw", ".dng"] or any(kw in name_lower for kw in ["img_", "dsc_", "photo", "фото", "семья", "семейн", "ирина", "роман", "дети", "отпуск", "дом", "родные"]):
        return "Семейная"
    
    # 3. Все про бокс (бокс, тренировки, спарринги, UFC, спорт)
    elif any(kw in name_lower for kw in ["бокс", "спорт", "тренир", "спарринг", "ufc", "перчатк", "лап", "офп", "сфп", "метод", "раунд"]):
        return "Все про бокс"
    
    # 4. Официальные документы
    elif ext in [".pdf", ".docx", ".doc", ".xlsx", ".xls"] and any(kw in name_lower for kw in ["паспорт", "снилс", "инн", "выписка", "свидетельст", "устав", "лицензия", "справка", "полис", "реквизит"]):
        return "Документы"
    
    # 5. Аудио и Совещания
    elif ext in [".mp3", ".m4a", ".ogg", ".wav", ".aac", ".flac", ".wma"] or any(kw in name_lower for kw in ["совещан", "голос", "планерк", "audio"]):
        return "Шестьсот пятнадцать" if "615" in name_lower else "Разное"
        
    return default_category

def detect_explicit_cloud_category(text):
    if not text:
        return None, text
    import re
    t_lower = text.lower()
    
    # 1. Семейная / Семья / Фото
    if any(kw in t_lower for kw in ["в семейная", "в семейную", "в семейное", "в семью", "папка семейная", "папка семья", "папку семья", "папку семейная", "сохрани в семейная", "сохрани в семейную", "сохрани в семью", "в облаке папка семейная", "в облако семейная", "в фото", "папка фото", "#семья", "#семейная", "#фото"]):
        clean = re.sub(r'^(?:добавь|сохрани|сохранить|запиши|внеси|перенеси)?\s*(?:в\s+облаке\s+папка|в\s+облако\s+папка|в\s+облаке|в\s+облако|в|к|по)?\s*(?:папку|папка|раздел)?\s*(?:семейная|семейную|семейное|семья|семью|фото|фотографии)\s*(?:от|для)?\s*:?\s*', '', text, flags=re.I).strip()
        clean = re.sub(r'#(?:семья|семейная|фото|семейное)', '', clean, flags=re.I).strip()
        return "Семейная", clean

    # 2. Шестьсот пятнадцать (615-ФЗ)
    if any(kw in t_lower for kw in ["в шестьсот пятнадцать", "в шестьсот 15", "в 615", "по 615", "папка 615", "папку 615", "папка шестьсот пятнадцать", "сохрани в 615", "сохрани в шестьсот", "в работу", "по работе", "папка работа", "папку работа", "сохрани в работу", "#615", "#615фз", "#парадигма", "#работа"]):
        clean = re.sub(r'^(?:добавь|сохрани|сохранить|запиши|внеси|перенеси)?\s*(?:в\s+облаке\s+папка|в\s+облако\s+папка|в\s+облаке|в\s+облако|в|к|по)?\s*(?:папку|папка|раздел)?\s*(?:шестьсот\s+пятнадцать|шестьсот|615|615-фз|615фз|работа|работу|работе)\s*(?:от|для)?\s*:?\s*', '', text, flags=re.I).strip()
        clean = re.sub(r'#(?:615|615фз|парадигма|работа)', '', clean, flags=re.I).strip()
        return "Шестьсот пятнадцать", clean

    # 3. Все про бокс
    if any(kw in t_lower for kw in ["во все про бокс", "в бокс", "про бокс", "папка бокс", "папку бокс", "в спорт", "папка спорт", "сохрани в бокс", "сохрани в спорт", "#бокс", "#спорт"]):
        clean = re.sub(r'^(?:добавь|сохрани|сохранить|запиши|внеси|перенеси)?\s*(?:в\s+облаке\s+папка|в\s+облако\s+папка|в\s+облаке|в\s+облако|в|к|по)?\s*(?:папку|папка|раздел)?\s*(?:все\s+про\s+бокс|бокс|боксу|спорт|спорту)\s*(?:от|для)?\s*:?\s*', '', text, flags=re.I).strip()
        clean = re.sub(r'#(?:бокс|спорт)', '', clean, flags=re.I).strip()
        return "Все про бокс", clean

    # 4. Документы
    if any(kw in t_lower for kw in ["в документы", "в доки", "папка документы", "папку документы", "сохрани в документы", "#документы", "#паспорт"]):
        clean = re.sub(r'^(?:добавь|сохрани|сохранить|запиши|внеси)?\s*(?:в\s+облаке\s+папка|в\s+облако\s+папка|в\s+облаке|в\s+облако|в|к)?\s*(?:папку|папка|раздел)?\s*(?:документы|документ|доки)\s*(?:от|для)?\s*:?\s*', '', text, flags=re.I).strip()
        clean = re.sub(r'#(?:документы|документ|паспорт)', '', clean, flags=re.I).strip()
        return "Документы", clean

    # 5. Общее
    if any(kw in t_lower for kw in ["в общее", "в общую", "папка общее", "папка общая", "папку общее", "сохрани в общее", "#общее"]):
        clean = re.sub(r'^(?:добавь|сохрани|сохранить|запиши|внеси)?\s*(?:в\s+облаке\s+папка|в\s+облако\s+папка|в\s+облаке|в\s+облако|в|к)?\s*(?:папку|папка|раздел)?\s*(?:общее|общая|общую)\s*(?:от|для)?\s*:?\s*', '', text, flags=re.I).strip()
        clean = re.sub(r'#общее', '', clean, flags=re.I).strip()
        return "Общее", clean

    # 6. Разное
    if any(kw in t_lower for kw in ["в разное", "в разный", "папка разное", "папку разное", "сохрани в разное", "#разное"]):
        clean = re.sub(r'^(?:добавь|сохрани|сохранить|запиши|внеси)?\s*(?:в\s+облаке\s+папка|в\s+облако\s+папка|в\s+облаке|в\s+облако|в|к)?\s*(?:папку|папка|раздел)?\s*(?:разное|разный|разные)\s*(?:от|для)?\s*:?\s*', '', text, flags=re.I).strip()
        clean = re.sub(r'#разное', '', clean, flags=re.I).strip()
        return "Разное", clean

    # 7. General / Дженерал
    if any(kw in t_lower for kw in ["в дженерал", "в general", "папка general", "папка дженерал", "в главную", "#general"]):
        clean = re.sub(r'^(?:добавь|сохрани|сохранить|запиши|внеси)?\s*(?:в\s+облаке\s+папка|в\s+облако\s+папка|в\s+облаке|в\s+облако|в|к)?\s*(?:папку|папка|раздел)?\s*(?:general|дженерал|главная|главную)\s*(?:от|для)?\s*:?\s*', '', text, flags=re.I).strip()
        clean = re.sub(r'#general', '', clean, flags=re.I).strip()
        return "General", clean

    return None, text

    return None, text

def move_cloud_file_category(file_id, new_category):
    index = load_cloud_index()
    for e in index:
        if e.get("id") == file_id:
            e["category"] = new_category
            save_cloud_index(index)
            return True, f"✅ Файл #{file_id} перемещен в папку «{new_category}»!"
    return False, "⚠️ Файл не найден в базе."

def save_file_to_cloud(src_path, original_name, category=None, tg_message_id=None, tg_channel_id=None):
    init_cloud()
    index = load_cloud_index()
    
    if not category:
        category = detect_category(original_name)
    
    cat_dir = os.path.join(CLOUD_BASE_DIR, category)
    os.makedirs(cat_dir, exist_ok=True)
    
    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp_str}_{original_name}"
    dest_path = os.path.join(cat_dir, safe_name)
    
    file_size = 0
    if os.path.exists(src_path):
        try:
            shutil.copy2(src_path, dest_path)
            file_size = os.path.getsize(dest_path)
        except Exception:
            file_size = os.path.getsize(src_path) if os.path.exists(src_path) else 0

    # Если категория Работа — также синхронизируем в Google Drive
    if category == "Работа" and os.path.exists(src_path):
        try:
            gdrive_work = os.path.join(GDRIVE_BASE_DIR, "Работа")
            os.makedirs(gdrive_work, exist_ok=True)
            shutil.copy2(src_path, os.path.join(gdrive_work, original_name))
        except Exception:
            pass

    new_id = max([e.get("id", 0) for e in index] + [0]) + 1
    entry = {
        "id": new_id,
        "original_name": original_name,
        "saved_name": safe_name,
        "path": dest_path,
        "category": category,
        "size_bytes": file_size,
        "date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    if tg_message_id:
        entry["tg_message_id"] = tg_message_id
    if tg_channel_id:
        entry["tg_channel_id"] = tg_channel_id

    index.append(entry)
    save_cloud_index(index)
    return entry

def save_text_to_cloud(text_content, title="Документ", category="Общая"):
    init_cloud()
    index = load_cloud_index()
    
    cat_dir = os.path.join(CLOUD_BASE_DIR, category)
    os.makedirs(cat_dir, exist_ok=True)

    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    file_name = f"{timestamp_str}_{title[:20]}.txt"
    dest_path = os.path.join(cat_dir, file_name)

    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(text_content)

    # Синхронизация в Google Drive если Работа или Google_Диск
    if category in ["Работа", "Google_Диск"]:
        try:
            sub = "Работа" if category == "Работа" else ""
            gdir = os.path.join(GDRIVE_BASE_DIR, sub) if sub else GDRIVE_BASE_DIR
            os.makedirs(gdir, exist_ok=True)
            with open(os.path.join(gdir, f"{title}.txt"), "w", encoding="utf-8") as f:
                f.write(text_content)
        except Exception:
            pass

    new_id = max([e.get("id", 0) for e in index] + [0]) + 1
    entry = {
        "id": new_id,
        "original_name": f"{title}.txt",
        "saved_name": file_name,
        "path": dest_path,
        "category": category,
        "size_bytes": len(text_content.encode("utf-8")),
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "preview": text_content[:150]
    }
    index.append(entry)
    save_cloud_index(index)
    return entry

def get_cloud_file_by_id(file_id):
    index = load_cloud_index()
    for e in index:
        if e.get("id") == file_id:
            return e
    return None

def delete_file_from_cloud(file_id):
    index = load_cloud_index()
    target = None
    new_index = []
    for e in index:
        if e.get("id") == file_id:
            target = e
        else:
            new_index.append(e)
    
    if target:
        if os.path.exists(target.get("path", "")):
            try:
                os.remove(target["path"])
            except Exception:
                pass
        save_cloud_index(new_index)
        return True
    return False

def get_filtered_cloud_files(category_filter=None):
    index = load_cloud_index()
    if not category_filter or category_filter == "all":
        return index
    
    def norm(s):
        return str(s).lower().replace("_", " ").replace("&", "и").replace("  ", " ").strip()

    cf_norm = norm(category_filter)
    res = []
    for e in index:
        cat_norm = norm(e.get("category", ""))
        orig_lower = e.get("original_name", "").lower()

        # 1. Семейная
        if cf_norm in ["семейная", "семья", "фото", "семейное", "family", "семейные"] and ("семейн" in cat_norm or "семь" in cat_norm or "фото" in cat_norm or orig_lower.endswith((".jpg", ".jpeg", ".png", ".heic", ".webp"))):
            res.append(e)
        # 2. Шестьсот пятнадцать
        elif cf_norm in ["шестьсот пятнадцать", "615", "шестьсот", "работа", "work"] and ("шестьсот" in cat_norm or "615" in cat_norm or "работ" in cat_norm or "парадигм" in orig_lower):
            res.append(e)
        # 3. Все про бокс
        elif cf_norm in ["все про бокс", "бокс", "спорт", "тренировки"] and ("бокс" in cat_norm or "спорт" in cat_norm or any(kw in orig_lower for kw in ["бокс", "ufc", "спорт", "boxing"])):
            res.append(e)
        # 4. Документы
        elif cf_norm in ["документы", "доки", "docs", "documents"] and ("документ" in cat_norm or "док" in cat_norm):
            res.append(e)
        # 5. Общее
        elif cf_norm in ["общее", "общая", "общие"] and ("общ" in cat_norm):
            res.append(e)
        # 6. Разное
        elif cf_norm in ["разное", "разный", "разные", "misc"] and ("разн" in cat_norm or "google" in cat_norm or "диск" in cat_norm or "медиа" in cat_norm):
            res.append(e)
        # 7. General
        elif cf_norm in ["general", "дженерал", "главная"] and ("general" in cat_norm or "дженерал" in cat_norm):
            res.append(e)
        elif cf_norm == cat_norm or cf_norm in cat_norm or cat_norm in cf_norm:
            res.append(e)
    return res

def format_file_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} Б"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} КБ"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} МБ"

def get_cloud_category_icon(category):
    c = str(category).lower()
    if "семейн" in c or "семь" in c or "фото" in c: return "👨‍👩‍👧"
    if "шестьсот" in c or "615" in c or "работ" in c: return "🏗"
    if "бокс" in c or "спорт" in c: return "🥊"
    if "документ" in c or "док" in c: return "📄"
    if "общее" in c or "общая" in c: return "📁"
    if "разное" in c or "разн" in c: return "📦"
    if "general" in c or "дженерал" in c: return "🌐"
    return "📁"

def get_cloud_dashboard_text():
    index = load_cloud_index()
    total_bytes = sum(e.get("size_bytes", 0) for e in index)
    total_mb = total_bytes / (1024 * 1024)
    cats = get_cloud_categories()

    lines = [
        "☁️ <b>ЛИЧНОЕ ОБЛАЧНОЕ ХРАНИЛИЩЕ</b>\n",
        f"📊 <b>Каталог файлов ({len(index)} объектов • {total_mb:.2f} МБ):</b>"
    ]
    for cat in cats:
        icon = get_cloud_category_icon(cat)
        cat_files = get_filtered_cloud_files(cat)
        lines.append(f" • {icon} <b>{cat}:</b> {len(cat_files)} файлов")
        
    lines.append("\n📂 <i>Выберите раздел для просмотра или используйте кнопки ниже для управления папками:</i>")
    return "\n".join(lines)

def get_cloud_dashboard_markup():
    cats = get_cloud_categories()
    rows = []
    btn_row = []
    for cat in cats:
        icon = get_cloud_category_icon(cat)
        btn_row.append({"text": f"{icon} {cat}", "callback_data": f"cloud_cat_{cat}"})
        if len(btn_row) == 2:
            rows.append(btn_row)
            btn_row = []
    if btn_row:
        rows.append(btn_row)

    rows.append([
        {"text": "➕ Создать папку", "callback_data": "cloud_folder_add_prompt"},
        {"text": "⚙️ Управление папками", "callback_data": "cloud_folder_manage"}
    ])
    rows.append([{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}])
    return {"inline_keyboard": rows}

def get_cloud_manage_folders_text():
    cats = get_cloud_categories()
    lines = [
        "⚙️ <b>УПРАВЛЕНИЕ ПАПКАМИ ОБЛАКА</b>\n",
        "Здесь вы можете удалить ненужную папку или изменить её название:\n"
    ]
    for idx, c in enumerate(cats, start=1):
        icon = get_cloud_category_icon(c)
        lines.append(f"<b>#{idx}. {icon} {c}</b>")
    
    lines.append("\n💬 <i>Также можно надиктовать голосом:</i>")
    lines.append("• <code>Создай папку Личное</code>")
    lines.append("• <code>Переименуй папку Работа в 615</code>")
    lines.append("• <code>Удали папку Старое</code>")
    return "\n".join(lines)

def get_cloud_manage_folders_markup():
    cats = get_cloud_categories()
    rows = []
    for c in cats:
        icon = get_cloud_category_icon(c)
        rows.append([
            {"text": f"✏️ {c}", "callback_data": f"cf_ren_{c}"},
            {"text": f"🗑 Удалить", "callback_data": f"cf_del_{c}"}
        ])
    rows.append([{"text": "➕ Добавить новую папку", "callback_data": "cloud_folder_add_prompt"}])
    rows.append([{"text": "« 🔙 В Облако", "callback_data": "nav_cloud"}])
    return {"inline_keyboard": rows}

def get_cloud_list_text(chat_id, category="all"):
    files = get_filtered_cloud_files(category)
    total_items = len(files)
    total_pages = max(1, math.ceil(total_items / CLOUD_PAGE_SIZE)) if total_items > 0 else 1
    curr_page = max(1, min(CLOUD_PAGE_STATE.get(chat_id, 1), total_pages))
    CLOUD_PAGE_STATE[chat_id] = curr_page
    CLOUD_CAT_STATE[chat_id] = category

    start_idx = (curr_page - 1) * CLOUD_PAGE_SIZE
    page_files = files[start_idx : start_idx + CLOUD_PAGE_SIZE]

    cat_titles = {
        "all": "ВСЕ ФАЙЛЫ",
        "семейная": "СЕМЕЙНАЯ",
        "шестьсот пятнадцать": "ШЕСТЬСОТ ПЯТНАДЦАТЬ (615)",
        "все про бокс": "ВСЕ ПРО БОКС",
        "документы": "ДОКУМЕНТЫ",
        "общее": "ОБЩЕЕ",
        "разное": "РАЗНОЕ",
        "general": "GENERAL"
    }
    cat_title = cat_titles.get(category.lower(), category.upper())

    text = f"☁️ <b>ОБЛАКО: {cat_title}</b> (Лист <b>{curr_page} из {total_pages}</b> • Файлов: <b>{total_items}</b>):\n\n"

    if not files:
        text += "<i>В этом разделе пока нет сохраненных файлов.</i>\n\n"
    else:
        for f in page_files:
            icon = get_cloud_category_icon(f.get("category", ""))
            name = html.escape(f.get("original_name", "Файл"))
            size_str = format_file_size(f.get("size_bytes", 0))
            date_str = f.get("date", "")[:16]
            cat_name = f.get("category", "")
            text += f"{icon} <b>#{f['id']}. {name}</b>\n   • Размер: <code>{size_str}</code> | {date_str}\n   • Ветка: <i>{cat_name}</i>\n\n"

    if total_pages > 1:
        text += f"📄 <i>Страница {curr_page} из {total_pages}</i>"

    return text

def get_cloud_list_markup(chat_id, category="all"):
    files = get_filtered_cloud_files(category)
    total_items = len(files)
    total_pages = max(1, math.ceil(total_items / CLOUD_PAGE_SIZE)) if total_items > 0 else 1
    curr_page = max(1, min(CLOUD_PAGE_STATE.get(chat_id, 1), total_pages))

    start_idx = (curr_page - 1) * CLOUD_PAGE_SIZE
    page_files = files[start_idx : start_idx + CLOUD_PAGE_SIZE]

    rows = []
    # Кнопки для каждого файла
    for f in page_files:
        icon = get_cloud_category_icon(f.get("category", ""))
        fname = f.get("original_name", "Файл")
        short_name = fname[:24] + "..." if len(fname) > 27 else fname
        rows.append([{"text": f"{icon} #{f['id']} {short_name}", "callback_data": f"cloud_file_{f['id']}"}])

    # Навигационные кнопки пагинации
    nav_row = []
    if curr_page > 1:
        nav_row.append({"text": "⬅️ Назад", "callback_data": f"cloud_page_{curr_page-1}"})
    if curr_page < total_pages:
        nav_row.append({"text": "Вперед ➡️", "callback_data": f"cloud_page_{curr_page+1}"})
    if nav_row:
        rows.append(nav_row)

    # Кнопки возврата
    rows.append([
        {"text": "📂 Все папки", "callback_data": "nav_cloud"},
        {"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}
    ])
    return {"inline_keyboard": rows}

CHANNEL_CONFIG_FILE = os.path.join(CLOUD_BASE_DIR, "cloud_channel.json")

def get_cloud_channel():
    if os.path.exists(CHANNEL_CONFIG_FILE):
        try:
            with open(CHANNEL_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("channel")
        except Exception:
            pass
    return None

def set_cloud_channel(channel_identifier):
    os.makedirs(CLOUD_BASE_DIR, exist_ok=True)
    clean_chan = channel_identifier.strip()
    with open(CHANNEL_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"channel": clean_chan, "updated": time.strftime("%Y-%m-%d %H:%M:%S")}, f, ensure_ascii=False, indent=2)
    return True, f"✅ Канал «{clean_chan}» успешно привязан к Облачному хранилищу!"

def get_cloud_hashtag(category):
    c = str(category).lower()
    if "семейн" in c or "семь" in c or "фото" in c: return "#семья #фото"
    if "шестьсот" in c or "615" in c or "работ" in c or "парадигм" in c: return "#615фз #работа"
    if "бокс" in c or "спорт" in c: return "#бокс #спорт"
    if "документ" in c or "паспорт" in c: return "#документы"
    if "общее" in c or "общая" in c: return "#общее"
    if "разное" in c or "разн" in c: return "#разное"
    if "general" in c or "дженерал" in c: return "#general"
    return "#облако"

def get_cloud_file_detail_text(file_id):
    f = get_cloud_file_by_id(file_id)
    if not f:
        return "⚠️ <b>Файл не найден в базе Облака.</b>"
    
    icon = get_cloud_category_icon(f.get("category", ""))
    name = html.escape(f.get("original_name", "Файл"))
    size_str = format_file_size(f.get("size_bytes", 0))
    date_str = f.get("date", "")
    cat_name = f.get("category", "")
    tag = get_cloud_hashtag(cat_name)
    path = f.get("path", "")
    exists_str = "✅ Доступен" if os.path.exists(path) else "☁️ В Telegram Cloud"
    chan = get_cloud_channel()
    chan_str = f"<code>{chan}</code>" if chan else "<i>не привязан</i>"

    text = (
        f"{icon} <b>УПРАВЛЕНИЕ ФАЙЛОМ #{f['id']}</b>\n\n"
        f"• Название: <b>{name}</b>\n"
        f"• Раздел: <code>{cat_name}</code> (хэштег: <b>{tag}</b>)\n"
        f"• Размер: <b>{size_str}</b>\n"
        f"• Дата добавления: <i>{date_str}</i>\n"
        f"• Статус: {exists_str}\n"
        f"• Привязанный канал: {chan_str}\n\n"
        f"💡 <i>Выберите действие ниже: получить файл в чат или отправить прямо в ваш Telegram-канал c хэштегом!</i>"
    )
    return text

def get_cloud_file_detail_markup(file_id):
    f = get_cloud_file_by_id(file_id)
    return {
        "inline_keyboard": [
            [{"text": "📥 Отправить мне в Telegram", "callback_data": f"cloud_send_{file_id}"}],
            [{"text": "📂 Сменить папку", "callback_data": f"cloud_move_pick_{file_id}"}, {"text": "📢 В Telegram-канал", "callback_data": f"cloud_chan_{file_id}"}],
            [{"text": "🗑 Удалить из Облака", "callback_data": f"cloud_del_{file_id}"}],
            [{"text": "« 🔙 К списку файлов", "callback_data": "cloud_cat_current"}, {"text": "☁️ В меню Облака", "callback_data": "nav_cloud"}],
            [{"text": "🎛 В Главное Меню", "callback_data": "nav_main"}]
        ]
    }

def get_cloud_move_markup(file_id):
    cats = get_cloud_categories()
    rows = []
    btn_row = []
    for c in cats:
        icon = get_cloud_category_icon(c)
        btn_row.append({"text": f"{icon} {c}", "callback_data": f"cloud_move_{file_id}_{c}"})
        if len(btn_row) == 2:
            rows.append(btn_row)
            btn_row = []
    if btn_row:
        rows.append(btn_row)
    rows.append([{"text": "« 🔙 Отмена", "callback_data": f"cloud_file_{file_id}"}])
    return {"inline_keyboard": rows}

def handle_cloud_folder_nlp(text):
    if not text:
        return False, None
    import re
    t_clean = text.strip()
    t_lower = t_clean.lower()
    
    # 0. Привязать канал
    m_chan = re.search(r'^(?:привяжи|установи|канал)\s+(?:для\s+облака\s+|хранилища\s+)?(@[\w\d_]+|-\d+)', t_clean, re.I)
    if m_chan:
        ch_val = m_chan.group(1).strip()
        ok, msg = set_cloud_channel(ch_val)
        return True, msg

    # 1. Создать папку
    m_create = re.search(r'^(?:создай|добавь|создать|новая)\s+папк[уаи]\s+(?:в\s+облаке\s+)?(.+)', t_clean, re.I)
    if m_create:
        f_name = m_create.group(1).strip()
        ok, msg = add_cloud_category(f_name)
        return True, msg
        
    # 2. Переименовать папку
    m_ren = re.search(r'^(?:переименуй|измени|назови)\s+папку\s+(.+?)\s+(?:в|на)\s+(.+)', t_clean, re.I)
    if m_ren:
        old_n = m_ren.group(1).strip()
        new_n = m_ren.group(2).strip()
        ok, msg = rename_cloud_category(old_n, new_n)
        return True, msg
        
    # 3. Удалить папку
    m_del = re.search(r'^(?:удали|удалить|стереть)\s+папку\s+(.+)', t_clean, re.I)
    if m_del:
        f_name = m_del.group(1).strip()
        ok, msg = delete_cloud_category(f_name)
        return True, msg
        
    return False, None

if __name__ == "__main__":
    init_cloud()
    print(get_cloud_dashboard_text())

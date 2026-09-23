#!/usr/bin/env python3
"""
ИИ-ВЕКТОР: Модуль Базы Заметок 5.0 (Notes Engine 5.0).
Комплексный автономный модуль для управления персональной базой знаний и заметок:
- Трехуровневая классификация (1_Спорт 🏋️, 2_Работа 🏗, 3_Общее 📁).
- Двусторонняя синхронизация с Markdown-файлами базы знаний.
- Автоматическая расстановка тегов, извлечение метаданных и полнотекстовый поиск.
- Атомарное сохранение с резервным копированием (notes.json и data_backup/notes.json).
- Пакетные операции (выборка, слияние, удаление, перемещение).
- Интеграция с Telegram UI (генераторы текста карточек и Inline-разметки).
- CLI-интерфейс командной строки для локального терминального управления.
"""

import os
import sys
import json
import time
import datetime
import re
import html
import shutil
import math
import argparse

# Пути к файлам и директориям
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
NOTES_PATH = os.path.join(PROJECT_ROOT, "notes.json")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "data_backup")
BACKUP_NOTES_PATH = os.path.join(BACKUP_DIR, "notes.json")
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
    "нокаут", "тейп", "бинт", "капа", "скакалк", "trx", "медбол", "эспандер", "кросс",
    "отжимания", "подтягивания", "турник", "брусья", "борьба", "мма", "мма", "тренировк"
]

WORK_KEYWORDS = [
    "работ", "стройк", "объект", "смет", "615", "акт", "подрядчик", "совещан", "договор",
    "котово", "михайловка", "парадигм", "инженер", "прораб", "дгх", "фонд", "кс-2", "кс-3",
    "теплотрасс", "водоканал", "концесси", "откос", "щебень", "брак", "субподрядчик",
    "44-фз", "223-фз", "заказчик", "гнб", "производственн", "труб", "сварк", "монтаж",
    "проект", "капремонт", "мкд", "экспертиз", "технадзор", "чертеж", "ведомост"
]

GENERAL_KEYWORDS = [
    "купить", "покупк", "магазин", "аптек", "напомни", "напоминание", "пароль", "семья",
    "дом", "личн", "идея", "мысль", "чек", "расход", "паспорт", "заметка", "книга",
    "фильм", "контакт", "телефон", "адрес", "поездка", "билет", "машина", "авто"
]

# Кэш в памяти
_NOTES_CACHE = None
_NOTES_CACHE_MTIME = 0

def init_notes_storage():
    """Инициализирует директории и файлы базы заметок при первом запуске."""
    os.makedirs(NOTES_DIR_BASE, exist_ok=True)
    for path in CATEGORY_DIR_MAP.values():
        os.makedirs(path, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    if not os.path.exists(NOTES_PATH):
        # Если есть бэкап - восстанавливаем из бэкапа
        if os.path.exists(BACKUP_NOTES_PATH):
            try:
                shutil.copy2(BACKUP_NOTES_PATH, NOTES_PATH)
            except Exception:
                with open(NOTES_PATH, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
        else:
            with open(NOTES_PATH, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        try:
            os.chmod(NOTES_PATH, 0o600)
        except Exception:
            pass

def invalidate_notes_cache():
    """Сбрасывает кэш заметок в памяти."""
    global _NOTES_CACHE, _NOTES_CACHE_MTIME
    _NOTES_CACHE = None
    _NOTES_CACHE_MTIME = 0

def extract_tags_from_text(text):
    """Извлекает хэштеги (#тег) из текста заметки."""
    if not text:
        return []
    tags = re.findall(r'#([A-Za-zА-Яа-я0-9_\-]+)', text)
    return sorted(list(set(t.lower() for t in tags)))

def classify_note_category(text, old_category=""):
    """
    Интеллектуальный классификатор категории заметки (Спорт / Работа / Общее).
    Опирается на семантические словари и явные маркеры.
    """
    if not text:
        return old_category or "Общее"
        
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
    return old_category or "Общее"

def load_notes():
    """Загружает список всех заметок с валидацией и нормализацией категорий."""
    global _NOTES_CACHE, _NOTES_CACHE_MTIME
    init_notes_storage()
    if not os.path.exists(NOTES_PATH):
        _NOTES_CACHE = []
        return []
    try:
        mtime = os.path.getmtime(NOTES_PATH)
        if _NOTES_CACHE is not None and mtime == _NOTES_CACHE_MTIME:
            return [dict(n) for n in _NOTES_CACHE]
        
        with open(NOTES_PATH, "r", encoding="utf-8") as f:
            notes = json.load(f)
            
        modified = False
        for idx, n in enumerate(notes, start=1):
            if "id" not in n:
                n["id"] = idx
                modified = True
            if "category" not in n or n["category"] not in ["Спорт", "Работа", "Общее"]:
                n["category"] = classify_note_category(n.get("text", ""))
                modified = True
            if "tags" not in n:
                n["tags"] = extract_tags_from_text(n.get("text", ""))
                modified = True
                
        _NOTES_CACHE = notes
        _NOTES_CACHE_MTIME = mtime
        
        if modified:
            save_notes(notes, sync_md=False)
            
        return [dict(n) for n in notes]
    except Exception as e:
        # Попытка восстановить из бэкапа при сбое чтения
        if os.path.exists(BACKUP_NOTES_PATH):
            try:
                with open(BACKUP_NOTES_PATH, "r", encoding="utf-8") as bf:
                    return json.load(bf)
            except Exception:
                pass
        return _NOTES_CACHE or []

def save_notes(notes_list, sync_md=False):
    """
    Атомарно сохраняет список заметок в JSON с автоматическим бэкапом.
    """
    init_notes_storage()
    temp_path = f"{NOTES_PATH}.tmp.{os.getpid()}"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(notes_list, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, NOTES_PATH)
        try:
            os.chmod(NOTES_PATH, 0o600)
        except Exception:
            pass
    except Exception as e:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise e

    # Резервная копия
    try:
        with open(BACKUP_NOTES_PATH, "w", encoding="utf-8") as bf:
            json.dump(notes_list, bf, ensure_ascii=False, indent=2)
        try:
            os.chmod(BACKUP_NOTES_PATH, 0o600)
        except Exception:
            pass
    except Exception:
        pass

    invalidate_notes_cache()

    if sync_md:
        for n in notes_list:
            sync_note_markdown_file(n)

def reindex_notes(notes):
    """Переиндексирует ID всех заметок от 1 до N."""
    for idx, n in enumerate(notes, start=1):
        n["id"] = idx
    return notes

def sync_note_markdown_file(note):
    """Синхронизирует отдельную заметку в Markdown-файл в соответствующей папке."""
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

    tags_line = ""
    tags = note.get("tags") or extract_tags_from_text(raw_text)
    if tags:
        tags_line = f"• **Теги:** " + ", ".join([f"#{t}" for t in tags]) + "\n"

    md_content = (
        f"# ЗАМЕТКА #{n_id} [{cat.upper()}]\n\n"
        f"• **Категория:** {cat}\n"
        f"• **Дата создания:** {note.get('time', '')}\n"
        f"• **Тип ввода:** {note.get('type', 'текст')}\n"
        f"{tags_line}\n"
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
    """Удаляет файл Markdown заметки со всех директорий категорий."""
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

def add_note(note_text, note_type="текст", category=None, tags=None):
    """
    Добавляет новую заметку в базу с автоклассификацией и сохранением в Markdown.
    """
    invalidate_notes_cache()
    notes = load_notes()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    if not category:
        category = classify_note_category(note_text) or "Общее"

    extracted_tags = extract_tags_from_text(note_text)
    if tags:
        if isinstance(tags, str):
            tags = [t.strip().lstrip("#") for t in tags.split(",") if t.strip()]
        all_tags = sorted(list(set(extracted_tags + [t.lower() for t in tags])))
    else:
        all_tags = extracted_tags

    new_id = len(notes) + 1
    new_note = {
        "id": new_id,
        "time": timestamp,
        "date": timestamp,
        "text": note_text.strip(),
        "type": note_type,
        "category": category,
        "tags": all_tags
    }
    
    notes.append(new_note)
    reindex_notes(notes)
    
    # Синхронизация созданной заметки
    for n in notes:
        if n["id"] == len(notes):
            sync_note_markdown_file(n)
            
    save_notes(notes)
    return new_note

# Совместимость с сигнатурой векторного бота
save_note = add_note

def get_note_by_id(note_id):
    """Возвращает заметку по числовому ID или None."""
    notes = load_notes()
    for n in notes:
        if n.get("id") == int(note_id):
            return dict(n)
    return None

def append_text_to_note(note_id, extra_text):
    """Дописывает дополнительный пункт или текст в существующую заметку."""
    invalidate_notes_cache()
    notes = load_notes()
    updated = False
    target_note = None
    note_id = int(note_id)
    
    for n in notes:
        if n.get("id") == note_id:
            old_txt = n.get("text", "").strip()
            bullet = extra_text.strip()
            if not bullet.startswith("•") and not bullet.startswith("-"):
                bullet = f"• {bullet}"
            n["text"] = f"{old_txt}\n{bullet}"
            n["tags"] = extract_tags_from_text(n["text"])
            sync_note_markdown_file(n)
            updated = True
            target_note = n
            break
            
    if updated:
        save_notes(notes)
    return updated, target_note

def replace_note_text(note_id, new_text):
    """Полностью заменяет текст заметки."""
    invalidate_notes_cache()
    notes = load_notes()
    updated = False
    target_note = None
    note_id = int(note_id)
    
    for n in notes:
        if n.get("id") == note_id:
            n["text"] = new_text.strip()
            n["tags"] = extract_tags_from_text(new_text)
            sync_note_markdown_file(n)
            updated = True
            target_note = n
            break
            
    if updated:
        save_notes(notes)
    return updated, target_note

def move_note_category(note_id, new_category):
    """Перемещает заметку в другую папку/категорию (Спорт, Работа, Общее)."""
    if new_category not in CATEGORY_DIR_MAP:
        return None
    invalidate_notes_cache()
    notes = load_notes()
    target_note = None
    note_id = int(note_id)
    
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
        save_notes(notes)
    return target_note

def delete_single_note(note_id):
    """Удаляет одну заметку и переиндексирует оставшиеся."""
    invalidate_notes_cache()
    notes = load_notes()
    note_id = int(note_id)
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
        save_notes(new_notes)
    return deleted

delete_note = delete_single_note

def delete_multiple_notes(note_ids):
    """Пакетно удаляет несколько заметок по их ID."""
    invalidate_notes_cache()
    notes = load_notes()
    ids_to_del = set(int(x) for x in note_ids)
    
    for n in notes:
        if n.get("id") in ids_to_del:
            delete_note_markdown_file(n)
            
    deleted_ids = [n["id"] for n in notes if n.get("id") in ids_to_del]
    new_notes = [n for n in notes if n.get("id") not in ids_to_del]
    
    reindex_notes(new_notes)
    for n in new_notes:
        sync_note_markdown_file(n)
        
    save_notes(new_notes)
    return deleted_ids

def merge_notes(note_ids, new_category=None):
    """Объединяет несколько заметок в одну единую заметку."""
    invalidate_notes_cache()
    notes = load_notes()
    ids_set = set(int(x) for x in note_ids)
    target_notes = [n for n in notes if n.get("id") in ids_set]
    
    if len(target_notes) < 2:
        return False, "Для объединения укажите хотя бы 2 существующие заметки."

    combined_text = "\n\n".join([f"📝 [Заметка #{n['id']} | {n.get('time', '')}]:\n{n['text']}" for n in target_notes])
    first_id = target_notes[0]["id"]
    chosen_category = new_category or target_notes[0].get("category", "Общее")
    
    for n in notes:
        if n["id"] == first_id:
            n["text"] = combined_text
            n["category"] = chosen_category
            n["time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            n["tags"] = extract_tags_from_text(combined_text)
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

    save_notes(remaining_notes)
    return True, f"Заметки {note_ids} успешно объединены в заметку #{first_id} [{chosen_category}]."

def search_notes(query, category=None, tag=None):
    """
    Полнотекстовый поиск заметок с фильтрацией по категории и тегам.
    Возвращает список подходящих заметок с оценкой релевантности.
    """
    notes = load_notes()
    q_clean = (query or "").lower().strip()
    tag_clean = (tag or "").lower().strip().lstrip("#")
    results = []

    for n in notes:
        if category and n.get("category") != category:
            continue
            
        note_tags = [t.lower() for t in n.get("tags", [])]
        if tag_clean and tag_clean not in note_tags:
            continue
            
        text = n.get("text", "")
        text_lower = text.lower()
        
        score = 0
        if q_clean:
            if q_clean in text_lower:
                score += 10
            # Поиск по отдельным словам
            words = [w for w in q_clean.split() if len(w) > 2]
            for w in words:
                if w in text_lower:
                    score += 2
            if score == 0:
                continue
        else:
            score = 1
            
        results.append({
            "note": n,
            "score": score
        })
        
    results.sort(key=lambda x: (x["score"], x["note"]["id"]), reverse=True)
    return [r["note"] for r in results]

def sync_all_markdown_files():
    """Синхронизирует всю базу notes.json со структурой каталогов База_Заметок."""
    notes = load_notes()
    init_notes_storage()
    synced_count = 0
    for n in notes:
        sync_note_markdown_file(n)
        synced_count += 1
    save_notes(notes, sync_md=False)
    return synced_count

def get_notes_stats():
    """Возвращает аналитическую статистику базы заметок."""
    notes = load_notes()
    cnt_sport = sum(1 for n in notes if n.get("category") == "Спорт")
    cnt_work = sum(1 for n in notes if n.get("category") == "Работа")
    cnt_gen = sum(1 for n in notes if n.get("category") not in ["Спорт", "Работа"])
    
    tags_freq = {}
    for n in notes:
        for t in n.get("tags", []):
            tags_freq[t] = tags_freq.get(t, 0) + 1
            
    top_tags = sorted(tags_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total": len(notes),
        "sport": cnt_sport,
        "work": cnt_work,
        "general": cnt_gen,
        "top_tags": top_tags,
        "last_note": notes[-1] if notes else None
    }

# ==========================================
# TELEGRAM UI И РАЗМЕТКА КАРТОЧЕК
# ==========================================

def get_notes_dashboard_text(chat_id=None, cat_state="overview", is_bulk=False, selected_ids=None, page=1, page_size=5):
    """Генерирует форматированный HTML-текст для Telegram карточки заметок."""
    notes = load_notes()
    selected_ids = selected_ids or set()
    
    cnt_sport = sum(1 for n in notes if n.get("category") == "Спорт")
    cnt_work = sum(1 for n in notes if n.get("category") == "Работа")
    cnt_gen = sum(1 for n in notes if n.get("category") not in ["Спорт", "Работа"])
    total_notes = len(notes)

    if cat_state == "overview":
        return (
            "🗂 <b>БАЗА ЗАМЕТОК И БАЗА ЗНАНИЙ (3 НАПРАВЛЕНИЯ)</b>\n\n"
            f"Всего заметок в хранилище: <b>{total_notes}</b>\n\n"
            f"🏋️ <b>Спорт</b>: {cnt_sport} заметок (комплексы, бокс, фармакология, методики)\n"
            f"🏗 <b>Работа</b>: {cnt_work} заметок (объекты 615-ФЗ, сметы, подрядчики, акты)\n"
            f"📁 <b>Общее</b>: {cnt_gen} заметок (покупки, личное, пароли, напоминания)\n\n"
            "💡 <i>Отправьте любой текст или голосовое боту — я сохраню и автоклассифицирую его в нужную категорию.</i>"
        )

    cat_name = cat_state
    icon = CATEGORY_ICON_MAP.get(cat_name, "📁")
    cat_notes = [n for n in notes if n.get("category") == cat_name or (cat_name == "Общее" and n.get("category") not in ["Спорт", "Работа"])]
    
    total_items = len(cat_notes)
    total_pages = max(1, math.ceil(total_items / page_size)) if total_items > 0 else 1
    curr_page = max(1, min(page, total_pages))

    start_idx = (curr_page - 1) * page_size
    page_notes = cat_notes[start_idx : start_idx + page_size]

    header_mode = " [РЕЖИМ МАССОВОГО ВЫБОРА]" if is_bulk else ""
    text_lines = [
        f"{icon} <b>ПАПКА «{cat_name.upper()}»</b> (Всего: {total_items}){header_mode}\n"
        f"📄 <i>Страница {curr_page} из {total_pages}</i>\n"
    ]

    if not page_notes:
        text_lines.append("<i>В этой папке пока нет заметок.</i>")
    else:
        for n in page_notes:
            n_id = n["id"]
            preview = n.get("text", "").strip()
            first_line = preview.split("\n")[0][:60]
            if len(preview.split("\n")[0]) > 60:
                first_line += "..."
                
            n_time = n.get("time", "")[:10]
            is_sel = n_id in selected_ids
            marker = "🔴 [ВЫБРАНА] " if is_sel else ""
            
            text_lines.append(f"<b>#{n_id}</b> {marker}• <i>{html.escape(first_line)}</i> (📅 {n_time})")

    if is_bulk:
        text_lines.append(f"\nВыбрано для действия: <b>{len(selected_ids)}</b> шт.")
    else:
        text_lines.append("\n<i>Нажмите на номер заметки ниже, чтобы открыть и отредактировать:</i>")

    return "\n".join(text_lines)

def get_notes_dashboard_markup(chat_id=None, cat_state="overview", is_bulk=False, selected_ids=None, page=1, page_size=5):
    """Генерирует Inline-клавиатуру для навигации по заметкам."""
    notes = load_notes()
    selected_ids = selected_ids or set()
    
    cnt_sport = sum(1 for n in notes if n.get("category") == "Спорт")
    cnt_work = sum(1 for n in notes if n.get("category") == "Работа")
    cnt_gen = sum(1 for n in notes if n.get("category") not in ["Спорт", "Работа"])

    if cat_state == "overview":
        return {
            "inline_keyboard": [
                [
                    {"text": f"🏋️ Спорт ({cnt_sport})", "callback_data": "notes_cat_Спорт"},
                    {"text": f"🏗 Работа ({cnt_work})", "callback_data": "notes_cat_Работа"}
                ],
                [
                    {"text": f"📁 Общее ({cnt_gen})", "callback_data": "notes_cat_Общее"}
                ],
                [
                    {"text": "« 🔙 В Меню", "callback_data": "nav_main"}
                ]
            ]
        }

    cat_name = cat_state
    cat_notes = [n for n in notes if n.get("category") == cat_name or (cat_name == "Общее" and n.get("category") not in ["Спорт", "Работа"])]
    
    total_items = len(cat_notes)
    total_pages = max(1, math.ceil(total_items / page_size)) if total_items > 0 else 1
    curr_page = max(1, min(page, total_pages))

    start_idx = (curr_page - 1) * page_size
    page_notes = cat_notes[start_idx : start_idx + page_size]

    rows = []

    if is_bulk:
        if page_notes:
            sel_buttons = []
            for n in page_notes:
                is_sel = n["id"] in selected_ids
                b_text = f"🔴 ☑️ #{n['id']}" if is_sel else f"⬜️ #{n['id']}"
                sel_buttons.append({"text": b_text, "callback_data": f"note_sel_toggle_{n['id']}"})
                if len(sel_buttons) == 3:
                    rows.append(sel_buttons)
                    sel_buttons = []
            if sel_buttons:
                rows.append(sel_buttons)

        if total_pages > 1:
            rows.append([
                {"text": "◀️ Пред", "callback_data": "note_page_prev"},
                {"text": f"📄 {curr_page}/{total_pages}", "callback_data": "note_page_noop"},
                {"text": "След ▶️", "callback_data": "note_page_next"}
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
        if page_notes:
            note_buttons = []
            for n in page_notes:
                note_buttons.append({"text": f"📝 #{n['id']}", "callback_data": f"note_detail_{n['id']}"})
                if len(note_buttons) == 3:
                    rows.append(note_buttons)
                    note_buttons = []
            if note_buttons:
                rows.append(note_buttons)

        if total_pages > 1:
            rows.append([
                {"text": "◀️ Назад", "callback_data": "note_page_prev"},
                {"text": f"📄 {curr_page} / {total_pages}", "callback_data": "note_page_noop"},
                {"text": "Вперед ▶️", "callback_data": "note_page_next"}
            ])

        rows.append([
            {"text": "🗑 Выбрать и удалить несколько", "callback_data": "note_bulk_mode_on"}
        ])

        rows.append([
            {"text": "📂 « Назад к Папкам", "callback_data": "notes_back_to_folders"},
            {"text": "« 🔙 Главное Меню", "callback_data": "nav_main"}
        ])

    return {"inline_keyboard": rows}

def get_note_detail_text(note_id):
    """Возвращает детальный HTML-текст отдельной заметки."""
    note = get_note_by_id(note_id)
    if not note:
        return "❌ <b>Заметка не найдена.</b>"
        
    n_id = note["id"]
    cat = note.get("category", "Общее")
    icon = CATEGORY_ICON_MAP.get(cat, "📁")
    created = note.get("time", "")
    n_type = note.get("type", "текст")
    raw_text = note.get("text", "")
    tags = note.get("tags") or extract_tags_from_text(raw_text)
    tags_str = ("\n🏷 <b>Теги:</b> " + ", ".join([f"#{t}" for t in tags])) if tags else ""

    return (
        f"{icon} <b>ЗАМЕТКА #{n_id}</b> [{cat}]\n"
        f"📅 <b>Дата:</b> {created} | <b>Тип:</b> {n_type}{tags_str}\n"
        f"────────────────────\n\n"
        f"{html.escape(raw_text)}\n\n"
        f"────────────────────"
    )

def get_note_detail_markup(note_id):
    """Возвращает клавиатуру действий для карточки заметки."""
    note = get_note_by_id(note_id)
    if not note:
        return {"inline_keyboard": [[{"text": "« Назад", "callback_data": "notes_back_to_folders"}]]}
        
    n_id = note["id"]
    cat = note.get("category", "Общее")

    return {
        "inline_keyboard": [
            [
                {"text": "📁 Сменить папку", "callback_data": f"note_move_prompt_{n_id}"},
                {"text": "📋 Скопировать текст", "callback_data": f"note_send_raw_{n_id}"}
            ],
            [
                {"text": "➕ Дописать в заметку", "callback_data": f"note_append_hint_{n_id}"},
                {"text": "🗑 Удалить эту заметку", "callback_data": f"note_delete_{n_id}"}
            ],
            [
                {"text": f"« 🔙 В папку [{cat}]", "callback_data": f"notes_cat_{cat}"},
                {"text": "🎛 В Главное Меню", "callback_data": "nav_main"}
            ]
        ]
    }

# ==========================================
# CLI ИНТЕРФЕЙС
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="ИИ-Вектор: Модуль Базы Заметок 5.0")
    subparsers = parser.add_subparsers(dest="command", help="Команды модуля")

    # list
    p_list = subparsers.add_parser("list", help="Вывести список заметок")
    p_list.add_argument("--category", "-c", choices=["Спорт", "Работа", "Общее"], help="Фильтр по категории")
    p_list.add_argument("--tag", "-t", help="Фильтр по тегу")

    # show / get
    p_get = subparsers.add_parser("get", help="Показать детальную заметку по ID")
    p_get.add_argument("id", type=int, help="ID заметки")

    # add
    p_add = subparsers.add_parser("add", help="Создать новую заметку")
    p_add.add_argument("text", type=str, help="Текст заметки")
    p_add.add_argument("--category", "-c", choices=["Спорт", "Работа", "Общее"], help="Категория")
    p_add.add_argument("--type", default="текст", help="Тип ввода (текст, голос, фото)")

    # append
    p_app = subparsers.add_parser("append", help="Дописать текст в существующую заметку")
    p_app.add_argument("id", type=int, help="ID заметки")
    p_app.add_argument("text", type=str, help="Дополнительный текст")

    # search
    p_search = subparsers.add_parser("search", help="Поиск по заметкам")
    p_search.add_argument("query", type=str, help="Поисковый запрос")
    p_search.add_argument("--category", "-c", help="Категория")

    # delete
    p_del = subparsers.add_parser("delete", help="Удалить заметку")
    p_del.add_argument("id", type=int, nargs="+", help="ID заметки или нескольких заметок")

    # merge
    p_merge = subparsers.add_parser("merge", help="Объединить заметки")
    p_merge.add_argument("ids", type=int, nargs="+", help="Список ID для объединения")

    # sync
    p_sync = subparsers.add_parser("sync", help="Синхронизировать все заметки с Markdown-файлами")

    # stats
    p_stats = subparsers.add_parser("stats", help="Статистика базы заметок")

    args = parser.parse_args()

    if not args.command or args.command == "list":
        notes = load_notes()
        cat = getattr(args, "category", None)
        tag = getattr(args, "tag", None)
        if cat:
            notes = [n for n in notes if n.get("category") == cat]
        if tag:
            tag_clean = tag.lower().lstrip("#")
            notes = [n for n in notes if tag_clean in [t.lower() for t in n.get("tags", [])]]
            
        print(f"=== БАЗА ЗАМЕТОК ({len(notes)} шт.) ===")
        for n in notes:
            icon = CATEGORY_ICON_MAP.get(n.get("category"), "📁")
            first_line = n["text"].split("\n")[0][:70]
            print(f"#{n['id']:03d} [{icon} {n.get('category', 'Общее'):<6}] ({n.get('time', '')[:10]}): {first_line}")

    elif args.command == "get":
        n = get_note_by_id(args.id)
        if not n:
            print(f"❌ Заметка #{args.id} не найдена.")
            sys.exit(1)
        icon = CATEGORY_ICON_MAP.get(n.get("category"), "📁")
        print(f"=== {icon} ЗАМЕТКА #{n['id']} [{n.get('category')}] ===")
        print(f"Дата: {n.get('time', '')} | Тип: {n.get('type', 'текст')}")
        if n.get("tags"):
            print(f"Теги: {', '.join(['#' + t for t in n['tags']])}")
        print("-" * 50)
        print(n.get("text", ""))
        print("-" * 50)
        if n.get("file_path"):
            print(f"Файл: {n['file_path']}")

    elif args.command == "add":
        new_note = add_note(args.text, note_type=args.type, category=args.category)
        print(f"✅ Создана заметка #{new_note['id']} [{new_note['category']}]:")
        print(new_note['text'])

    elif args.command == "append":
        ok, n = append_text_to_note(args.id, args.text)
        if ok:
            print(f"✅ Заметка #{args.id} успешно дополнена.")
        else:
            print(f"❌ Заметка #{args.id} не найдена.")

    elif args.command == "search":
        results = search_notes(args.query, category=args.category)
        print(f"=== РЕЗУЛЬТАТЫ ПОИСКА «{args.query}» ({len(results)} шт.) ===")
        for n in results:
            icon = CATEGORY_ICON_MAP.get(n.get("category"), "📁")
            first_line = n["text"].split("\n")[0][:70]
            print(f"#{n['id']:03d} [{icon} {n.get('category', 'Общее')}] ({n.get('time', '')[:10]}): {first_line}")

    elif args.command == "delete":
        if len(args.id) == 1:
            if delete_single_note(args.id[0]):
                print(f"✅ Заметка #{args.id[0]} успешно удалена.")
            else:
                print(f"❌ Заметка #{args.id[0]} не найдена.")
        else:
            del_ids = delete_multiple_notes(args.id)
            print(f"✅ Удалены заметки: {del_ids}")

    elif args.command == "merge":
        ok, msg = merge_notes(args.ids)
        print(msg)

    elif args.command == "sync":
        cnt = sync_all_markdown_files()
        print(f"✅ Успешно синхронизировано {cnt} заметок в каталоге База_Заметок.")

    elif args.command == "stats":
        st = get_notes_stats()
        print("=== СТАТИСТИКА БАЗЫ ЗАМЕТОК ===")
        print(f"Всего заметок: {st['total']}")
        print(f"🏋️ Спорт:     {st['sport']}")
        print(f"🏗 Работа:    {st['work']}")
        print(f"📁 Общее:     {st['general']}")
        if st['top_tags']:
            print("Топ тегов:")
            for tag, count in st['top_tags']:
                print(f"  #{tag}: {count}")

if __name__ == "__main__":
    main()

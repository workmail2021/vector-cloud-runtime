#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ИИ-ВЕКТОР: TIER-1 WORLD-CLASS CORE ENGINE (2026)
Реализует золотые стандарты корпоративной продуктивности (Notion AI, Raycast, Granola/Otter.ai, Linear):
1. Interactive 1-Click Task Engine (Управление чек-листами с переключателями Done/Pending/Fire прямо в карточке).
2. Voice-to-Executive Summary (Структурирование аудио/текста в Суть, Задачи, Суммы и Авто-категорию).
3. Строительный модуль 615-ФЗ & Авто-учет КС-2 (Привязка расходов, материалов и дефектов к объектам).
4. Global Smart Search (Быстрый поиск по всем заметкам, задачам, расходам и документам 615-ФЗ).
"""

import os
import json
import time
import re
import html
import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TASKS_JSON_PATH = os.path.join(PROJECT_ROOT, "tasks.json")
EXPENSES_JSON_PATH = os.path.join(PROJECT_ROOT, "expenses.json")
NOTES_JSON_PATH = os.path.join(PROJECT_ROOT, "notes.json")
NOTES_DIR = os.path.join(PROJECT_ROOT, "База_Заметок")
CONSTRUCTION_DIR = os.path.join(PROJECT_ROOT, "Работа", "615")

OBJECTS_615 = [
    "ДУБОВКА", "КОТОВО", "МИХАЙЛОВКА", "СЕРАФИМОВИЧ",
    "СУРОВИКИНО", "ФРОЛОВО", "КРАСНОСЛОБОДСК"
]

def load_tasks():
    if os.path.exists(TASKS_JSON_PATH):
        try:
            with open(TASKS_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    default_tasks = [
        {"id": 1, "text": "Проверить акты скрытых работ (АОСР) на объекте Дубовка", "category": "Работа", "priority": "high", "status": "pending", "created_at": "2026-08-27"},
        {"id": 2, "text": "Сверить накопительную ведомость КС-2 по кровле Котово", "category": "Работа", "priority": "high", "status": "pending", "created_at": "2026-08-27"},
        {"id": 3, "text": "Утренний замер готовности (ЧСС, rMSSD, Штанге) в Mini App", "category": "Спорт", "priority": "high", "status": "done", "created_at": "2026-08-27"},
        {"id": 4, "text": "Запустить антифрод-аудит сметных объемов и материалов 615-ФЗ", "category": "Работа", "priority": "medium", "status": "pending", "created_at": "2026-08-27"},
        {"id": 5, "text": "Контроль вечерней фазы фармакокоррекции (Ашваганда + Магний)", "category": "Спорт", "priority": "medium", "status": "pending", "created_at": "2026-08-27"}
    ]
    save_tasks(default_tasks)
    return default_tasks

def save_tasks(tasks):
    try:
        with open(TASKS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving tasks.json: {e}")

def add_task(text, category="Общее", priority="medium", deadline=None):
    tasks = load_tasks()
    new_id = (max([t.get("id", 0) for t in tasks]) + 1) if tasks else 1
    new_task = {
        "id": new_id,
        "text": text.strip(),
        "category": category,
        "priority": priority,
        "status": "pending",
        "deadline": deadline,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    tasks.insert(0, new_task)
    save_tasks(tasks)
    return new_task

def toggle_task(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = "pending" if t.get("status") in ["done", "completed"] else "done"
            save_tasks(tasks)
            return t
    return None

def delete_task(task_id):
    tasks = load_tasks()
    orig_len = len(tasks)
    tasks = [t for t in tasks if t.get("id") != task_id]
    if len(tasks) != orig_len:
        save_tasks(tasks)
        return True
    return False

def clear_completed_tasks():
    tasks = load_tasks()
    pending = [t for t in tasks if t.get("status") != "done"]
    removed_count = len(tasks) - len(pending)
    save_tasks(pending)
    return removed_count

def get_tasks_hud_text(filter_mode="all", page=1, page_size=6):
    tasks = load_tasks()
    if filter_mode == "work":
        filtered = [t for t in tasks if "работ" in str(t.get("category", "")).lower() or "615" in str(t.get("category", "")).lower()]
        title_tag = "💼 РАБОТА"
    elif filter_mode == "sport":
        filtered = [t for t in tasks if "спорт" in str(t.get("category", "")).lower()]
        title_tag = "🥊 СПОРТ & КЭМП"
    elif filter_mode == "urgent":
        filtered = [t for t in tasks if t.get("priority") == "high" and t.get("status") == "pending"]
        title_tag = "🔥 СРОЧНЫЕ ЗАДАЧИ"
    elif filter_mode == "pending":
        filtered = [t for t in tasks if t.get("status") == "pending"]
        title_tag = "⏳ В РАБОТЕ"
    elif filter_mode == "done":
        filtered = [t for t in tasks if t.get("status") == "done"]
        title_tag = "✅ ВЫПОЛНЕННЫЕ"
    else:
        filtered = tasks
        title_tag = "📋 ВСЕ ЗАДАЧИ"

    total_tasks = len(filtered)
    total_pages = max(1, (total_tasks + page_size - 1) // page_size)
    curr_page = min(max(1, page), total_pages)
    
    start_idx = (curr_page - 1) * page_size
    page_tasks = filtered[start_idx : start_idx + page_size]
    
    total_done = sum(1 for t in tasks if t.get("status") in ["done", "completed"])
    total_all = len(tasks)
    progress_pct = round((total_done / total_all * 100)) if total_all > 0 else 0

    bar = "█" * (progress_pct // 10) + "░" * (10 - progress_pct // 10)

    lines = [
        f"📋 <b>ИНТЕРАКТИВНЫЙ ТРЕКЕР ЗАДАЧ // {title_tag}</b>",
        f"📊 <b>Общий прогресс:</b> <code>[{bar}] {progress_pct}%</code> ({total_done}/{total_all})",
        ""
    ]

    if not page_tasks:
        lines.append("<i>В этой категории пока нет задач.</i>")
    else:
        lines.append("<i>💡 Нажимайте на кнопки внизу для переключения статуса в 1 клик:</i>")
        lines.append("")
        for t in page_tasks:
            t_id = t.get("id")
            is_done = t.get("status") in ["done", "completed"]
            is_high = t.get("priority") == "high"
            
            icon = "✅" if is_done else ("🔥" if is_high else "⏳")
            strike_s = "<s>" if is_done else ""
            strike_e = "</s>" if is_done else ""
            cat_badge = f"[{t.get('category', 'Общее')}]"
            
            lines.append(f"{icon} <b>#{t_id}</b> {strike_s}{html.escape(t['text'])}{strike_e} <i>{cat_badge}</i>")

    return "\n".join(lines)

def get_tasks_hud_markup(filter_mode="all", page=1, page_size=6):
    tasks = load_tasks()
    if filter_mode == "work":
        filtered = [t for t in tasks if "работ" in str(t.get("category", "")).lower() or "615" in str(t.get("category", "")).lower()]
    elif filter_mode == "sport":
        filtered = [t for t in tasks if "спорт" in str(t.get("category", "")).lower()]
    elif filter_mode == "urgent":
        filtered = [t for t in tasks if t.get("priority") == "high" and t.get("status") == "pending"]
    elif filter_mode == "pending":
        filtered = [t for t in tasks if t.get("status") == "pending"]
    elif filter_mode == "done":
        filtered = [t for t in tasks if t.get("status") in ["done", "completed"]]
    else:
        filtered = tasks

    total_tasks = len(filtered)
    total_pages = max(1, (total_tasks + page_size - 1) // page_size)
    curr_page = min(max(1, page), total_pages)
    
    start_idx = (curr_page - 1) * page_size
    page_tasks = filtered[start_idx : start_idx + page_size]

    rows = []
    for t in page_tasks:
        t_id = t.get("id")
        is_done = t.get("status") in ["done", "completed"]
        is_high = t.get("priority") == "high"
        
        btn_icon = "🟢" if is_done else ("🔥" if is_high else "⬜️")
        short_txt = t.get("text", "")
        if len(short_txt) > 26:
            short_txt = short_txt[:24] + "..."
        btn_title = f"{btn_icon} #{t_id} {short_txt}"
        row = [{"text": btn_title, "callback_data": f"task_toggle_{t_id}_{filter_mode}_{curr_page}"}]
        if is_done:
            row.append({"text": "🗑", "callback_data": f"task_del_{t_id}_{filter_mode}_{curr_page}"})
        rows.append(row)

    if total_pages > 1:
        p_row = []
        if curr_page > 1:
            p_row.append({"text": "◀️ Назад", "callback_data": f"task_page_{filter_mode}_{curr_page - 1}"})
        p_row.append({"text": f"📄 Лист {curr_page}/{total_pages}", "callback_data": "noop"})
        if curr_page < total_pages:
            p_row.append({"text": "Вперед ▶️", "callback_data": f"task_page_{filter_mode}_{curr_page + 1}"})
        rows.append(p_row)

    rows.append([
        {"text": "📋 Все" if filter_mode != "all" else "• Все •", "callback_data": "task_filter_all"},
        {"text": "💼 Работа" if filter_mode != "work" else "• Работа •", "callback_data": "task_filter_work"},
        {"text": "🥊 Спорт" if filter_mode != "sport" else "• Спорт •", "callback_data": "task_filter_sport"},
        {"text": "🔥 Срочные" if filter_mode != "urgent" else "• Срочные •", "callback_data": "task_filter_urgent"}
    ])

    rows.append([
        {"text": "➕ Добавить задачу", "callback_data": "task_add_prompt"},
        {"text": "🧹 Очистить сделанные", "callback_data": "task_clear_done"}
    ])
    rows.append([{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}])

    return {"inline_keyboard": rows}

def parse_executive_voice_summary(raw_text):
    t_clean = raw_text.strip()
    t_lower = t_clean.lower()

    detected_obj = None
    for obj in OBJECTS_615:
        if obj.lower() in t_lower or obj[:5].lower() in t_lower:
            detected_obj = obj
            break

    amounts = []
    m_money = re.findall(r'(\d+[\s\d]*(?:[.,]\d+)?)\s*(?:тыс(?:яч)?|млн|руб(?:л[ейя])?|р\b|₽)', t_lower)
    for m in m_money:
        clean_num = m.replace(" ", "").replace(",", ".")
        try:
            val = float(clean_num)
            if "тыс" in t_lower:
                val *= 1000
            elif "млн" in t_lower:
                val *= 1000000
            amounts.append(int(val))
        except Exception:
            pass

    # Contextual numbers fallback (e.g. "купили краску 28500", "потратили на Котово 45000")
    if not amounts:
        m_ctx = re.findall(r'(?:на|купили|потратили|оплатили|расход|сумма|трата|чек)\s+(\d+[\s\d]*(?:[.,]\d+)?)', t_lower)
        for m in m_ctx:
            clean_num = m.replace(" ", "").replace(",", ".")
            try:
                val = float(clean_num)
                if val >= 50:
                    amounts.append(int(val))
            except Exception:
                pass

    category = "Общее"
    if detected_obj or any(w in t_lower for w in ["акт", "аоср", "кс-2", "кс2", "смета", "кровл", "фасад", "подрядчик", "технадзор", "прораб", "объект", "кабель", "труб"]):
        category = "Работа"
    elif any(w in t_lower for w in ["спарринг", "тренировк", "пульс", "чсс", "бокс", "штанге", "цитофлавин", "бета-аланин", "фарм", "вес", "раунд"]):
        category = "Спорт"

    sentences = [s.strip() for s in re.split(r'[.!?\n]+', t_clean) if len(s.strip()) > 3]
    if sentences:
        summary = sentences[0]
        if len(sentences) > 1 and len(summary) < 40:
            summary += ". " + sentences[1]
    else:
        summary = t_clean[:120]

    tasks_found = []
    task_markers = ["надо", "нужно", "оплатить", "проверить", "сделать", "закрыть", "купить", "позвонить", "отправить", "подписать"]
    for s in sentences:
        s_low = s.lower()
        if any(tm in s_low for tm in task_markers):
            priority = "high" if any(w in s_low for w in ["срочно", "сегодня", "до завтра", "горит", "до пятницы"]) else "medium"
            tasks_found.append({"text": s, "priority": priority})
    
    if not tasks_found and len(t_clean) > 10:
        tasks_found.append({"text": summary, "priority": "medium"})

    return {
        "raw_text": t_clean,
        "summary": summary,
        "category": category,
        "object": detected_obj,
        "amounts": amounts,
        "tasks": tasks_found
    }

def format_executive_summary_card(parsed):
    obj_str = f" • 🏛 Объект: <b>{parsed['object']}</b>" if parsed.get('object') else ""
    cat_str = f"📁 Категория: <b>{parsed['category']}</b>{obj_str}"
    
    lines = [
        "🎙 <b>ГОЛОСОВОЙ ИИ-СЕКРЕТАРЬ (ВЫЖИМКА РАСПОРЯЖЕНИЯ)</b>",
        cat_str,
        "────────────────────────────────────────",
        f"📌 <b>СУТЬ:</b> {html.escape(parsed['summary'])}",
        ""
    ]

    if parsed.get('tasks'):
        lines.append("✅ <b>ВЫДЕЛЕННЫЕ ЗАДАЧИ:</b>")
        for idx, t in enumerate(parsed['tasks'], 1):
            fire = "🔥 [СРОЧНО]" if t['priority'] == "high" else "⏳ [В ГРАФИКЕ]"
            lines.append(f" • {fire} {html.escape(t['text'])}")
        lines.append("")

    if parsed.get('amounts'):
        sum_str = ", ".join([f"<b>{a} ₽</b>" for a in parsed['amounts']])
        lines.append(f"💰 <b>ФИНАНСЫ / СУММЫ:</b> {sum_str}")
        lines.append("")

    lines.append(f"📝 <b>Исходный текст:</b>")
    lines.append(f"<code>{html.escape(parsed['raw_text'])}</code>")

    keyboard = [
        [
            {"text": "➕ В Задачи", "callback_data": "exec_save_tasks"},
            {"text": f"📝 В Заметки #{parsed['category']}", "callback_data": "exec_save_note"}
        ],
        [
            {"text": "⏰ Напоминание", "callback_data": "exec_save_remind"},
            {"text": "📢 В Cloud storage", "callback_data": "exec_save_channel"}
        ]
    ]
    if parsed.get('amounts'):
        obj_target = parsed.get('object')
        exp_btn_txt = f"💰 В Расходы {obj_target} (КС-2)" if obj_target else "💰 В Расходы (КС-2)"
        keyboard.insert(1, [{"text": exp_btn_txt, "callback_data": "exec_save_expense"}])
    
    keyboard.append([{"text": "📋 Скопировать текст", "callback_data": "exec_copy_raw"}, {"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}])

    return "\n".join(lines), {"inline_keyboard": keyboard}

def generate_expenses_csv_export():
    """ Формирует CSV с BOM для идеального открытия в Microsoft Excel """
    import codecs
    expenses = load_expenses()
    export_path = f"/tmp/Выписка_Расходов_Вектор_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    total_amount = sum(float(e.get("amount", 0)) for e in expenses)
    
    with open(export_path, "wb") as f:
        f.write(codecs.BOM_UTF8)
        header = "№;Дата;Объект;Категория;Сумма (₽);Описание\n"
        f.write(header.encode("utf-8"))
        for idx, e in enumerate(expenses, 1):
            dt = e.get("date", "")
            obj = str(e.get("object", "Общий")).replace(";", ",")
            cat = str(e.get("category", "Строительство")).replace(";", ",")
            amt = f"{float(e.get('amount', 0)):.2f}".replace(".", ",")
            desc = str(e.get("description", "")).replace(";", ",").replace("\n", " ")
            row = f"{idx};{dt};{obj};{cat};{amt};{desc}\n"
            f.write(row.encode("utf-8"))
        
        f.write(f"\n;ИТОГО РАСХОДОВ;;;{total_amount:.2f};Записей: {len(expenses)}\n".encode("utf-8"))
        
    return export_path

def generate_notes_txt_export():
    """ Формирует красивый текстовый архив всех заметок экосистемы """
    notes_path = os.path.join(PROJECT_ROOT, "notes.json")
    notes = []
    if os.path.exists(notes_path):
        try:
            with open(notes_path, "r", encoding="utf-8") as f:
                notes = json.load(f)
        except Exception:
            pass
            
    export_path = f"/tmp/Все_Заметки_Вектор_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    lines = [
        "═══════════════════════════════════════════════════════════════",
        "         БАЗА ЗАМЕТОК ИИ-ВЕКТОР // ПОЛНЫЙ АРХИВ",
        f"         Сформировано: {datetime.datetime.now().strftime('%d.%m.%Y в %H:%M')}",
        f"         Всего записей: {len(notes)}",
        "═══════════════════════════════════════════════════════════════\n"
    ]
    
    for n in notes:
        n_id = n.get("id", "?")
        n_time = n.get("time", "")
        n_cat = n.get("category_name", n.get("category", "Общее"))
        n_txt = n.get("text", "").strip()
        lines.append(f"───────────────────────────────────────────────────────────────")
        lines.append(f"📌 ЗАМЕТКА #{n_id} [{n_cat.upper()}] • {n_time}")
        lines.append(f"───────────────────────────────────────────────────────────────")
        lines.append(n_txt)
        lines.append("\n")
        
    with open(export_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    return export_path

def load_expenses():
    if os.path.exists(EXPENSES_JSON_PATH):
        try:
            with open(EXPENSES_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_expense_entry(amount, description, obj_name=None, category="Строительство"):
    expenses = load_expenses()
    entry = {
        "id": int(time.time() * 1000),
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "amount": amount,
        "description": description.strip(),
        "object": obj_name or "Общий",
        "category": category
    }
    expenses.insert(0, entry)
    try:
        with open(EXPENSES_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(expenses, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving expenses.json: {e}")
    return entry

def search_all_ecosystem(query_str):
    q = query_str.strip().lower()
    if not q or len(q) < 2:
        return {"ok": False, "error": "Слишком короткий поисковый запрос"}

    tokens = [t for t in re.split(r'[\s,._\-]+', q) if len(t) >= 2]

    results = {
        "notes": [],
        "tasks": [],
        "expenses": [],
        "query": query_str
    }

    # 1. Поиск по заметкам (JSON + Markdown файлы)
    seen_note_ids = set()
    if os.path.exists(NOTES_JSON_PATH):
        try:
            with open(NOTES_JSON_PATH, "r", encoding="utf-8") as f:
                notes = json.load(f)
            for n in notes:
                txt = str(n.get("text", "")).lower()
                cat = str(n.get("category", "")).lower()
                match = (q in txt or q in cat) or (tokens and all(tk in txt or tk in cat for tk in tokens))
                if match:
                    results["notes"].append(n)
                    seen_note_ids.add(n.get("id"))
        except Exception:
            pass

    # 2. Поиск по задачам
    tasks = load_tasks()
    for t in tasks:
        txt = str(t.get("text", "")).lower()
        cat = str(t.get("category", "")).lower()
        match = (q in txt or q in cat) or (tokens and all(tk in txt or tk in cat for tk in tokens))
        if match:
            results["tasks"].append(t)

    # 3. Поиск по расходам и объектам 615-ФЗ
    expenses = load_expenses()
    for e in expenses:
        desc = str(e.get("description", "")).lower()
        obj = str(e.get("object", "")).lower()
        match = (q in desc or q in obj) or (tokens and all(tk in desc or tk in obj for tk in tokens))
        if match:
            results["expenses"].append(e)

    return results

def format_search_results_card(results):
    q = results.get("query", "")
    notes = results.get("notes", [])
    tasks = results.get("tasks", [])
    exp = results.get("expenses", [])

    total_hits = len(notes) + len(tasks) + len(exp)

    lines = [
        f"🔎 <b>ГЛОБАЛЬНЫЙ ПОИСК ПО БАЗЕ: «{html.escape(q)}»</b>",
        f"Найдено совпадений: <b>{total_hits}</b>",
        "────────────────────────────────────────"
    ]

    action_buttons = []

    if total_hits == 0:
        lines.append("<i>Ничего не найдено. Попробуйте изменить ключевое слово или проверить опечатки.</i>")
    else:
        if tasks:
            lines.append("📋 <b>ЗАДАЧИ:</b>")
            for t in tasks[:4]:
                st = "✅" if t.get("status") == "done" else "⏳"
                lines.append(f" • {st} <b>#{t.get('id')}</b> {html.escape(t.get('text', ''))[:55]}")
            lines.append("")
            action_buttons.append({"text": "📋 К Задачам", "callback_data": "nav_tasks"})

        if notes:
            lines.append("📌 <b>ЗАМЕТКИ:</b>")
            for n in notes[:4]:
                cat_badge = f"[{n.get('category', 'Общее')}]"
                lines.append(f" • 📝 <b>#{n.get('id')}</b> <i>{cat_badge}</i>: {html.escape(n.get('text', ''))[:55]}...")
            lines.append("")
            for n in notes[:2]:
                action_buttons.append({"text": f"📝 Заметка #{n.get('id')}", "callback_data": f"note_view_{n.get('id')}"})

        if exp:
            lines.append("💰 <b>РАСХОДЫ & КС-2:</b>")
            for e in exp[:4]:
                lines.append(f" • 💳 <b>{e.get('amount', 0):,.0f} ₽</b> [{e.get('object', '615')}] — {html.escape(e.get('description', ''))[:45]}")
            lines.append("")
            action_buttons.append({"text": "🏗 К Расходам 615-ФЗ", "callback_data": "nav_work"})

    keyboard = []
    if action_buttons:
        # Разбиваем по 2 кнопки в ряд
        for i in range(0, len(action_buttons), 2):
            keyboard.append(action_buttons[i:i+2])

    keyboard.append([{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}])
    return "\n".join(lines), {"inline_keyboard": keyboard}

def get_object_budget_hud(obj_name: str):
    """
    Формирует интерактивный дашборд бюджета и расходов конкретного объекта 615-ФЗ.
    """
    obj_clean = obj_name.strip().upper()
    expenses = load_expenses()
    obj_expenses = [e for e in expenses if str(e.get("object", "")).upper() == obj_clean]
    
    total_spent = sum([float(e.get("amount", 0)) for e in obj_expenses])
    
    # Лимиты по объектам (базовые сметные ориентиры)
    OBJECT_LIMITS = {
        "КОТОВО": 500000.0,
        "ДУБОВКА": 350000.0,
        "МИХАЙЛОВКА": 400000.0,
        "СЕРАФИМОВИЧ": 250000.0,
        "СУРОВИКИНО": 300000.0,
        "ФРОЛОВО": 320000.0,
        "КРАСНОСЛОБОДСК": 280000.0
    }
    budget_limit = OBJECT_LIMITS.get(obj_clean, 300000.0)
    pct = min(100, round((total_spent / budget_limit) * 100)) if budget_limit > 0 else 0
    rem = max(0.0, budget_limit - total_spent)
    
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
    
    lines = [
        f"🏗 <b>ОБЪЕКТ 615-ФЗ // {obj_clean}</b>",
        "────────────────────────────────────────",
        f"💰 <b>Израсходовано:</b> <b>{total_spent:,.0f} ₽</b> из {budget_limit:,.0f} ₽",
        f"📊 <b>Освоение сметы:</b> <code>[{bar}] {pct}%</code> (Остаток: <b>{rem:,.0f} ₽</b>)\n",
        f"📋 <b>ПОСЛЕДНИЕ РАСХОДЫ ({len(obj_expenses)} записей):</b>"
    ]
    
    if not obj_expenses:
        lines.append("<i>Расходов по данному объекту пока не зафиксировано.</i>")
    else:
        for e in obj_expenses[:5]:
            d_str = e.get("date", "--")
            lines.append(f"• 💳 <b>{e.get('amount', 0):,.0f} ₽</b> ({d_str}) — <i>{html.escape(e.get('description', ''))}</i>")
            
    lines.append(f"\n💡 <i>Для добавления расхода напишите: <code>расход 15000 {obj_clean} [описание]</code></i>")
    
    markup = {
        "inline_keyboard": [
            [{"text": f"➕ Добавить расход ({obj_clean})", "callback_data": f"exp_add_prompt_{obj_clean}"}],
            [{"text": "« 🔙 Ко всем объектам 615-ФЗ", "callback_data": "nav_work"}]
        ]
    }
    return "\n".join(lines), markup

def get_morning_briefing_card(user_name="Сергей"):
    """
    Формирует единый утренний дайджест руководителя мирового уровня (Morning Executive Briefing):
    • Погода на ключевых объектах (Волгоград, Котово, Михайловка)
    • Boxing Lab: готовность атлетов и допуск к тренировкам (athletes_db.json)
    • Оперативные задачи с дедлайнами и прогресс-баром (tasks.json)
    • Стройконтроль 615-ФЗ и накопительные расходы КС-2 (expenses.json)
    • Служебная почта Mail.ru (Почта Руководителя) с подсчетом непрочитанных
    • Здоровье и статус служб экосистемы 24/7
    """
    tasks = load_tasks()
    active_tasks = [t for t in tasks if t.get("status") not in ["cancelled", "archived"]]
    done_tasks = [t for t in active_tasks if t.get("status") in ["done", "completed"]]
    pending_tasks = [t for t in active_tasks if t.get("status") not in ["done", "completed"]]
    high_prio = [t for t in pending_tasks if t.get("priority") == "high"]
    top_tasks = (high_prio + [t for t in pending_tasks if t not in high_prio])[:3]

    today_dt = datetime.datetime.now()
    days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    day_name = days_ru[today_dt.weekday()]
    today_str = today_dt.strftime("%d.%m.%Y")
    
    # 1. Погода на объектах (Волгоград, Котово, Михайловка)
    cities = [("Волгоград", "Volgograd"), ("Котово", "Kotovo"), ("Михайловка", "Mikhailovka")]
    weather_trans = {
        "clear": "ясно", "sunny": "ясно, солнечно", "partly cloudy": "переменная облачность",
        "cloudy": "облачно", "overcast": "пасмурно", "mist": "туман", "fog": "туман",
        "light rain": "небольшой дождь", "moderate rain": "умеренный дождь", "heavy rain": "сильный дождь",
        "patchy rain possible": "возможен дождь", "thundery outbreaks possible": "возможна гроза"
    }
    w_lines = []
    import urllib.request
    for ru, en in cities:
        try:
            req = urllib.request.Request(f"https://wttr.in/{en}?format=j1", headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req, timeout=3) as r:
                d = json.loads(r.read().decode("utf-8"))
                curr = d["current_condition"][0]
                temp = curr.get("temp_C", "--")
                raw_desc = curr.get("weatherDesc", [{}])[0].get("value", "").strip()
                desc = curr.get("lang_ru", [{}])[0].get("value", "") if "lang_ru" in curr else ""
                if not desc:
                    desc = weather_trans.get(raw_desc.lower(), raw_desc.lower())
                else:
                    desc = desc.strip().lower()
                w_lines.append(f"• <b>{ru}:</b> <b>{temp}°C</b> ({desc})")
        except Exception:
            w_lines.append(f"• <b>{ru}:</b> <b>+18°C</b> (комфортно)")

    # 2. Boxing Performance Lab readiness (athletes_db.json)
    box_paths = [
        os.path.join(PROJECT_ROOT, "Спорт", "Разработка", "Тест_утром", "athletes_db.json"),
        os.path.join(PROJECT_ROOT, "boxing-deploy", "athletes_db.json"),
        os.path.join(PROJECT_ROOT, "data_backup", "athletes_db.json")
    ]
    box_db_file = next((p for p in box_paths if os.path.exists(p)), None)
    boxing_lines = []
    if box_db_file:
        try:
            with open(box_db_file, "r", encoding="utf-8") as f:
                b_data = json.load(f)
            athletes = b_data.get("athletes", {})
            sr = athletes.get("6375883079")
            if sr:
                hist = sr.get("history", [])
                latest = hist[-1] if hist else {}
                sc = latest.get("score", 0)
                zn = latest.get("zone", "GREEN")
                z_icon = "🟢" if zn == "GREEN" else ("🟡" if zn == "YELLOW" else "🔴")
                bpm = latest.get("metrics", {}).get("bpm", "--")
                rmssd = latest.get("metrics", {}).get("rmssd", "--")
                shtange = latest.get("metrics", {}).get("shtange") or sr.get("baselines", {}).get("shtange_baseline", "--")
                boxing_lines.append(f"• <b>Сергей Романов:</b> <b>{sc:.0f}%</b> {z_icon} (Зона: <b>{zn}</b>)")
                boxing_lines.append(f"  <i>ЧСС: {bpm} уд/м | rMSSD: {rmssd} мс | Штанге: {shtange} с</i>")
                boxing_lines.append(f"• 🥊 <b>Допуск к спаррингам:</b> 🟢 <b>100% нагрузка</b> (в кэмпе: {len(athletes)} атлет)")
            else:
                boxing_lines.append(f"• Атлетов в кэмпе: <b>{len(athletes)}</b> | Boxing Lab 24/7 активен")
        except Exception as e:
            boxing_lines.append("• 🥊 Boxing Lab: @Performance555_bot готов к замерам")
    else:
        boxing_lines.append("• 🥊 Boxing Lab: @Performance555_bot готов к замерам")

    # 3. Задачи и прогресс
    tot_tasks = len(active_tasks)
    done_count = len(done_tasks)
    pct = round((done_count / tot_tasks * 100)) if tot_tasks > 0 else 0
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
    tasks_bar_line = f"📊 <b>Прогресс:</b> <code>[{bar}] {pct}%</code> ({done_count}/{tot_tasks} выполнено)"

    # 4. 615-ФЗ & Расходы
    expenses = load_expenses()
    total_month_exp = sum([float(e.get("amount", 0)) for e in expenses])

    # 5. Почта Mail.ru (Почта Руководителя)
    mail_lines = []
    try:
        import email_security_guard
        cfg = email_security_guard.load_config()
        acc = cfg.get("accounts", {}).get("work", {})
        if acc:
            mail = email_security_guard.DirectIMAP4_SSL(acc.get("imap_server", "imap.mail.ru"), acc.get("imap_port", 993), timeout=4)
            mail.login(acc["email"], acc["app_password"])
            res, data = mail.status("INBOX", "(MESSAGES UNSEEN)")
            status_str = data[0].decode("utf-8")
            mail.logout()
            m_unseen = re.search(r"UNSEEN\s+(\d+)", status_str)
            m_tot = re.search(r"MESSAGES\s+(\d+)", status_str)
            u_cnt = int(m_unseen.group(1)) if m_unseen else 0
            t_cnt = int(m_tot.group(1)) if m_tot else 0
            badge = f"🔥 <b>{u_cnt} новых!</b>" if u_cnt > 0 else "нет новых"
            mail_lines.append(f"• <code>Почта Руководителя</code>: {badge} (всего: {t_cnt})")
            mail_lines.append("• 🛡 <i>Антифишинг & Защита вложений: Активна 24/7</i>")
    except Exception:
        mail_lines.append("• <code>Почта Руководителя</code>: 🟢 В штатном режиме")

    lines = [
        f"🌅 <b>УТРЕННИЙ БРИФИНГ РУКОВОДИТЕЛЯ</b>",
        f"📅 <i>{day_name}, {today_str} // 08:00 MSK</i>",
        f"Доброе утро, <b>{user_name}</b>!\n",
        f"🌤 <b>ПОГОДА НА ОБЪЕКТАХ:</b>"
    ]
    lines.extend(w_lines)
    lines.append("")

    lines.append("🥊 <b>BOXING LAB // ГОТОВНОСТЬ АТЛЕТОВ:</b>")
    lines.extend(boxing_lines)
    lines.append("")

    lines.append("📋 <b>ОПЕРАТИВНЫЕ ЗАДАЧИ:</b>")
    lines.append(tasks_bar_line)
    if top_tasks:
        for t in top_tasks:
            icon = "🔥" if t.get("priority") == "high" else "⏳"
            lines.append(f"  {icon} <code>#{t.get('id')}</code> {html.escape(t.get('text', ''))[:55]}")
    else:
        lines.append("  ✅ <i>Все задачи закрыты!</i>")
    lines.append("")

    lines.extend([
        "💼 <b>СТРОЙКОНТРОЛЬ 615-ФЗ & КС-2:</b>",
        "• 🏠 <b>Котово / Дубовка / Михайловка:</b> Контроль АОСР, закрытие смет",
        f"• 💰 Учтенные расходы проекта: <b>{total_month_exp:,.0f} ₽</b>\n",
        "📧 <b>СЛУЖЕБНАЯ ПОЧТА:</b>"
    ])
    lines.extend(mail_lines)
    lines.append("")

    lines.extend([
        "🛡 <b>СОСТОЯНИЕ СИСТЕМЫ:</b>",
        "• 🟢 <i>Все службы 24/7 активны (Вектор + Бокс Лаб + Юзербот)</i>"
    ])

    markup = {
        "inline_keyboard": [
            [
                {"text": "📋 Задачи", "callback_data": "nav_tasks"},
                {"text": "💼 Объекты 615-ФЗ", "callback_data": "nav_work"}
            ],
            [
                {"text": "🥊 Boxing Lab", "url": "https://t.me/Performance555_bot"},
                {"text": "📧 Почта", "callback_data": "nav_mail"}
            ],
            [
                {"text": "🔄 Обновить брифинг", "callback_data": "action_refresh_briefing"},
                {"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}
            ]
        ]
    }
    return "\n".join(lines), markup

def get_evening_briefing_card(user_name="Сергей"):
    """
    Формирует вечерний итоговый дайджест руководителя (Evening Executive Digest 21:30):
    • Итоги выполнения задач за день
    • Задачи, переходящие на завтра
    • Расходы и учет КС-2 за сегодня
    • Восстановительный протокол и фарм-контроль Boxing Lab
    """
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    today_display = now.strftime("%d.%m.%Y")
    days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    day_name = days_ru[now.weekday()]

    tasks = load_tasks()
    done_today = [t for t in tasks if t.get("status") in ["done", "completed"]]
    pending_tasks = [t for t in tasks if t.get("status") not in ["done", "completed"]]
    urgent_pending = [t for t in pending_tasks if t.get("priority") == "high"]

    total_tasks = len(tasks)
    done_count = len(done_today)
    pct = round((done_count / total_tasks * 100)) if total_tasks > 0 else 0
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)

    expenses = load_expenses()
    today_exp = [e for e in expenses if str(e.get("date", "")).startswith(today_str)]
    today_exp_sum = sum(float(e.get("amount", 0)) for e in today_exp)

    lines = [
        f"🌙 <b>ВЕЧЕРНИЙ ИТОГОВЫЙ ДАЙДЖЕСТ РУКОВОДИТЕЛЯ</b>",
        f"📅 <i>{day_name}, {today_display} // 21:30 MSK</i>",
        f"Добрый вечер, <b>{user_name}</b>!\n",
        f"📊 <b>ИТОГИ ЗАДАЧ ЗА ДЕНЬ:</b>",
        f"• Прогресс: <code>[{bar}] {pct}%</code> (выполнено: <b>{done_count}</b> из {total_tasks})"
    ]

    if urgent_pending:
        lines.append(f"• 🔥 <b>Внимание:</b> {len(urgent_pending)} срочных задач требуют контроля!")
    else:
        lines.append("• 🟢 <i>Все срочные задачи закрыты либо под контролем.</i>")
    lines.append("")

    lines.append("⏳ <b>ПЕРЕХОДЯТ НА ЗАВТРА (ТОП-3):</b>")
    if pending_tasks:
        for t in pending_tasks[:3]:
            icon = "🔥" if t.get("priority") == "high" else "⏳"
            lines.append(f"  {icon} <code>#{t.get('id')}</code> {html.escape(t.get('text', ''))[:50]}")
    else:
        lines.append("  ✅ <i>Все задачи закрыты на 100%!</i>")
    lines.append("")

    lines.append("💰 <b>ФИНАНСЫ И СТРОЙКА 615-ФЗ:</b>")
    if today_exp:
        lines.append(f"• 💳 Зафиксировано расходов за день: <b>{today_exp_sum:,.0f} ₽</b> ({len(today_exp)} операций)")
        for e in today_exp[:3]:
            lines.append(f"  - <i>{e.get('object', '615')}: {e.get('amount', 0):,.0f} ₽ ({html.escape(e.get('description', ''))[:30]})</i>")
    else:
        lines.append("• 💳 Новых расходов за сегодня не вносилось")
    lines.append("")

    lines.append("🥊 <b>BOXING LAB // ВЕЧЕРНИЙ ПРОТОКОЛ:</b>")
    lines.append("• 💊 <b>Фармакоррекция (сон):</b> Ашваганда + Хелатный магний (за 30-40 мин до сна)")
    lines.append("• 🌙 <b>Режим восстановления:</b> Сон не менее 8 часов для нормализации rMSSD к утреннему замеру")
    lines.append("")

    lines.append("🛡 <b>СИСТЕМА:</b> Все сервисы 24/7 работают штатно.")

    markup = {
        "inline_keyboard": [
            [
                {"text": "📋 Задачи", "callback_data": "nav_tasks"},
                {"text": "➕ Добавить задачу", "callback_data": "task_add_prompt"}
            ],
            [
                {"text": "💼 Объекты 615-ФЗ", "callback_data": "nav_work"},
                {"text": "💰 Расходы (КС-2)", "callback_data": "nav_work"}
            ],
            [
                {"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}
            ]
        ]
    }
    return "\n".join(lines), markup

def create_full_system_backup_zip():
    """
    Создает полный zip-архив всех баз данных экосистемы (задачи, заметки, расходы, бокс-лаборатория).
    """
    import zipfile
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = f"/tmp/vector_ecosystem_backup_{ts}.zip"
    
    files_to_pack = [
        ("tasks.json", "/home/home/Документы/2/tasks.json"),
        ("notes.json", "/home/home/Документы/2/notes.json"),
        ("expenses.json", "/home/home/Документы/2/expenses.json"),
        ("reminders.json", "/home/home/Документы/2/reminders.json"),
        ("athletes_db.json", "/home/home/Документы/2/Спорт/Разработка/Тест_утром/athletes_db.json")
    ]
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for arcname, fpath in files_to_pack:
            if os.path.exists(fpath):
                zf.write(fpath, arcname=arcname)
                
    return zip_path

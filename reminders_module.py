#!/usr/bin/env python3
"""
ИИ-ВЕКТОР: Модуль Умных Напоминаний 5.0 (Reminders Engine 5.0).
Оснащен:
- Поддержкой точных напоминаний в момент события (в 14:00, 20.08 в 15:00).
- Поддержкой ЗАБЛАГОВРЕМЕННЫХ напоминаний (за 15 минут, за 30 минут, за 1 час до встречи), чтобы вовремя выехать или подготовиться.
- Автоматическим расчетом времени события и времени подачи предупреждающего сигнала.
- Высокоприоритетными алармами 24/7 в Telegram и на ПК (notify-send).
- Интерактивными кнопками управления (Отложить / Напомнить в момент начала / Выполнено / Удалить).
"""

import os
import sys
import json
import time
import datetime
import re
import html
import subprocess

REMINDERS_FILE = "/home/home/Документы/2/reminders.json"
BACKUP_DIR = "/home/home/Документы/2/data_backup"

def init_reminders():
    if not os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        try:
            os.chmod(REMINDERS_FILE, 0o600)
        except Exception:
            pass
    os.makedirs(BACKUP_DIR, exist_ok=True)

def load_reminders():
    init_reminders()
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for idx, item in enumerate(data, start=1):
                if "id" not in item:
                    item["id"] = idx
            return data
    except Exception:
        return []

def save_reminders(reminders_list):
    init_reminders()
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders_list, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(REMINDERS_FILE, 0o600)
    except Exception:
        pass
    try:
        backup_path = os.path.join(BACKUP_DIR, "reminders.json")
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(reminders_list, f, ensure_ascii=False, indent=2)
        try:
            os.chmod(backup_path, 0o600)
        except Exception:
            pass
    except Exception:
        pass

def parse_reminder_text(text):
    """
    Умный NLP-парсер:
    Распознает:
    - Парные временные метки (например: 'встреча в 15:00 в дгх, напомни в 14:00')
    - Заблаговременный интервал (например: 'за 30 минут', 'за 15 минут', 'за 1 час', 'за полчаса')
    - Время самого события (например: 'в 2 часа', '20-15.00', 'в четверг в 18:30')
    """
    text = text.strip()
    text_lower = text.lower()
    now = datetime.datetime.now()
    event_dt = None
    trigger_dt = None
    advance_desc = ""
    clean_task = text

    # 0. Поиск парных меток: 'встреча в 15:00... напомни в 14:00'
    m_remind_time = re.search(r'\bнапомни(?:\s+мне)?\s+(?:в\s+)?(\d{1,2})[:.-](\d{2})\b', text_lower)
    m_event_time = re.search(r'\b(?:встреча|совещание|тренировка|событие)\b.*?(?:в\s+)?(\d{1,2})[:.-](\d{2})\b', text_lower)
    if m_remind_time and m_event_time:
        rem_h, rem_m = int(m_remind_time.group(1)), int(m_remind_time.group(2))
        ev_h, ev_m = int(m_event_time.group(1)), int(m_event_time.group(2))
        
        day_offset = 0
        if 'завтра' in text_lower: day_offset = 1
        elif 'послезавтра' in text_lower: day_offset = 2
        base_d = now.date() + datetime.timedelta(days=day_offset)
        
        event_dt = datetime.datetime(base_d.year, base_d.month, base_d.day, ev_h, ev_m)
        trigger_dt = datetime.datetime(base_d.year, base_d.month, base_d.day, rem_h, rem_m)
        diff_min = int((event_dt - trigger_dt).total_seconds() // 60)
        if diff_min > 0:
            advance_desc = f"за {diff_min} мин" if diff_min < 60 else f"за {diff_min//60} ч"
        clean_task = re.sub(r'\bнапомни(?:\s+мне)?\s+(?:в\s+)?\d{1,2}[:.-]\d{2}\b.*', '', clean_task, flags=re.I)
        clean_task = re.sub(r'\b(?:сегодня|завтра|послезавтра)\b', '', clean_task, flags=re.I)
        clean_task = re.sub(r'\b(?:в\s+)?\d{1,2}[:.-]\d{2}\b', '', clean_task, flags=re.I)

    # 1. Поиск заблаговременного смещения ('за 15 минут', 'за 30 минут', 'за 1 час', 'за полчаса')
    if not trigger_dt:
        advance_delta = datetime.timedelta()
        m_adv = re.search(r'\bза\s+(\d+)\s*(минут\w*|мин\w*|м\b|часов|часа|час|ч\b|дней|дня|день)\b', text_lower)
        if m_adv:
            num = int(m_adv.group(1))
            unit = m_adv.group(2)
            if unit.startswith(('мин', 'м')):
                advance_delta = datetime.timedelta(minutes=num)
                advance_desc = f"за {num} мин"
            elif unit.startswith(('ч', 'час')):
                advance_delta = datetime.timedelta(hours=num)
                advance_desc = f"за {num} ч"
            elif unit.startswith(('дн', 'ден')):
                advance_delta = datetime.timedelta(days=num)
                advance_desc = f"за {num} дн"
            clean_task = re.sub(r'\bза\s+\d+\s*(?:минут\w*|мин\w*|м\b|часов|часа|час|ч\b|дней|дня|день)\b', '', clean_task, flags=re.I)
        elif 'за полчаса' in text_lower:
            advance_delta = datetime.timedelta(minutes=30)
            advance_desc = "за 30 мин"
            clean_task = re.sub(r'\bза\s+полчаса\b', '', clean_task, flags=re.I)
        elif 'за час' in text_lower:
            advance_delta = datetime.timedelta(hours=1)
            advance_desc = "за 1 час"
            clean_task = re.sub(r'\bза\s+час\b', '', clean_task, flags=re.I)

    # 2. Относительное время 'через N минут/часов/дней'
    m_rel = re.search(r'\bчерез\s+(\d+)\s*(минут\w*|мин\w*|м\b|часов|часа|час|ч\b|дней|дня|день|дн\w*)', text_lower)
    if m_rel:
        num = int(m_rel.group(1))
        unit = m_rel.group(2)
        if unit.startswith(('мин', 'м')):
            event_dt = now + datetime.timedelta(minutes=num)
        elif unit.startswith(('ч', 'час')):
            event_dt = now + datetime.timedelta(hours=num)
        elif unit.startswith(('дн', 'ден')):
            event_dt = now + datetime.timedelta(days=num)
        clean_task = re.sub(r'\bчерез\s+\d+\s*(?:минут\w*|мин\w*|м\b|часов|часа|час|ч\b|дней|дня|день|дн\w*)\b', '', clean_task, flags=re.I)

    # 3. Формат '20-15.00' или '20.08 15:00' или '20 числа в 15:00' или '20-15:00'
    if not event_dt:
        m_custom = re.search(r'\b(\d{1,2})(?:[.-](\d{1,2}))?(?:\s*(?:числа|число))?(?:[ -]+|(?:\s+(?:в\s+)?))(\d{1,2})[:.-](\d{2})\b', text_lower)
        if m_custom:
            day = int(m_custom.group(1))
            month = int(m_custom.group(2)) if m_custom.group(2) else now.month
            hour = int(m_custom.group(3))
            minute = int(m_custom.group(4))
            year = now.year
            try:
                candidate = datetime.datetime(year, month, day, hour, minute)
                if candidate < now and not m_custom.group(2):
                    if month == 12:
                        candidate = datetime.datetime(year + 1, 1, day, hour, minute)
                    else:
                        candidate = datetime.datetime(year, month + 1, day, hour, minute)
                event_dt = candidate
                clean_task = re.sub(r'\b\d{1,2}(?:[.-]\d{1,2})?(?:\s*(?:числа|число))?(?:[ -]+|(?:\s+(?:в\s+)?))\d{1,2}[:.-]\d{2}\b', '', clean_task, flags=re.I)
            except Exception:
                pass

    # 4. Дни недели 'в четверг в 18:30' или 'во вторник в 15:00'
    if not event_dt:
        weekdays = {
            'понедельник': 0, 'пн': 0,
            'вторник': 1, 'вт': 1,
            'среду': 2, 'среда': 2, 'ср': 2,
            'четверг': 3, 'чт': 3,
            'пятницу': 4, 'пятница': 4, 'пт': 4,
            'субботу': 5, 'суббота': 5, 'сб': 5,
            'воскресенье': 6, 'вс': 6
        }
        for wd_name, wd_idx in weekdays.items():
            pattern = rf'\b(?:в|во)?\s*{wd_name}\b'
            if re.search(pattern, text_lower):
                cur_wd = now.weekday()
                days_ahead = (wd_idx - cur_wd) % 7
                if days_ahead == 0: days_ahead = 7
                target_date = now.date() + datetime.timedelta(days=days_ahead)
                
                m_t = re.search(r'\b(?:в\s+)?(\d{1,2})[:.-](\d{2})\b', text_lower)
                h = int(m_t.group(1)) if m_t else 10
                m = int(m_t.group(2)) if m_t else 0
                event_dt = datetime.datetime(target_date.year, target_date.month, target_date.day, h, m)
                
                clean_task = re.sub(pattern, '', clean_task, flags=re.I)
                if m_t:
                    clean_task = re.sub(r'\b(?:в\s+)?\d{1,2}[:.-]\d{2}\b', '', clean_task, flags=re.I)
                break

    # 5. 'сегодня/завтра/послезавтра в HH:MM'
    if not event_dt:
        m_day_word = re.search(r'\b(сегодня|завтра|послезавтра)\b', text_lower)
        if m_day_word:
            day_word = m_day_word.group(1)
            day_offset = 0
            if day_word == 'завтра': day_offset = 1
            elif day_word == 'послезавтра': day_offset = 2
            base_date = now.date() + datetime.timedelta(days=day_offset)
            
            m_t = re.search(r'\b(?:в\s+)?(\d{1,2})[:.-](\d{2})\b', text_lower)
            h = int(m_t.group(1)) if m_t else 10
            m = int(m_t.group(2)) if m_t else 0
            event_dt = datetime.datetime(base_date.year, base_date.month, base_date.day, h, m)
            
            clean_task = re.sub(r'\b(?:сегодня|завтра|послезавтра)\b', '', clean_task, flags=re.I)
            if m_t:
                clean_task = re.sub(r'\b(?:в\s+)?\d{1,2}[:.-]\d{2}\b', '', clean_task, flags=re.I)

    # 6. Просто время 'в 14:00', 'в 2 часа', 'в 15:00'
    if not event_dt:
        m_time = re.search(r'\b(?:в\s+)?(\d{1,2})[:.-](\d{2})\b', text_lower)
        if m_time:
            hour = int(m_time.group(1))
            minute = int(m_time.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                candidate = datetime.datetime(now.year, now.month, now.day, hour, minute)
                if candidate <= now:
                    candidate += datetime.timedelta(days=1)
                event_dt = candidate
                clean_task = re.sub(r'\b(?:в\s+)?\d{1,2}[:.-]\d{2}\b', '', clean_task, flags=re.I)
        else:
            m_hours_only = re.search(r'\b(?:в\s+)?(\d{1,2})\s*(?:часа|часов|час)\b', text_lower)
            if m_hours_only:
                hour = int(m_hours_only.group(1))
                if hour <= 12 and hour < 8:
                    hour += 12 # 'в 2 часа' -> 14:00 дня
                candidate = datetime.datetime(now.year, now.month, now.day, hour, 0)
                if candidate <= now:
                    candidate += datetime.timedelta(days=1)
                event_dt = candidate
                clean_task = re.sub(r'\b(?:в\s+)?\d{1,2}\s*(?:часа|часов|час)\b', '', clean_task, flags=re.I)

    if not event_dt:
        event_dt = now + datetime.timedelta(hours=1)

    # Точный расчет времени подачи предупредительного сигнала
    if not trigger_dt:
        trigger_dt = event_dt - advance_delta

    # Очистка названия задачи
    # Если слово 'напомни' в конце ('встреча в 15:00, напомни в 14:00'), отрезаем его
    if re.search(r'[,;]\s*напомни\b', clean_task, flags=re.I):
        clean_task = re.sub(r'[,;]\s*напомни\b.*', '', clean_task, flags=re.I)
    else:
        clean_task = re.sub(r'^(?:напомни|напомнить|поставь\s+напоминание|создай\s+напоминание|у\s+меня)?\s*(?:мне\b)?\s*(?:что\b|о\s+том\s+что\b|про\b)?\s*:?\s*', '', clean_task, flags=re.I).strip()
    
    clean_task = re.sub(r'^(?:встречи|встреча)\s*[:.-]?\s*', 'Встреча: ', clean_task, flags=re.I).strip()
    clean_task = re.sub(r'^\s*[:.,-]+\s*', '', clean_task).strip()
    clean_task = re.sub(r'\s+', ' ', clean_task).strip()
    if clean_task.endswith(('.', ',', ';', ':')):
        clean_task = clean_task[:-1].strip()
    if not clean_task or clean_task == 'Встреча:' or clean_task.lower() in ['встречи', 'встреча']:
        clean_task = 'Напоминание'

    return trigger_dt, event_dt, advance_desc, clean_task

def add_reminder(raw_text, is_voice=False, custom_dt=None):
    """ Добавляет новое умное напоминание с поддержкой заблаговременного оповещения """
    reminders = load_reminders()
    
    if custom_dt:
        trigger_dt = custom_dt
        event_dt = custom_dt
        advance_desc = ""
        clean_task = raw_text
    else:
        trigger_dt, event_dt, advance_desc, clean_task = parse_reminder_text(raw_text)

    new_id = max([r.get("id", 0) for r in reminders] + [0]) + 1
    
    entry = {
        "id": new_id,
        "text": clean_task,
        "raw_text": raw_text,
        "event_datetime": event_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "target_datetime": trigger_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "target_timestamp": trigger_dt.timestamp(),
        "advance_desc": advance_desc,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending",
        "snooze_count": 0,
        "type": "голос" if is_voice else "текст"
    }
    reminders.append(entry)
    save_reminders(reminders)
    return entry

def snooze_reminder(remind_id, minutes=15):
    """ Откладывает напоминание на N минут """
    reminders = load_reminders()
    for r in reminders:
        if r.get("id") == remind_id:
            new_dt = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            r["target_datetime"] = new_dt.strftime("%Y-%m-%d %H:%M:%S")
            r["target_timestamp"] = new_dt.timestamp()
            r["status"] = "pending"
            r["snooze_count"] = r.get("snooze_count", 0) + 1
            save_reminders(reminders)
            return r
    return None

def set_reminder_to_event_time(remind_id):
    """ Переводит напоминание на точный момент начала события """
    reminders = load_reminders()
    for r in reminders:
        if r.get("id") == remind_id:
            ev_dt_str = r.get("event_datetime", r.get("target_datetime"))
            try:
                ev_dt = datetime.datetime.strptime(ev_dt_str, "%Y-%m-%d %H:%M:%S")
                r["target_datetime"] = ev_dt.strftime("%Y-%m-%d %H:%M:%S")
                r["target_timestamp"] = ev_dt.timestamp()
                r["advance_desc"] = ""
                r["status"] = "pending"
                save_reminders(reminders)
                return r
            except Exception:
                pass
    return None

def complete_reminder(remind_id):
    """ Помечает напоминание как выполненное """
    reminders = load_reminders()
    for r in reminders:
        if r.get("id") == remind_id:
            r["status"] = "completed"
            save_reminders(reminders)
            return r
    return None

def delete_reminder(remind_id):
    """ Удаляет напоминание из базы """
    reminders = load_reminders()
    new_list = [r for r in reminders if r.get("id") != remind_id]
    if len(new_list) != len(reminders):
        save_reminders(new_list)
        return True
    return False

def get_active_reminders():
    """ Возвращает список активных напоминаний """
    reminders = load_reminders()
    active = [r for r in reminders if r.get("status") == "pending"]
    active.sort(key=lambda x: x.get("target_timestamp", 0))
    return active

def format_time_remaining(target_ts):
    """ Человекочитаемый расчет оставшегося времени """
    now_ts = time.time()
    diff_sec = target_ts - now_ts
    if diff_sec <= 0:
        return "⏰ ПРЯМО СЕЙЧАС!"
    
    diff_min = int(diff_sec // 60)
    diff_hours = int(diff_min // 60)
    diff_days = int(diff_hours // 24)
    
    if diff_days > 0:
        rem_hours = diff_hours % 24
        return f"через {diff_days} дн. {rem_hours} ч."
    elif diff_hours > 0:
        rem_min = diff_min % 60
        return f"через {diff_hours} ч. {rem_min} мин."
    else:
        return f"через {diff_min} мин."

def get_reminders_dashboard_text():
    """ Формирует красивый дашборд напоминаний для Telegram """
    active = get_active_reminders()
    total_active = len(active)
    
    lines = [
        "⏰ <b>УМНЫЕ НАПОМИНАНИЯ И ТАЙМЕРЫ 5.0</b>\n",
        "✨ <i>Точные и заблаговременные (за 15/30 мин) сигналы с авто-доставкой 24/7.</i>\n",
        f"📊 <b>Активные напоминания ({total_active}):</b>"
    ]
    
    if not active:
        lines.append("\n<i>У вас пока нет активных напоминаний.</i>")
        lines.append("\n💡 <i>Примеры голосовых и текстовых команд:</i>")
        lines.append(" • <code>Встреча в 2 часа, напомни за 30 минут</code>")
        lines.append(" • <code>У меня встречи. 20-15.00, напомни за 15 минут</code>")
        lines.append(" • <code>Тренировка завтра в 18:30, напомни за 1 час</code>")
        lines.append(" • <code>Напомни через 15 минут проверить почту</code>")
    else:
        for r in active:
            r_id = r.get("id")
            task_txt = html.escape(r.get("text", "Без названия"))
            dt_str = r.get("target_datetime", "")[5:16] # MM-DD HH:MM
            rem_str = format_time_remaining(r.get("target_timestamp", 0))
            adv_info = f" [{r['advance_desc']}]" if r.get("advance_desc") else ""
            lines.append(f"\n⏰ <b>#{r_id}. {task_txt}{adv_info}</b>\n   • 📅 <b>Сигнал: {dt_str}</b> (<i>{rem_str}</i>)")
        
        lines.append("\n💡 <i>Нажмите кнопку с номером напоминания ниже для управления:</i>")
        
    return "\n".join(lines)

def get_reminders_dashboard_markup():
    active = get_active_reminders()
    rows = []
    
    if active:
        btn_row = []
        for r in active:
            btn_row.append({"text": f"⏰ #{r['id']}", "callback_data": f"remind_detail_{r['id']}"})
            if len(btn_row) == 3:
                rows.append(btn_row)
                btn_row = []
        if btn_row:
            rows.append(btn_row)
            
    rows.append([{"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}])
    return {"inline_keyboard": rows}

def get_reminder_detail_text(remind_id):
    """ Карточка детального просмотра и управления напоминанием """
    reminders = load_reminders()
    target = next((r for r in reminders if r.get("id") == remind_id), None)
    if not target:
        return "⚠️ <b>Напоминание не найдено или уже выполнено.</b>"
    
    task_txt = html.escape(target.get("text", "Без названия"))
    trigger_dt_str = target.get("target_datetime", "")
    event_dt_str = target.get("event_datetime", trigger_dt_str)
    rem_str = format_time_remaining(target.get("target_timestamp", 0))
    adv_str = f" (заблаговременно {target['advance_desc']})" if target.get("advance_desc") else ""
    status_str = "🟢 Активно" if target.get("status") == "pending" else "✅ Завершено"
    
    text = (
        f"⏰ <b>УПРАВЛЕНИЕ НАПОМИНАНИЕМ #{target['id']}</b>\n\n"
        f"📌 <b>Событие:</b> <code>{task_txt}</code>\n"
        f"📅 <b>Время события:</b> <b>{event_dt_str}</b>\n"
        f"🚨 <b>Время сигнала:</b> <b>{trigger_dt_str}</b>{adv_str}\n"
        f"⏳ <b>До сигнала:</b> <i>{rem_str}</i>\n"
        f"⚙️ <b>Статус:</b> {status_str}\n\n"
        f"💡 <i>Выберите действие ниже:</i>"
    )
    return text

def get_reminder_detail_markup(remind_id):
    return {
        "inline_keyboard": [
            [
                {"text": "⏱ Отложить на 15 мин", "callback_data": f"remind_snooze_15_{remind_id}"},
                {"text": "⏱ Отложить на 1 час", "callback_data": f"remind_snooze_60_{remind_id}"}
            ],
            [
                {"text": "🔔 Напомнить в начале", "callback_data": f"remind_at_event_{remind_id}"},
                {"text": "✅ Выполнено", "callback_data": f"remind_done_{remind_id}"}
            ],
            [
                {"text": "🗑 Удалить", "callback_data": f"remind_del_{remind_id}"},
                {"text": "« 🔙 К списку", "callback_data": "nav_remind"}
            ],
            [
                {"text": "🎛 В Главное Меню", "callback_data": "nav_main"}
            ]
        ]
    }

def check_and_get_triggered_reminders():
    """ Проверяет и возвращает наступившие напоминания для отправки аларма """
    reminders = load_reminders()
    now_ts = time.time()
    triggered = []
    
    for r in reminders:
        if r.get("status") == "pending" and r.get("target_timestamp", 0) <= now_ts:
            r["status"] = "triggered"
            triggered.append(r)
            
    if triggered:
        save_reminders(reminders)
        for r in triggered:
            task_title = r.get("text", "Задача")
            try:
                subprocess.Popen(["notify-send", "-u", "critical", "-a", "ИИ-ВЕКТОР", "⏰ НАПОМИНАНИЕ ВЕКТОР", task_title])
            except Exception:
                pass
            # Попытка воспроизвести звуковой сигнал аларма
            for sound_cmd in [
                ["paplay", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"],
                ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                ["canberra-gtk-play", "-i", "alarm-clock-elapsed"],
                ["spd-say", "-r", "10", f"Внимание. Напоминание: {task_title[:40]}"]
            ]:
                try:
                    if subprocess.run(["which", sound_cmd[0]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                        subprocess.Popen(sound_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        break
                except Exception:
                    pass
                
    return triggered

if __name__ == "__main__":
    init_reminders()
    print(get_reminders_dashboard_text())

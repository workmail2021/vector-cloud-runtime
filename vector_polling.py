#!/usr/bin/env python3
"""
Фоновый слушатель (Polling Daemon) для бота ВЕКТОР в Telegram.
Оснащен:
- Блокировкой одиночного экземпляра (Single Instance Lock via fcntl)
- 24/7 Фоновым стражем умных напоминаний (Reminders Watchdog Thread)
- Авто-переподключением при смене Wi-Fi и перезагрузке
"""

import sys
import os
import time
import json
import urllib.request
import urllib.parse
import urllib.error
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor
import http.client
import socket
import ssl
import fcntl
import threading
import html
from vector_bot import process_single_update, load_config, setup_bot_commands, AUTHORIZED_CHAT_ID
from reminders_module import check_and_get_triggered_reminders
from logger_engine import log_info, log_warning, log_error, get_recent_errors

LOCK_FILE = "/tmp/vector_bot.lock"

def acquire_single_instance_lock():
    lock_file_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_file_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file_fd.write(str(os.getpid()))
        lock_file_fd.flush()
        return lock_file_fd
    except IOError:
        print("⚠️ [ВЕКТОР] Экземпляр бота уже активен в системе (PID lock удержан). Завершение дублирующего процесса.")
        sys.exit(0)

def wait_for_network_connectivity(max_wait_seconds=60):
    """
    Ожидает готовности сетевого соединения после старта ПК,
    чтобы бот гарантированно подключился при загрузке системы.
    """
    start_t = time.time()
    print("📡 [ВЕКТОР] Проверка интернет-соединения...")
    while time.time() - start_t < max_wait_seconds:
        try:
            req = urllib.request.Request("https://api.telegram.org", headers={"User-Agent": "VectorBot/2.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                print("✅ [ВЕКТОР] Сеть активна, доступ к Telegram API подтвержден!")
                return True
        except Exception:
            time.sleep(2)
    print("⚠️ [ВЕКТОР] Сеть не ответила вовремя, запуск в фоновом режиме с авто-повтором.")
    return False

def reminders_watchdog_loop(token):
    """ Фоновый поток 24/7: проверяет наступление времени напоминаний и шлет срочные алармы """
    print("⏰ [ВЕКТОР] Фоновый страж напоминаний 24/7 активирован!")
    while True:
        try:
            triggered = check_and_get_triggered_reminders()
            if triggered:
                for r in triggered:
                    task = html.escape(r.get("text", "Без названия"))
                    dt = r.get("target_datetime", "")
                    ev_dt = r.get("event_datetime", dt)
                    adv = r.get("advance_desc", "")
                    r_id = r.get("id")
                    
                    if adv:
                        alert_text = (
                            f"🚨 <b>ВНИМАНИЕ! ЗАБЛАГОВРЕМЕННОЕ НАПОМИНАНИЕ ({adv})!</b> ⏰\n\n"
                            f"📌 <b>Событие:</b> <code>{task}</code>\n"
                            f"📅 <b>Начало:</b> <b>{ev_dt}</b> (<i>через {adv.replace('за ','')}</i>)\n\n"
                            f"💡 <i>Пора выезжать / готовиться! Выберите действие:</i>"
                        )
                        btn_rows = [
                            [
                                {"text": "🔔 Напомнить в начале", "callback_data": f"remind_at_event_{r_id}"},
                                {"text": "⏱ Отложить на 15 мин", "callback_data": f"remind_snooze_15_{r_id}"}
                            ],
                            [
                                {"text": "✅ Выполнено", "callback_data": f"remind_done_{r_id}"},
                                {"text": "🗑 Удалить", "callback_data": f"remind_del_{r_id}"}
                            ]
                        ]
                    else:
                        alert_text = (
                            f"🚨 <b>ВНИМАНИЕ! СРАБОТАЛО НАПОМИНАНИЕ!</b> ⏰\n\n"
                            f"📌 <b>Задача:</b> <code>{task}</code>\n"
                            f"📅 <b>Время:</b> <b>{dt}</b> (<i>прямо сейчас!</i>)\n\n"
                            f"💡 <i>Что сделать с напоминанием?</i>"
                        )
                        btn_rows = [
                            [
                                {"text": "⏱ Отложить на 15 мин", "callback_data": f"remind_snooze_15_{r_id}"},
                                {"text": "⏱ Отложить на 1 час", "callback_data": f"remind_snooze_60_{r_id}"}
                            ],
                            [
                                {"text": "✅ Выполнено", "callback_data": f"remind_done_{r_id}"},
                                {"text": "🗑 Удалить", "callback_data": f"remind_del_{r_id}"}
                            ]
                        ]
                    markup = {"inline_keyboard": btn_rows}
                    data = {
                        "chat_id": AUTHORIZED_CHAT_ID,
                        "text": alert_text,
                        "parse_mode": "HTML",
                        "reply_markup": json.dumps(markup)
                    }
                    post_data = urllib.parse.urlencode(data).encode("utf-8")
                    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=post_data)
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        pass
                    log_info("RemindersWatchdog", "trigger", f"Напоминание #{r_id} отправлено: {r.get('text')}")
                    print(f"⏰ [ВЕКТОР] Сработало напоминание #{r_id}: '{r.get('text')}' — аларм отправлен в Telegram!")
        except Exception as err:
            log_error("RemindersWatchdog", "reminders_watchdog_loop", f"Ошибка проверки напоминаний: {err}", exc=err)
        time.sleep(5)


def ai_model_health_watchdog_loop():
    """ Фоновый поток: периодически проверяет статус доступности модели OpenAI GPT-5 (каждые 15 минут) """
    time.sleep(10)
    while True:
        try:
            from chatgpt_engine import check_openai_api_health
            check_openai_api_health()
        except Exception:
            pass
        time.sleep(900)

def autonomous_scheduler_247():
    """
    Автономный планировщик задач 24/7:
    - Ежедневный отчет в 20:00 (daily_bot_audit)
    - Еженедельный аудит в Пн в 10:00 (weekly_bot_audit)
    - Автоматический мастер-бэкап каждые 12 часов (backup_all_project_data)
    - Авто-очистка мусора каждые 6 часов (pc_maintenance)
    """
    print("⏳ [ВЕКТОР] Автономный планировщик регулярных задач 24/7 запущен...")
    last_daily_date = ""
    last_weekly_week = ""
    last_backup_time = time.time()
    last_cleanup_time = time.time()
    last_yandex_check_time = time.time()
    last_chat_sort_slot = ''

    time.sleep(15) # Пауза при запуске

    while True:
        try:
            now = time.localtime()
            today_str = time.strftime("%Y-%m-%d", now)
            current_hour = now.tm_hour
            current_min = now.tm_min
            weekday = now.tm_wday # 0 = Понедельник
            week_str = f"{now.tm_year}-W{time.strftime('%V', now)}"

            # 1. Ежедневный тематический отчет (20:00)
            if current_hour == 20 and current_min >= 0 and today_str != last_daily_date:
                try:
                    from daily_bot_audit import generate_daily_topic_report
                    generate_daily_topic_report()
                    last_daily_date = today_str
                    log_info("AutonomousScheduler", "daily_report", f"Ежедневный отчет за {today_str} успешно сформирован и отправлен.")
                except Exception as e:
                    log_error("AutonomousScheduler", "daily_report", f"Ошибка отправки ежедневного отчета: {e}", exc=e)

            # 2. Еженедельный тематический аудит (Понедельник, 10:00)
            if weekday == 0 and current_hour == 10 and current_min >= 0 and week_str != last_weekly_week:
                try:
                    from weekly_bot_audit import generate_weekly_topic_report
                    generate_weekly_topic_report()
                    last_weekly_week = week_str
                    log_info("AutonomousScheduler", "weekly_audit", f"Еженедельный аудит за неделю {week_str} успешно сформирован.")
                except Exception as e:
                    log_error("AutonomousScheduler", "weekly_audit", f"Ошибка отправки еженедельного аудита: {e}", exc=e)

            # 3. Периодический мастер-бэкап (каждые 12 часов)
            if time.time() - last_backup_time >= 43200:
                try:
                    from backup_all_project_data import backup_all_data
                    backup_all_data()
                    last_backup_time = time.time()
                    log_info("AutonomousScheduler", "auto_backup", "Плановый мастер-бэкап успешно обновлен.")
                except Exception as e:
                    log_error("AutonomousScheduler", "auto_backup", f"Ошибка авто-бэкапа: {e}", exc=e)

            # 4. Периодическая очистка мусора ПК (каждые 6 часов)
            if time.time() - last_cleanup_time >= 21600:
                try:
                    from pc_maintenance import clean_system_junk
                    cleaned = clean_system_junk()
                    last_cleanup_time = time.time()
                    log_info("AutonomousScheduler", "auto_cleanup", f"Плановая очистка ПК выполнена ({cleaned} файлов очищено).")
                except Exception as e:
                    log_error("AutonomousScheduler", "auto_cleanup", f"Ошибка очистки мусора: {e}", exc=e)

            # 5. Ежедневный фоновый мониторинг отзывов на Яндекс.Картах (каждые 12-24 часа)
            if time.time() - last_yandex_check_time >= 43200:
                try:
                    from yandex_maps_guard import check_and_record_new_yandex_reviews
                    check_and_record_new_yandex_reviews()
                    last_yandex_check_time = time.time()
                    log_info("AutonomousScheduler", "yandex_reviews", "Плановый мониторинг отзывов Яндекс.Карт выполнен.")
                except Exception as e:
                    log_error("AutonomousScheduler", "yandex_reviews", f"Ошибка проверки отзывов Яндекс.Карт: {e}", exc=e)

            # 6. Автоматический разбор и зачистка чата Telegram (2 раза в день: в 10:00 и в 20:00)
            if current_hour in [10, 20] and current_min >= 0 and f"{today_str}_{current_hour}" != last_chat_sort_slot:
                try:
                    from auto_chat_cleaner_and_sorter import run_chat_sort_and_cleanup
                    run_chat_sort_and_cleanup()
                    last_chat_sort_slot = f"{today_str}_{current_hour}"
                    log_info("AutonomousScheduler", "chat_sort_cleanup", f"Плановый авторазбор и зачистка чата выполнены ({last_chat_sort_slot}).")
                except Exception as e:
                    log_error("AutonomousScheduler", "chat_sort_cleanup", f"Ошибка авто-разбора чата: {e}", exc=e)

        except Exception as sched_err:
            log_error("AutonomousScheduler", "loop", f"Ошибка цикла планировщика: {sched_err}", exc=sched_err)

        time.sleep(30)

def main_polling_loop():
    lock_fd = acquire_single_instance_lock()
    config = load_config()
    token = config.get("telegram_bot_token")
    offset = None

    if not token:
        print("Ошибка: Токен Telegram не найден в конфигурации.")
        return

    # Запуск фонового стража напоминаний
    t = threading.Thread(target=reminders_watchdog_loop, args=(token,), daemon=True)
    t.start()

    # Запуск фонового стража доступности ИИ-моделей (GPT-5 / Gemini)
    t_ai = threading.Thread(target=ai_model_health_watchdog_loop, daemon=True)
    t_ai.start()

    # Запуск автономного планировщика регулярных задач 24/7
    t_sched = threading.Thread(target=autonomous_scheduler_247, daemon=True)
    t_sched.start()

    # Пул параллельных воркеров для мгновенной обработки кликов и сообщений
    executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="VectorWorker")

    # Высокоскоростная сессия с Keep-Alive для Long Polling
    poll_session = requests.Session()
    adapter = HTTPAdapter(pool_connections=15, pool_maxsize=25, max_retries=Retry(total=2, backoff_factor=0.1))
    poll_session.mount("https://", adapter)
    poll_session.mount("http://", adapter)

    print("⚡️ [ВЕКТОР] Бот запущен на Turbo Keep-Alive движке (Параллельные воркеры активны) 24/7...")

    def _worker_process_update(up):
        up_id = up.get("update_id", 0)
        try:
            process_single_update(up)
        except Exception as up_err:
            log_error("VectorPolling", "process_single_update", f"Ошибка обработки update_id={up_id}: {up_err}", exc=up_err)
            send_emergency_recovery_response(up, up_err)

    while True:
        try:
            params = {"timeout": 20}
            if offset:
                params["offset"] = offset

            url = f"https://api.telegram.org/bot{token}/getUpdates"
            resp = poll_session.get(url, params=params, timeout=25)
            if resp.status_code == 200:
                res = resp.json()
                if res.get("ok") and res.get("result"):
                    for update in res["result"]:
                        update_id = update["update_id"]
                        offset = update_id + 1
                        executor.submit(_worker_process_update, update)

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, socket.timeout, ConnectionResetError) as net_e:
            time.sleep(0.1)
        except Exception as e:
            err_str = str(e).lower()
            if "timed out" not in err_str and "temporary failure" not in err_str and "handshake" not in err_str:
                log_error("VectorPolling", "main_polling_loop", f"Ошибка в цикле опроса: {e}", exc=e)
            time.sleep(1)

if __name__ == "__main__":
    main_polling_loop()

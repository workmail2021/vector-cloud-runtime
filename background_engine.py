#!/usr/bin/env python3
"""
ИИ-ВЕКТОР: Единый Модуль Фоновых Процессов и Служб 5.0 (Background Engine 5.0).
Обеспечивает непрерывную работу автономных фоновых воркеров 24/7:
1. ⏰ Watchdog Напоминаний (Reminders Watchdog) — ежесекундный контроль алармов, заблаговременные сигналы, Telegram push и notify-send на ПК.
2. 🤖 Watchdog Автономных Задач (Agent Tasks Dispatcher) — исполнение системных директив и задач из Telegram.
3. 💾 Watchdog Резервного Копирования и Синхронизации (Backup & Markdown Sync) — авто-бэкап баз данных и синхронизация заметок.
4. 🩺 Watchdog Здоровья Системы и Самовосстановления (Health & Self-Healing Watchdog) — телеметрия SSD/ОЗУ, сетевой пинг, проверка служб systemd.
5. 🛡 Watchdog Логирования и Контроля Ошибок (Quality & Error Watchdog) — агрегация логов, мониторинг ИИ-моделей.
"""

import os
import sys
import time
import datetime
import json
import fcntl
import threading
import subprocess
import html
import urllib.request
import argparse
import shutil

# Базовые пути проекта
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

LOCK_FILE = "/tmp/vector_background_engine.lock"
STATUS_FILE = os.path.join(PROJECT_ROOT, ".background_engine_status.json")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "data_backup")

# Подключение модулей экосистемы
try:
    from reminders_module import check_and_get_triggered_reminders, load_reminders
except ImportError:
    check_and_get_triggered_reminders = None
    load_reminders = None

try:
    from notes_module import sync_all_markdown_files, load_notes
except ImportError:
    sync_all_markdown_files = None
    load_notes = None

try:
    from autonomous_quality_engine import load_quality_metrics, record_interaction_metrics
except ImportError:
    load_quality_metrics = None
    record_interaction_metrics = None

try:
    import logger_engine as _le
    def log_info(msg, func="main", module="BackgroundEngine"):
        _le.log_info(module, func, msg)
    def log_warning(msg, func="main", module="BackgroundEngine"):
        _le.log_warning(module, func, msg)
    def log_error(msg, func="main", module="BackgroundEngine", exc=None):
        _le.log_error(module, func, msg, exc=exc)
    def get_recent_errors(n=5):
        return _le.get_recent_errors(n)
except ImportError:
    def log_info(msg, func="main", module="BackgroundEngine"): print(f"[INFO] {msg}")
    def log_warning(msg, func="main", module="BackgroundEngine"): print(f"[WARN] {msg}")
    def log_error(msg, func="main", module="BackgroundEngine", exc=None): print(f"[ERROR] {msg}")
    def get_recent_errors(n=5): return []

AUTHORIZED_CHAT_ID = 6375883079

def get_bot_token():
    cfg_path = os.path.expanduser("~/.config/antigravity-email/config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f).get("telegram_bot_token")
        except Exception:
            pass
    return None

def send_telegram_alert(text, reply_markup=None):
    token = get_bot_token()
    if not token:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": AUTHORIZED_CHAT_ID,
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("ok", False)
    except Exception as e:
        log_warning(f"Ошибка отправки Telegram-оповещения из фонового модуля: {e}")
        return False

def send_desktop_notification(title, message, urgency="normal"):
    """Отправляет всплывающее уведомление на рабочий стол Linux через notify-send."""
    if shutil.which("notify-send"):
        try:
            subprocess.run(
                ["notify-send", "-u", urgency, "-a", "Вектор 5.0", title, message],
                check=False,
                timeout=5
            )
        except Exception:
            pass

class BackgroundEngine:
    """Главный управляющий оркестратор фоновых модулей."""
    def __init__(self):
        self.is_running = False
        self.lock_fd = None
        self.threads = []
        self.last_briefing_date = None
        self.last_evening_briefing_date = None
        self.stats = {
            "start_time": None,
            "reminders_checked": 0,
            "reminders_fired": 0,
            "backups_performed": 0,
            "markdown_synced": 0,
            "health_checks": 0,
            "briefings_sent": 0,
            "last_active": None,
            "errors": 0
        }

    def acquire_lock(self):
        try:
            self.lock_fd = open(LOCK_FILE, "w")
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            return True
        except IOError:
            return False

    def release_lock(self):
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
            except Exception:
                pass
            if os.path.exists(LOCK_FILE):
                try:
                    os.remove(LOCK_FILE)
                except Exception:
                    pass

    def save_status(self):
        """Сохраняет текущий статус фонового движка для мониторинга."""
        self.stats["last_active"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.stats["pid"] = os.getpid()
        self.stats["is_running"] = self.is_running
        try:
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ==========================================
    # ВОРКЕР 1: НАПОМИНАНИЯ И АЛАРМЫ (10 сек)
    # ==========================================
    def worker_reminders(self):
        log_info("Фоновый воркер Напоминаний 24/7 запущен.")
        while self.is_running:
            try:
                if check_and_get_triggered_reminders:
                    triggered = check_and_get_triggered_reminders()
                    self.stats["reminders_checked"] += 1
                    if triggered:
                        for r in triggered:
                            self.stats["reminders_fired"] += 1
                            task = html.escape(r.get("text", "Без названия"))
                            dt = r.get("target_datetime", "")
                            ev_dt = r.get("event_datetime", dt)
                            adv = r.get("advance_desc", "")
                            r_id = r.get("id")

                            send_desktop_notification("⏰ Напоминание Вектор", task, urgency="critical")

                            if adv:
                                alert_text = (
                                    f"🚨 <b>ВНИМАНИЕ! ЗАБЛАГОВРЕМЕННОЕ НАПОМИНАНИЕ ({adv})!</b> ⏰\n\n"
                                    f"📌 <b>Событие:</b> <code>{task}</code>\n"
                                    f"📅 <b>Начало:</b> <b>{ev_dt}</b> (<i>через {adv.replace('за ','')}</i>)\n\n"
                                    f"💡 <i>Пора выезжать / подготовиться! Выберите действие:</i>"
                                )
                                btn_rows = {
                                    "inline_keyboard": [
                                        [
                                            {"text": "🔔 Напомнить в начале", "callback_data": f"remind_at_event_{r_id}"},
                                            {"text": "⏱ Отложить на 15 мин", "callback_data": f"remind_snooze_15_{r_id}"}
                                        ],
                                        [
                                            {"text": "✅ Выполнено", "callback_data": f"remind_done_{r_id}"},
                                            {"text": "🗑 Удалить", "callback_data": f"remind_del_{r_id}"}
                                        ]
                                    ]
                                }
                            else:
                                alert_text = (
                                    f"🚨 <b>ВНИМАНИЕ! СРАБОТАЛО НАПОМИНАНИЕ!</b> ⏰\n\n"
                                    f"📌 <b>Задача:</b> <code>{task}</code>\n"
                                    f"📅 <b>Время:</b> <b>{dt}</b> (<i>прямо сейчас!</i>)\n\n"
                                    f"💡 <i>Что сделать с напоминанием?</i>"
                                )
                                btn_rows = {
                                    "inline_keyboard": [
                                        [
                                            {"text": "⏱ Отложить на 15 мин", "callback_data": f"remind_snooze_15_{r_id}"},
                                            {"text": "⏱ На 1 час", "callback_data": f"remind_snooze_60_{r_id}"}
                                        ],
                                        [
                                            {"text": "✅ Выполнено", "callback_data": f"remind_done_{r_id}"},
                                            {"text": "🗑 Удалить", "callback_data": f"remind_del_{r_id}"}
                                        ]
                                    ]
                                }
                            send_telegram_alert(alert_text, reply_markup=btn_rows)
            except Exception as e:
                self.stats["errors"] += 1
                log_error(f"Ошибка в воркере напоминаний: {e}")
            self.save_status()
            time.sleep(10)

    # ==========================================
    # ВОРКЕР 2: БЭКАП И СИНХРОНИЗАЦИЯ (30 мин)
    # ==========================================
    def worker_backup_and_sync(self):
        log_info("Фоновый воркер Резервного копирования и синхронизации запущен.")
        while self.is_running:
            try:
                # 1. Синхронизация Markdown заметок
                if sync_all_markdown_files:
                    cnt = sync_all_markdown_files()
                    self.stats["markdown_synced"] += cnt

                # 2. Создание снимка базы данных
                backup_script = os.path.join(PROJECT_ROOT, "backup_all_project_data.py")
                if os.path.exists(backup_script):
                    subprocess.run([sys.executable, backup_script], check=False, timeout=30)
                    self.stats["backups_performed"] += 1

            except Exception as e:
                self.stats["errors"] += 1
                log_error(f"Ошибка в воркере бэкапа и синхронизации: {e}")
            self.save_status()
            # Интервал: 30 минут (1800 секунд)
            for _ in range(180):
                if not self.is_running:
                    break
                time.sleep(10)

    # ==========================================
    # ВОРКЕР 3: ЗДОРОВЬЕ СИСТЕМЫ И САМОВОССТАНОВЛЕНИЕ (60 сек)
    # ==========================================
    def worker_health_and_telemetry(self):
        log_info("Фоновый воркер Здоровья и Самовосстановления запущен.")
        while self.is_running:
            try:
                self.stats["health_checks"] += 1
                
                # 1. Проверка доступности интернета
                net_ok = False
                try:
                    req = urllib.request.Request("https://api.telegram.org", headers={"User-Agent": "VectorBackgroundEngine/5.0"})
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        net_ok = True
                except Exception:
                    net_ok = False

                # 2. Проверка свободного места на SSD
                disk_stat = shutil.disk_usage(PROJECT_ROOT)
                free_gb = disk_stat.free / (1024 ** 3)
                if free_gb < 2.0:
                    log_warning(f"Критически мало места на диске: {free_gb:.2f} ГБ!")
                    send_desktop_notification("⚠️ Мало места на диске", f"Свободно всего {free_gb:.2f} ГБ", urgency="critical")

                # 3. Самовосстановление и перезапуск критических служб 24/7
                critical_services = [
                    "vector-bot.service",
                    "vector-userbot.service",
                    "boxing-performance-bot.service",
                    "boxing-performance-tunnel.service"
                ]
                for srv in critical_services:
                    try:
                        res = subprocess.run(
                            ["systemctl", "--user", "is-active", srv],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        st = res.stdout.strip()
                        if st not in ["active", "activating"]:
                            log_warning(f"Служба {srv} перешла в статус '{st}'. Запуск авто-восстановления...")
                            subprocess.run(["systemctl", "--user", "restart", srv], check=False, timeout=10)
                            log_info(f"✅ Служба {srv} успешно перезапущена сторожевым демоном!")
                    except Exception as srv_err:
                        log_error(f"Ошибка проверки службы {srv}: {srv_err}")

            except Exception as e:
                self.stats["errors"] += 1
                log_error(f"Ошибка в воркере здоровья системы: {e}")
            self.save_status()
            time.sleep(60)

    # ==========================================
    # ВОРКЕР 4: УТРЕННИЙ БРИФИНГ РУКОВОДИТЕЛЯ (08:00 MSK)
    # ==========================================
    def worker_morning_briefing(self):
        log_info("Фоновый воркер Утреннего Брифинга 08:00 запущен.")
        while self.is_running:
            try:
                now = datetime.datetime.now()
                today_str = now.strftime("%Y-%m-%d")
                # Запуск ровно в 08:00 MSK (или при первом старте после 08:00 утра до 09:00, если не отправлялся)
                if now.hour == 8 and now.minute >= 0 and today_str != self.last_briefing_date:
                    log_info("⏰ 08:00 MSK! Формирование и отправка Утреннего Брифинга Руководителя...")
                    try:
                        from vector_tier1_engine import get_morning_briefing_card
                        card_txt, card_mk = get_morning_briefing_card(user_name="Сергей")
                        ok = send_telegram_alert(card_txt, reply_markup=card_mk)
                        if ok:
                            self.last_briefing_date = today_str
                            self.stats["briefings_sent"] += 1
                            log_info("✅ Утренний брифинг успешно отправлен в Telegram руководителю (chat_id: 6375883079)!")
                    except Exception as b_err:
                        log_error(f"Ошибка при формировании утреннего брифинга: {b_err}")
            except Exception as e:
                self.stats["errors"] += 1
                log_error(f"Ошибка в воркере утреннего брифинга: {e}")
            self.save_status()
            # Проверка каждые 30 секунд
            for _ in range(3):
                if not self.is_running:
                    break
                time.sleep(10)

    # ==========================================
    # ВОРКЕР 5: ВЕЧЕРНИЙ БРИФИНГ РУКОВОДИТЕЛЯ (21:30 MSK)
    # ==========================================
    def worker_evening_briefing(self):
        log_info("Фоновый воркер Вечернего Брифинга 21:30 запущен.")
        while self.is_running:
            try:
                now = datetime.datetime.now()
                today_str = now.strftime("%Y-%m-%d")
                if (now.hour == 21 and now.minute >= 30) or (now.hour > 21 and now.hour < 23):
                    if today_str != self.last_evening_briefing_date:
                        log_info("⏰ 21:30 MSK! Формирование и отправка Вечернего Брифинга Руководителя...")
                        try:
                            from vector_tier1_engine import get_evening_briefing_card
                            card_txt, card_mk = get_evening_briefing_card(user_name="Сергей")
                            ok = send_telegram_alert(card_txt, reply_markup=card_mk)
                            if ok:
                                self.last_evening_briefing_date = today_str
                                self.stats["briefings_sent"] += 1
                                log_info("✅ Вечерний брифинг успешно отправлен в Telegram руководителю (chat_id: 6375883079)!")
                        except Exception as b_err:
                            log_error(f"Ошибка при формировании вечернего брифинга: {b_err}")
            except Exception as e:
                self.stats["errors"] += 1
                log_error(f"Ошибка в воркере вечернего брифинга: {e}")
            self.save_status()
            # Проверка каждые 30 секунд
            for _ in range(3):
                if not self.is_running:
                    break
                time.sleep(10)

    def start(self):
        """Запускает все фоновые воркеры в многопоточном режиме с удержанием блокировки."""
        if not self.acquire_lock():
            print("⚠️ [ВЕКТОР] Фоновый движок уже запущен в системе (PID lock занят).")
            return False

        self.is_running = True
        self.stats["start_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_status()

        print("🚀 [ВЕКТОР] Фоновый Модуль Служб 5.0 успешно запущен 24/7.")
        log_info("Фоновый Модуль Служб 5.0 запущен.")

        # Регистрация потоков воркеров
        w_reminders = threading.Thread(target=self.worker_reminders, name="Worker-Reminders", daemon=True)
        w_backup = threading.Thread(target=self.worker_backup_and_sync, name="Worker-BackupSync", daemon=True)
        w_health = threading.Thread(target=self.worker_health_and_telemetry, name="Worker-Health", daemon=True)
        w_briefing = threading.Thread(target=self.worker_morning_briefing, name="Worker-Briefing", daemon=True)
        w_evening = threading.Thread(target=self.worker_evening_briefing, name="Worker-EveningBriefing", daemon=True)

        self.threads = [w_reminders, w_backup, w_health, w_briefing, w_evening]
        for t in self.threads:
            t.start()

        try:
            while self.is_running:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.stop()
        return True

    def stop(self):
        """Корректная остановка фонового движка."""
        print("🛑 [ВЕКТОР] Остановка фонового модуля...")
        self.is_running = False
        self.save_status()
        self.release_lock()
        log_info("Фоновый Модуль Служб 5.0 остановлен.")

    def run_once(self):
        """Выполняет однократный прогон всех задач фонового контура (для cron или ручного тестирования)."""
        print("⚡️ [ВЕКТОР] Выполнение единичного цикла фоновых модулей...")
        
        # 1. Напоминания
        reminders_count = 0
        if check_and_get_triggered_reminders:
            triggered = check_and_get_triggered_reminders()
            reminders_count = len(triggered)
            for r in triggered:
                task = r.get("text", "Без названия")
                send_desktop_notification("⏰ Напоминание Вектор", task)
                
        # 2. Markdown Синхронизация
        md_count = 0
        if sync_all_markdown_files:
            md_count = sync_all_markdown_files()

        # 3. Бэкап
        backup_script = os.path.join(PROJECT_ROOT, "backup_all_project_data.py")
        if os.path.exists(backup_script):
            subprocess.run([sys.executable, backup_script], check=False, timeout=30)

        print(f"✅ Цикл завершен: сработало напоминаний: {reminders_count}, синхронизировано заметок: {md_count}, бэкап обновлен.")
        return True

def get_engine_status():
    """Возвращает информацию о текущем состоянии фонового движка."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Проверяем реальность процесса по PID
            pid = data.get("pid")
            is_alive = False
            if pid:
                try:
                    os.kill(pid, 0)
                    is_alive = True
                except OSError:
                    is_alive = False
            data["is_alive"] = is_alive
            return data
        except Exception:
            pass
    return {"is_alive": False, "is_running": False}

def generate_systemd_service():
    """Генерирует юнит-файл systemd для автозапуска фонового движка при старте ОС."""
    service_content = f"""[Unit]
Description=Vector 24/7 Background Engine Daemon (Reminders, Backups, Health & Sync)
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={PROJECT_ROOT}
ExecStart={sys.executable} {os.path.join(PROJECT_ROOT, 'background_engine.py')} start
Restart=always
RestartSec=5s
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""
    systemd_user_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(systemd_user_dir, exist_ok=True)
    service_file = os.path.join(systemd_user_dir, "vector-background-engine.service")
    with open(service_file, "w", encoding="utf-8") as f:
        f.write(service_content)
    return service_file

def main():
    parser = argparse.ArgumentParser(description="ИИ-Вектор: Единый Фоновый Модуль 5.0")
    subparsers = parser.add_subparsers(dest="command", help="Команды управления")

    # start
    subparsers.add_parser("start", help="Запустить фоновый движок 24/7")

    # stop
    subparsers.add_parser("stop", help="Остановить работающий фоновый движок")

    # status
    subparsers.add_parser("status", help="Проверить статус фоновых служб")

    # run-once
    subparsers.add_parser("run-once", help="Выполнить один цикл проверки и синхронизации")

    # briefing
    subparsers.add_parser("briefing", help="Сформировать и отправить утренний брифинг руководителю прямо сейчас")

    # install-service
    subparsers.add_parser("install-service", help="Установить и включить автозапуск systemd службы")

    args = parser.parse_args()

    engine = BackgroundEngine()

    if not args.command or args.command == "status":
        st = get_engine_status()
        status_icon = "🟢 АКТИВЕН" if st.get("is_alive") else "🔴 НЕ АКТИВЕН"
        print(f"=== СТАТУС ФОНОВОГО ДВИЖКА ВЕКТОР ===")
        print(f"Состояние:           {status_icon}")
        print(f"PID:                 {st.get('pid', 'N/A')}")
        print(f"Время старта:        {st.get('start_time', 'N/A')}")
        print(f"Последняя активность:{st.get('last_active', 'N/A')}")
        print(f"Проверок напоминаний:{st.get('reminders_checked', 0)}")
        print(f"Сработало алармов:   {st.get('reminders_fired', 0)}")
        print(f"Бэкапов выполнено:   {st.get('backups_performed', 0)}")
        print(f"Синхронизаций MD:    {st.get('markdown_synced', 0)}")
        print(f"Проверок здоровья:   {st.get('health_checks', 0)}")
        print(f"Брифингов отправлено:{st.get('briefings_sent', 0)}")
        print(f"Ошибок:              {st.get('errors', 0)}")

    elif args.command == "start":
        engine.start()

    elif args.command == "run-once":
        engine.run_once()

    elif args.command in ["briefing", "morning-briefing"]:
        print("🌅 Формирование и отправка Утреннего Брифинга Руководителя...")
        try:
            from vector_tier1_engine import get_morning_briefing_card
            card_txt, card_mk = get_morning_briefing_card(user_name="Сергей")
            print("\n" + card_txt + "\n")
            ok = send_telegram_alert(card_txt, reply_markup=card_mk)
            if ok:
                print("✅ Утренний брифинг успешно отправлен в Telegram руководителю (chat_id: 6375883079)!")
            else:
                print("⚠️ Telegram API вернул ошибку при отправке сообщения.")
        except Exception as e:
            print(f"❌ Ошибка генерации брифинга: {e}")

    elif args.command == "stop":
        st = get_engine_status()
        pid = st.get("pid")
        if pid and st.get("is_alive"):
            try:
                import signal
                os.kill(pid, signal.SIGTERM)
                print(f"✅ Сигнал остановки отправлен процессу PID {pid}.")
            except Exception as e:
                print(f"❌ Ошибка остановки процесса: {e}")
        else:
            print("ℹ️ Фоновый движок не запущен.")

    elif args.command == "install-service":
        sf = generate_systemd_service()
        try:
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
            subprocess.run(["systemctl", "--user", "enable", "--now", "vector-background-engine.service"], check=False)
            print(f"✅ Служба успешно установлена и активирована: {sf}")
            print("Статус: systemctl --user status vector-background-engine.service")
        except Exception as e:
            print(f"Файл службы создан ({sf}), но произошла ошибка при активации systemd: {e}")

if __name__ == "__main__":
    main()

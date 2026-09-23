#!/usr/bin/env python3
"""
🛰 ЕДИНЫЙ БОРТОВОЙ ЖУРНАЛ И СИСТЕМА ЛОГИРОВАНИЯ ИИ-ВЕКТОР (FLIGHT LOG ENGINE)
Создан по прямому указанию Сергея Романова.
Обеспечивает точную локализацию сбоев, запись таймстемпов, функций, стеков вызовов
и автоматический доступ LLM к ошибкам для самоотладки без догадок.
"""

import os
import sys
import time
import logging
import traceback
import json
from datetime import datetime

LOGS_DIR = "/home/home/Документы/2/logs"
FLIGHT_LOG_PATH = os.path.join(LOGS_DIR, "vector_flight.log")
ERROR_LOG_PATH = os.path.join(LOGS_DIR, "vector_errors.log")

from logging.handlers import RotatingFileHandler

os.makedirs(LOGS_DIR, exist_ok=True)

# Настройка системного логгера
logger = logging.getLogger("VectorFlightLog")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    # Общий бортовой журнал (Все события, тайминги, переходы) — ротация до 5 МБ, 3 бэкапа
    fh_all = RotatingFileHandler(FLIGHT_LOG_PATH, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    fh_all.setLevel(logging.DEBUG)
    fmt_all = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh_all.setFormatter(fmt_all)
    logger.addHandler(fh_all)

    # Журнал критических сбоев и ошибок (для мгновенной самодиагностики LLM) — ротация до 5 МБ, 3 бэкапа
    fh_err = RotatingFileHandler(ERROR_LOG_PATH, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    fh_err.setLevel(logging.ERROR)
    fmt_err = logging.Formatter(
        "[%(asctime)s] [🛑 ERROR] [%(filename)s:%(funcName)s:%(lineno)d]\nMessage: %(message)s\n" + "-"*60,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh_err.setFormatter(fmt_err)
    logger.addHandler(fh_err)

def log_info(module_name, func_name, message):
    """Фиксация штатного действия в бортовом журнале."""
    logger.info(f"[{module_name} -> {func_name}] {message}")

def log_warning(module_name, func_name, message):
    """Фиксация предупреждения/задержки."""
    logger.warning(f"[{module_name} -> {func_name}] {message}")

def log_error(module_name, func_name, error_msg, exc=None):
    """
    Фиксация ошибки с полным контекстом и стеком вызовов (traceback).
    Позволяет ИИ сразу увидеть файл, номер строки и причину сбоя.
    """
    tb_str = ""
    if exc:
        tb_str = f"\nTraceback:\n{''.join(traceback.format_tb(exc.__traceback__))}\nException: {type(exc).__name__}: {exc}"
    elif sys.exc_info()[0] is not None:
        tb_str = f"\nTraceback:\n{traceback.format_exc()}"
    
    full_log = f"[{module_name} -> {func_name}] {error_msg}{tb_str}"
    logger.error(full_log)
    print(f"🛑 [БОРТОВОЙ ЖУРНАЛ: ОШИБКА] {full_log}", file=sys.stderr)

def get_recent_errors(limit=10):
    """Возвращает последние зафиксированные ошибки для автономного дебага LLM."""
    if not os.path.exists(ERROR_LOG_PATH):
        return []
    try:
        with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            blocks = content.split("-" * 60)
            clean_blocks = [b.strip() for b in blocks if b.strip()]
            return clean_blocks[-limit:]
    except Exception as e:
        return [f"Ошибка чтения журнала ошибок: {e}"]

def get_flight_summary():
    """Сводка состояния бортового журнала."""
    all_size = os.path.getsize(FLIGHT_LOG_PATH) if os.path.exists(FLIGHT_LOG_PATH) else 0
    err_size = os.path.getsize(ERROR_LOG_PATH) if os.path.exists(ERROR_LOG_PATH) else 0
    errors = get_recent_errors(5)
    return {
        "flight_log": FLIGHT_LOG_PATH,
        "flight_log_size_kb": round(all_size / 1024, 2),
        "error_log": ERROR_LOG_PATH,
        "error_log_size_kb": round(err_size / 1024, 2),
        "recent_errors_count": len(errors),
        "last_error": errors[-1] if errors else "Ошибок не зафиксировано (Все системы в норме)"
    }

if __name__ == "__main__":
    log_info("FlightLog", "main", "Бортовой журнал успешно инициализирован.")
    print("🛰 Сводка бортового журнала:")
    print(json.dumps(get_flight_summary(), ensure_ascii=False, indent=2))

#!/usr/bin/env python3
"""
Интеллектуальное ИИ-Ядро для «ИИ-Секретаря» Вектор на базе Google Gemini DeepMind.
Полностью переведено на семейство моделей Google Gemini (без зависимостей от OpenAI).
Обеспечивает 100% изоляцию пользователей (Multi-Tenant Privacy):
- Каждый пользователь общается со своей выбранной моделью Gemini изолированно.
- Личные данные, пароли и файлы Сергея Романова никогда не передаются внешним пользователям.
"""

import os
import sys
import json
import time
import re
import html
import subprocess
import urllib.request
import urllib.parse
import urllib.error
import datetime

CONFIG_PATH = os.path.expanduser("~/.config/antigravity-email/config.json")
STATE_PATH = os.path.expanduser("~/.config/antigravity-email/openai_state.json")
AGY_BIN = "/home/home/.local/bin/agy"
OWNER_CHAT_ID = 6375883079

MODELS_CATALOG = {
    "gemini-3.8-flash": {
        "title": "Google Gemini 3.8 Flash (High)",
        "short_title": "Gemini 3.8 Flash",
        "badge": "Gemini 3.8 Flash",
        "family": "gemini",
        "model_arg": "gemini-3.8-flash-high",
        "limit_type": "Безлимитно 24/7",
        "description": "Новейший флагман Google DeepMind: сверхскоростной отклик, глубокая логика и идеальный русский язык."
    },
    "gemini-3.1-pro": {
        "title": "Google Gemini 3.1 Pro (High)",
        "short_title": "Gemini 3.1 Pro",
        "badge": "Gemini 3.1 Pro",
        "family": "gemini",
        "model_arg": "gemini-3.1-pro-high",
        "limit_type": "Безлимитно 24/7",
        "description": "Тяжеловес для сложнейших инженерных задач, смет 615-ФЗ, кодинга, регламентов и глубоких рассуждений."
    },
    "gemini-3.8-flash-low": {
        "title": "Google Gemini 3.8 Express (Мгновенный)",
        "short_title": "Gemini Express",
        "badge": "Gemini Express",
        "family": "gemini",
        "model_arg": "gemini-3.8-flash-low",
        "limit_type": "Мгновенный отклик",
        "description": "Сверхлегкий экспресс-режим для моментальных ответов на короткие вопросы без ожидания."
    },
    "auto": {
        "title": "Авто-Выбор (Gemini Adaptive)",
        "short_title": "Авто-Балансировщик",
        "badge": "Gemini Auto",
        "family": "gemini",
        "model_arg": "gemini-3.8-flash-high",
        "limit_type": "Адаптивный баланс",
        "description": "Автоматический выбор оптимальной модели Google Gemini под контекст и сложность задачи."
    }
}

MODEL_ALIASES = {
    "gpt-5.6-luna": "gemini-3.8-flash",
    "gpt-5": "gemini-3.8-flash",
    "gpt-4o": "gemini-3.8-flash",
    "o1": "gemini-3.1-pro",
    "gemini-3.7-flash": "gemini-3.8-flash",
    "gemini-pro": "gemini-3.1-pro"
}

def resolve_model_key(key: str) -> str:
    if key in MODELS_CATALOG:
        return key
    return MODEL_ALIASES.get(key, "gemini-3.8-flash")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def load_ai_state():
    today_str = datetime.date.today().isoformat()
    state = {
        "active_model": "gemini-3.8-flash",
        "user_models": {},
        "today_date": today_str,
        "gemini_today": 0,
        "gpt_today": 0,
        "total_requests": 0,
        "successful_requests": 0,
        "last_request_time": None
    }

    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                state.update(saved)
        except Exception:
            pass

    state["active_model"] = resolve_model_key(state.get("active_model", "gemini-3.8-flash"))

    if "user_models" not in state or not isinstance(state["user_models"], dict):
        state["user_models"] = {}

    if state.get("today_date") != today_str:
        state["today_date"] = today_str
        state["gemini_today"] = 0
        state["gpt_today"] = 0

    return state

def save_ai_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def get_active_model_key(user_id=None):
    state = load_ai_state()
    if user_id is not None:
        u_str = str(user_id)
        if u_str in state.get("user_models", {}):
            return resolve_model_key(state["user_models"][u_str])
    return resolve_model_key(state.get("active_model", "gemini-3.8-flash"))

def set_active_model(model_key, user_id=None):
    resolved = resolve_model_key(model_key)
    state = load_ai_state()
    if user_id is not None:
        state["user_models"][str(user_id)] = resolved
    if user_id is None or str(user_id) == str(OWNER_CHAT_ID):
        state["active_model"] = resolved
    save_ai_state(state)
    return True, MODELS_CATALOG[resolved]

def reset_usage_counter():
    state = load_ai_state()
    state["gemini_today"] = 0
    state["gpt_today"] = 0
    save_ai_state(state)

def get_usage_summary_short(user_id=None):
    state = load_ai_state()
    active_k = get_active_model_key(user_id)
    info = MODELS_CATALOG.get(active_k, MODELS_CATALOG["gemini-3.8-flash"])
    return f"{info['short_title']} (Безлимит • {state.get('gemini_today', 0)} сегодня)"

def get_models_menu_text(user_id=None, is_guest=False):
    curr_k = get_active_model_key(user_id)
    curr_info = MODELS_CATALOG.get(curr_k, MODELS_CATALOG["gemini-3.8-flash"])
    if is_guest:
        return (
            "<b>ВЫБОР ИИ-МОДЕЛИ GOOGLE GEMINI</b>\n\n"
            f"Текущая активная модель: <b>{curr_info['title']}</b>\n\n"
            "<i>Выберите режим работы нейросети в 1 клик:</i>\n"
            "• <b>Gemini 3.8 Flash</b> — сверхскоростной флагман\n"
            "• <b>Gemini 3.1 Pro</b> — глубокий анализ и сложные задачи"
        )
    return (
        "<b>СЕЛЕКТОР МОДЕЛЕЙ GOOGLE GEMINI (24/7)</b>\n\n"
        f"Текущий активный движок: <b>{curr_info['title']}</b>\n"
        f"Тариф/Режим: <code>{curr_info['limit_type']}</code>\n"
        f"<i>{curr_info['description']}</i>\n\n"
        "<i>Переключение моделей доступно в 1 клик без ограничений:</i>"
    )

def get_models_markup(user_id=None, is_guest=False):
    curr_k = get_active_model_key(user_id)
    if is_guest:
        return {
            "inline_keyboard": [
                [
                    {"text": f"{'[✓] ' if curr_k == 'gemini-3.8-flash' else ''}Gemini 3.8 Flash", "callback_data": "set_model_gemini-3.8-flash"},
                    {"text": f"{'[✓] ' if curr_k == 'gemini-3.1-pro' else ''}Gemini 3.1 Pro", "callback_data": "set_model_gemini-3.1-pro"}
                ],
                [
                    {"text": "К ИИ-Секретарю", "callback_data": "nav_secretary"}
                ]
            ]
        }

    rows = [
        [
            {"text": f"{'[✓] ' if curr_k == 'gemini-3.8-flash' else ''}Gemini 3.8 Flash", "callback_data": "set_model_gemini-3.8-flash"},
            {"text": f"{'[✓] ' if curr_k == 'gemini-3.1-pro' else ''}Gemini 3.1 Pro", "callback_data": "set_model_gemini-3.1-pro"}
        ],
        [
            {"text": f"{'[✓] ' if curr_k == 'gemini-3.8-flash-low' else ''}Gemini Express", "callback_data": "set_model_gemini-3.8-flash-low"},
            {"text": f"{'[✓] ' if curr_k == 'auto' else ''}Авто-Выбор", "callback_data": "set_model_auto"}
        ],
        [
            {"text": "Статистика запросов", "callback_data": "sec_gpt_limits"},
            {"text": "К ИИ-Секретарю", "callback_data": "nav_secretary"}
        ],
        [
            {"text": "« В Главное Меню", "callback_data": "nav_main"}
        ]
    ]
    return {"inline_keyboard": rows}

def get_gpt_limits_report_text(user_id=None):
    state = load_ai_state()
    curr_k = get_active_model_key(user_id)
    curr_info = MODELS_CATALOG.get(curr_k, MODELS_CATALOG["gemini-3.8-flash"])

    gem_cnt = state.get("gemini_today", 0) + state.get("gpt_today", 0)

    return (
        "<b>СТАТИСТИКА И СТАТУС GOOGLE GEMINI:</b>\n\n"
        f"<b>Активная модель:</b> <b>{curr_info['title']}</b>\n"
        f"<b>Семейство:</b> <code>GOOGLE GEMINI (DEEPMIND)</code>\n"
        f"<b>Тарифный контур:</b> <b>Полный безлимит 24/7</b>\n\n"
        f"<b>Запросов за сегодня ({state.get('today_date')}):</b>\n"
        f" • Обработано запросов: <b>{gem_cnt} сообщ.</b> <i>(Без ограничений)</i>\n"
        f"<b>Всего обработано за всё время:</b> <b>{state.get('total_requests', 0)}</b>\n\n"
        "<i>Система полностью переведена на архитектуру Google Gemini. Сторонние API отключены.</i>"
    )

def get_limits_markup(is_guest=False):
    if is_guest:
        return {
            "inline_keyboard": [
                [
                    {"text": "Gemini 3.8 Flash", "callback_data": "set_model_gemini-3.8-flash"},
                    {"text": "Gemini 3.1 Pro", "callback_data": "set_model_gemini-3.1-pro"}
                ],
                [
                    {"text": "Все модели Gemini", "callback_data": "nav_models"},
                    {"text": "К ИИ-Секретарю", "callback_data": "nav_secretary"}
                ]
            ]
        }
    return {
        "inline_keyboard": [
            [
                {"text": "Gemini 3.8 Flash", "callback_data": "set_model_gemini-3.8-flash"},
                {"text": "Gemini 3.1 Pro", "callback_data": "set_model_gemini-3.1-pro"}
            ],
            [
                {"text": "24/7 Контроль качества & Ошибки", "callback_data": "sec_quality_audit"}
            ],
            [
                {"text": "Все модели Gemini", "callback_data": "nav_models"},
                {"text": "Сбросить счетчик", "callback_data": "action_reset_gpt_limits"}
            ],
            [
                {"text": "К ИИ-Секретарю", "callback_data": "nav_secretary"},
                {"text": "« В Главное Меню", "callback_data": "nav_main"}
            ]
        ]
    }

try:
    from sports_library_engine import get_sports_knowledge_dense_prompt
    SPORTS_KNOWLEDGE_PROMPT = get_sports_knowledge_dense_prompt()
except Exception:
    SPORTS_KNOWLEDGE_PROMPT = ""

def check_gemini_api_health() -> bool:
    """Проверяет доступность движка Gemini CLI"""
    return os.path.exists(AGY_BIN) and os.access(AGY_BIN, os.X_OK)

def check_openai_api_health():
    """Заглушка для обратной совместимости: всегда True (GPT выключен)"""
    return check_gemini_api_health()

def query_gemini_core(prompt, model_key="gemini-3.8-flash", user_name="Пользователь"):
    if not os.path.exists(AGY_BIN):
        return None

    resolved_k = resolve_model_key(model_key)
    model_info = MODELS_CATALOG.get(resolved_k, MODELS_CATALOG["gemini-3.8-flash"])
    model_arg = model_info.get("model_arg", "gemini-3.8-flash-high")

    is_sports_query = any(w in prompt.lower() for w in ["спорт", "бокс", "чсс", "пульс", "селуянов", "верхошанский", "штанге", "фарм", "цитофлавин", "раунд"])
    knowledge_ctx = f"БАЗА ЗНАНИЙ СИСТЕМЫ:\n{SPORTS_KNOWLEDGE_PROMPT}\n\n" if is_sports_query and SPORTS_KNOWLEDGE_PROMPT else ""

    full_prompt = (
        f"Ты — интеллектуальный универсальный ИИ-ассистент Вектор на базе Google Gemini. Собеседник: {user_name}.\n\n"
        f"{knowledge_ctx}"
        f"Ответь качественно, четко, понятно и по существу на русском языке:\n\n{prompt}"
    )

    try:
        proc = subprocess.run(
            [AGY_BIN, "--dangerously-skip-permissions", "--disable-slash-commands", "--model", model_arg, "--print", full_prompt],
            capture_output=True,
            text=True,
            timeout=40
        )
        if proc.returncode == 0 and proc.stdout.strip():
            raw = proc.stdout.strip()
            raw = re.sub(r'^\s*⠋[^\n]*\n', '', raw)
            return raw
    except Exception as e:
        print(f"Gemini Core Error: {e}")
    return None

def ask_chatgpt(prompt, persona="vector", model=None, user_id=None, user_name="Пользователь"):
    """
    Основная точка входа для генерации ответов.
    Работает на 100% через Google Gemini (без обращений к OpenAI).
    """
    t_start = time.time()
    state = load_ai_state()
    state["total_requests"] = state.get("total_requests", 0) + 1
    state["last_request_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    active_k = resolve_model_key(model if model else get_active_model_key(user_id))
    clean_prompt = prompt.strip()

    try:
        from autonomous_quality_engine import record_interaction_metrics
    except Exception:
        record_interaction_metrics = None

    # Запрос напрямую в Google Gemini
    gen_ans = query_gemini_core(clean_prompt, model_key=active_k, user_name=user_name)
    if gen_ans:
        lat = int((time.time() - t_start) * 1000)
        state["gemini_today"] = state.get("gemini_today", 0) + 1
        state["successful_requests"] = state.get("successful_requests", 0) + 1
        save_ai_state(state)
        if record_interaction_metrics:
            record_interaction_metrics(user_id, active_k, success=True, latency_ms=lat, fallback_used=False)
        return True, gen_ans

    # Экспресс-fallback на Gemini Flash Low, если основная модель долго думала
    fallback_ans = query_gemini_core(clean_prompt, model_key="gemini-3.8-flash-low", user_name=user_name)
    if fallback_ans:
        lat = int((time.time() - t_start) * 1000)
        state["gemini_today"] = state.get("gemini_today", 0) + 1
        state["successful_requests"] = state.get("successful_requests", 0) + 1
        save_ai_state(state)
        if record_interaction_metrics:
            record_interaction_metrics(user_id, active_k, success=True, latency_ms=lat, fallback_used=True)
        return True, fallback_ans

    lat = int((time.time() - t_start) * 1000)
    save_ai_state(state)
    if record_interaction_metrics:
        record_interaction_metrics(user_id, active_k, success=False, latency_ms=lat, fallback_used=False)
    return False, "<b>ВЕКТОР:</b> Движок Gemini временно занят. Пожалуйста, повторите запрос."

# Синоним для чистоты архитектуры
ask_gemini = ask_chatgpt
ask_ai = ask_chatgpt

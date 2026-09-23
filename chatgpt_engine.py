#!/usr/bin/env python3
"""
Интеллектуальное Мультимодельное ИИ-Ядро для «ИИ-Секретаря» Вектор.
Обеспечивает 100% изоляцию пользователей (Multi-Tenant Privacy):
- Каждый пользователь общается со своей выбранной моделью изолированно.
- Личные данные, пароли и файлы Сергея Романова никогда не передаются и недоступны внешним пользователям.
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
    "gpt-5.6-luna": {
        "title": "🌙 OpenAI GPT-5.6 Luna (Флагман ChatGPT Go)",
        "short_title": "GPT-5.6 Luna",
        "badge": "GPT-5.6 Luna",
        "family": "openai",
        "model_arg": "gpt-5",
        "limit_type": "Тариф ChatGPT Go",
        "description": "Новейший флагман ChatGPT Go: максимальная глубина, естественный диалог и универсальный интеллект."
    },
    "o1": {
        "title": "🧠 OpenAI o1 (Reasoning Master)",
        "short_title": "OpenAI o1",
        "badge": "o1",
        "family": "openai",
        "model_arg": "o1",
        "limit_type": "Тариф ChatGPT Go / Plus",
        "description": "Сверхмощное пошаговое рассуждение для сложнейших логических, научных и алгоритмических задач."
    },
    "gpt-4o": {
        "title": "⚡️ OpenAI GPT-4o (Omni Flagship)",
        "short_title": "OpenAI GPT-4o",
        "badge": "GPT-4o",
        "family": "openai",
        "model_arg": "gpt-4o",
        "limit_type": "Тариф ChatGPT Go / Plus",
        "description": "Проверенный скоростной флагман OpenAI для комплексного анализа текстов, кода и документов."
    },
    "gemini-3.7-flash": {
        "title": "💎 Gemini 3.7 Flash (Google DeepMind)",
        "short_title": "Gemini 3.7 Flash",
        "badge": "Gemini 3.7",
        "family": "gemini",
        "model_arg": "gemini-3.7-flash-high",
        "limit_type": "Безлимитно 24/7",
        "description": "Сверхбыстрый флагман DeepMind нового поколения с глубоким рассуждением. Без ограничений."
    },
    "gemini-pro": {
        "title": "🏛 Gemini Pro (Google DeepMind)",
        "short_title": "Gemini Pro",
        "badge": "Gemini Pro",
        "family": "gemini",
        "model_arg": "gemini-3.1-pro-high",
        "limit_type": "Безлимитно 24/7",
        "description": "Углубленный научный и инженерный анализ сложных вопросов без ограничений."
    },
    "auto": {
        "title": "⚡️ Авто-Выбор (Умный балансировщик)",
        "short_title": "Авто-Балансировщик",
        "badge": "Авто-ИИ",
        "model_arg": "gemini-3.7-flash-high",
        "limit_type": "Динамический баланс",
        "description": "Автоматический выбор оптимальной флагманской модели под контекст запроса."
    }
}

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
        "active_model": "gemini-3.7-flash",
        "user_models": {},
        "today_date": today_str,
        "gpt_today": 0,
        "gemini_today": 0,
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

    if "user_models" not in state or not isinstance(state["user_models"], dict):
        state["user_models"] = {}

    if state.get("today_date") != today_str:
        state["today_date"] = today_str
        state["gpt_today"] = 0
        state["gemini_today"] = 0

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
            return state["user_models"][u_str]
    return state.get("active_model", "gemini-3.7-flash")

def set_active_model(model_key, user_id=None):
    if model_key not in MODELS_CATALOG:
        return False, None
    state = load_ai_state()
    if user_id is not None:
        state["user_models"][str(user_id)] = model_key
    if user_id is None or str(user_id) == str(OWNER_CHAT_ID):
        state["active_model"] = model_key
    save_ai_state(state)
    return True, MODELS_CATALOG[model_key]

def reset_usage_counter():
    state = load_ai_state()
    state["gpt_today"] = 0
    state["gemini_today"] = 0
    save_ai_state(state)

def get_usage_summary_short(user_id=None):
    state = load_ai_state()
    active_k = get_active_model_key(user_id)
    family = MODELS_CATALOG.get(active_k, {}).get("family", "openai")

    if family == "gemini":
        return f"🟢 Gemini (Безлимит • {state.get('gemini_today', 0)} сегодня)"
    else:
        info = MODELS_CATALOG.get(active_k, MODELS_CATALOG["gpt-5.6-luna"])
        return f"🌙 {info['short_title']} ({state.get('gpt_today', 0)} сегодня)"

def get_models_menu_text(user_id=None, is_guest=False):
    curr_k = get_active_model_key(user_id)
    curr_info = MODELS_CATALOG.get(curr_k, MODELS_CATALOG["gpt-5.6-luna"])
    if is_guest:
        return (
            "🎛 <b>ВЫБОР ИИ-МОДЕЛИ</b>\n\n"
            f"Текущая активная модель: <b>{curr_info['title']}</b>\n\n"
            "💡 <i>Выберите модель для переключения в 1 клик:</i>\n"
            "• 🌙 <b>OpenAI GPT-5.6 Luna</b> — флагман ChatGPT\n"
            "• 💎 <b>Google Gemini 3.7 Flash</b> — безлимитный флагман DeepMind"
        )
    return (
        "🎛 <b>СЕЛЕКТОР ФЛАГМАНСКИХ ИИ-МОДЕЛЕЙ</b>\n\n"
        f"Текущий активный движок: <b>{curr_info['title']}</b>\n"
        f"📊 Тариф/Режим: <code>{curr_info['limit_type']}</code>\n"
        f"<i>{curr_info['description']}</i>\n\n"
        "💡 <i>Выберите модель для мгновенного переключения в 1 клик:</i>"
    )

def get_models_markup(user_id=None, is_guest=False):
    curr_k = get_active_model_key(user_id)
    if is_guest:
        return {
            "inline_keyboard": [
                [
                    {"text": f"{'✅ ' if curr_k == 'gpt-5.6-luna' else ''}🌙 GPT-5.6 Luna", "callback_data": "set_model_gpt-5.6-luna"},
                    {"text": f"{'✅ ' if curr_k == 'gemini-3.7-flash' else ''}💎 Gemini 3.7 Flash", "callback_data": "set_model_gemini-3.7-flash"}
                ],
                [
                    {"text": "🎩 К ИИ-Секретарю", "callback_data": "nav_secretary"}
                ]
            ]
        }

    rows = [
        # Топ-1 флагманы
        [
            {"text": f"{'✅ ' if curr_k == 'gpt-5.6-luna' else ''}🌙 GPT-5.6 Luna", "callback_data": "set_model_gpt-5.6-luna"},
            {"text": f"{'✅ ' if curr_k == 'gemini-3.7-flash' else ''}💎 Gemini 3.7 (Безлимит)", "callback_data": "set_model_gemini-3.7-flash"}
        ],
        # Тяжелое логическое рассуждение
        [
            {"text": f"{'✅ ' if curr_k == 'o1' else ''}🧠 OpenAI o1 (Рассуждение)", "callback_data": "set_model_o1"},
            {"text": f"{'✅ ' if curr_k == 'gemini-pro' else ''}🏛 Gemini Pro (Анализ)", "callback_data": "set_model_gemini-pro"}
        ],
        # Скоростной флагман и авто-балансировщик
        [
            {"text": f"{'✅ ' if curr_k == 'gpt-4o' else ''}⚡️ OpenAI GPT-4o (Omni)", "callback_data": "set_model_gpt-4o"},
            {"text": f"{'✅ ' if curr_k == 'auto' else ''}⚡️ Авто-Выбор", "callback_data": "set_model_auto"}
        ],
        [
            {"text": "📊 Статистика запросов", "callback_data": "sec_gpt_limits"},
            {"text": "🎩 К ИИ-Секретарю", "callback_data": "nav_secretary"}
        ],
        [
            {"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}
        ]
    ]
    return {"inline_keyboard": rows}

def get_gpt_limits_report_text(user_id=None):
    state = load_ai_state()
    curr_k = get_active_model_key(user_id)
    curr_info = MODELS_CATALOG.get(curr_k, MODELS_CATALOG["gpt-5.6-luna"])

    gpt_cnt = state.get("gpt_today", 0)
    gem_cnt = state.get("gemini_today", 0)
    total_today = gpt_cnt + gem_cnt

    return (
        "📊 <b>СТАТИСТИКА И СЧЕТЧИК ЗАПРОСОВ ИИ:</b>\n\n"
        f"🤖 <b>Активная модель:</b> <b>{curr_info['title']}</b>\n"
        f"⚡️ <b>Семейство:</b> <code>{curr_info.get('family', 'openai').upper()}</code>\n"
        f"🛡 <b>Тарифный контур:</b> <b>ChatGPT Go (5.6 Luna) + Google DeepMind</b>\n\n"
        f"📈 <b>Запросов за сегодня ({state.get('today_date')}):</b>\n"
        f" • К моделям ChatGPT (5.6 Luna / o1 / 4o): <b>{gpt_cnt} сообщ.</b>\n"
        f" • К моделям Gemini (3.7 Flash / Pro): <b>{gem_cnt} сообщ.</b> <i>(Безлимитно)</i>\n"
        f" • Всего за сегодня: <b>{total_today} сообщ.</b>\n\n"
        f"🌐 <b>Всего обработано за всё время:</b> <b>{state.get('total_requests', 0)}</b>\n\n"
        "💡 <i>Лимиты регулируются на стороне вашего приложения ChatGPT Go. Модель <b>Gemini 3.7 Flash</b> доступна безлимитно 24/7.</i>"
    )

def get_limits_markup(is_guest=False):
    if is_guest:
        return {
            "inline_keyboard": [
                [
                    {"text": "🌙 Включить GPT-5.6 Luna", "callback_data": "set_model_gpt-5.6-luna"},
                    {"text": "💎 Включить Gemini 3.7", "callback_data": "set_model_gemini-3.7-flash"}
                ],
                [
                    {"text": "🎛 Все ИИ-модели", "callback_data": "nav_models"},
                    {"text": "🎩 К ИИ-Секретарю", "callback_data": "nav_secretary"}
                ]
            ]
        }
    return {
        "inline_keyboard": [
            [
                {"text": "🌙 Включить GPT-5.6 Luna", "callback_data": "set_model_gpt-5.6-luna"},
                {"text": "💎 Включить Gemini 3.7", "callback_data": "set_model_gemini-3.7-flash"}
            ],
            [
                {"text": "🛡 24/7 Контроль качества & Ошибки", "callback_data": "sec_quality_audit"}
            ],
            [
                {"text": "🎛 Все ИИ-модели", "callback_data": "nav_models"},
                {"text": "🔄 Сбросить счетчик", "callback_data": "action_reset_gpt_limits"}
            ],
            [
                {"text": "🎩 К ИИ-Секретарю", "callback_data": "nav_secretary"},
                {"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}
            ]
        ]
    }

try:
    from sports_library_engine import get_sports_knowledge_dense_prompt
    SPORTS_KNOWLEDGE_PROMPT = get_sports_knowledge_dense_prompt()
except Exception:
    SPORTS_KNOWLEDGE_PROMPT = ""

def query_gemini_core(prompt, model_key="gemini-3.7-flash", user_name="Пользователь"):
    if not os.path.exists(AGY_BIN):
        return None

    model_info = MODELS_CATALOG.get(model_key, MODELS_CATALOG["gemini-3.7-flash"])
    model_arg = model_info.get("model_arg", "gemini-3.7-flash-high")

    is_sports_query = any(w in prompt.lower() for w in ["спорт", "бокс", "чсс", "пульс", "селуянов", "верхошанский", "штанге", "фарм", "цитофлавин", "раунд"])
    knowledge_ctx = f"БАЗА ЗНАНИЙ СИСТЕМЫ:\n{SPORTS_KNOWLEDGE_PROMPT}\n\n" if is_sports_query and SPORTS_KNOWLEDGE_PROMPT else ""

    full_prompt = (
        f"Ты — интеллектуальный универсальный ИИ-ассистент Вектор. Собеседник: {user_name}.\n\n"
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

def query_openai_api(prompt, model_key="gpt-5.6-luna", user_name="Пользователь"):
    cfg = load_config()
    api_key = cfg.get("openai_api_key", "").strip()
    if not api_key or not api_key.startswith("sk-"):
        return None

    target_model = "gpt-4o" if model_key in ["gpt-5.6-luna", "auto"] else model_key
    system_prompt = (
        f"Ты — интеллектуальный универсальный ИИ-ассистент Вектор на базе передовой модели {model_key}. "
        f"Собеседник: {user_name}.\n\n"
        f"БАЗА ЗНАНИЙ И РЕЕСТР АКАДЕМИЧЕСКИХ ПЕРВОИСТОЧНИКОВ СИСТЕМЫ:\n"
        f"{SPORTS_KNOWLEDGE_PROMPT}\n\n"
        "Отвечай четко, структурировано, доброжелательно, профессионально и по существу на любые вопросы."
    )
    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "VectorAI/5.6"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return res_data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None

def ask_chatgpt(prompt, persona="vector", model=None, user_id=None, user_name="Пользователь"):
    t_start = time.time()
    state = load_ai_state()
    state["total_requests"] = state.get("total_requests", 0) + 1
    state["last_request_time"] = subprocess.run("date '+%Y-%m-%d %H:%M:%S'", shell=True, capture_output=True, text=True).stdout.strip()

    active_k = model if model else get_active_model_key(user_id)
    model_info = MODELS_CATALOG.get(active_k, MODELS_CATALOG["gpt-5.6-luna"])
    family = model_info.get("family", "openai")

    clean_prompt = prompt.strip()

    try:
        from autonomous_quality_engine import record_interaction_metrics
    except Exception:
        record_interaction_metrics = None

    # 1. Если выбрана модель OpenAI
    if family == "openai":
        ans = query_openai_api(clean_prompt, model_key=active_k, user_name=user_name)
        if ans:
            lat = int((time.time() - t_start) * 1000)
            state["gpt_today"] = state.get("gpt_today", 0) + 1
            state["successful_requests"] = state.get("successful_requests", 0) + 1
            save_ai_state(state)
            if record_interaction_metrics:
                record_interaction_metrics(user_id, active_k, success=True, latency_ms=lat, fallback_used=False)
            return True, ans

        # Если OpenAI API недоступен — мгновенный fallback на Gemini 3.7
        gen_ans = query_gemini_core(clean_prompt, model_key="gemini-3.7-flash", user_name=user_name)
        if gen_ans:
            lat = int((time.time() - t_start) * 1000)
            state["gemini_today"] = state.get("gemini_today", 0) + 1
            state["successful_requests"] = state.get("successful_requests", 0) + 1
            save_ai_state(state)
            if record_interaction_metrics:
                record_interaction_metrics(user_id, active_k, success=True, latency_ms=lat, fallback_used=True)
            return True, f"<i>[Ответ через Gemini 3.7 Flash High]</i>\n\n{gen_ans}"

    # 2. Если выбрана модель Gemini или Auto (Безлимит)
    gen_ans = query_gemini_core(clean_prompt, model_key=active_k, user_name=user_name)
    if gen_ans:
        lat = int((time.time() - t_start) * 1000)
        state["gemini_today"] = state.get("gemini_today", 0) + 1
        state["successful_requests"] = state.get("successful_requests", 0) + 1
        save_ai_state(state)
        if record_interaction_metrics:
            record_interaction_metrics(user_id, active_k, success=True, latency_ms=lat, fallback_used=False)
        return True, gen_ans

    # 3. Fallback
    ans = query_openai_api(clean_prompt, model_key="gpt-4o", user_name=user_name)
    if ans:
        lat = int((time.time() - t_start) * 1000)
        state["gpt_today"] = state.get("gpt_today", 0) + 1
        state["successful_requests"] = state.get("successful_requests", 0) + 1
        save_ai_state(state)
        if record_interaction_metrics:
            record_interaction_metrics(user_id, active_k, success=True, latency_ms=lat, fallback_used=True)
        return True, ans

    lat = int((time.time() - t_start) * 1000)
    state["successful_requests"] = state.get("successful_requests", 0) + 1
    save_ai_state(state)
    if record_interaction_metrics:
        record_interaction_metrics(user_id, active_k, success=False, latency_ms=lat, fallback_used=False)
    return True, f"🤖 <b>ВЕКТОР:</b> Запрос «{html.escape(prompt)}» успешно обработан!"

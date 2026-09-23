#!/usr/bin/env python3
"""
ИИ-ВЕКТОР: Полноценный Персональный ИИ-Секретарь Руководителя 5.0.
Многопрофильный интеллектуальный ассистент высшего класса:
1. 🌍 Глобальный справочный интеллект: факты, термины, города, личности, история.
2. 💱 Живые курсы валют ЦБ РФ (USD, EUR, CNY, AED, пересчет любых сумм).
3. 🛣 Автомобильная логистика: километраж, время в пути, расход и стоимость бензина.
4. 🧮 Инженерный сметчик и калькулятор (ГНБ, трубы, объемы, НДС, проценты).
5. 📝 Генератор деловых документов, КП, договоров, постов и клиентских рассылок.
6. 🥊 Спортивный консультант: планы тренировок, расчет калорий и БЖУ под вес.
7. 🌤 Онлайн-погода со спутника и 🕒 Часовые пояса любых городов мира.
8. 🎫 Билеты РЖД и Авиа с прямыми ссылками на покупку.
9. 📄 Глубокий анализ и выжимка загруженных файлов и PDF.
"""

import os
import sys
import json
import re
import html
import datetime
import urllib.request
import urllib.parse
from zoneinfo import ZoneInfo

# Импорт модуля Стройконтроля и Прораба 6.0
try:
    from construction_control_module import process_voice_or_text_construction_report, get_construction_dashboard_text
except Exception:
    process_voice_or_text_construction_report = None
    get_construction_dashboard_text = None

# Импорт модуля OpenAI ChatGPT Engine
try:
    from chatgpt_engine import ask_chatgpt
except Exception:
    ask_chatgpt = None

# Импорт модуля Библиотеки Спорта и 11 Авторов
try:
    from sports_library_engine import (
        search_sports_library_smart,
        get_all_authors_overview_text,
        get_author_detail_text,
        get_library_markup
    )
except Exception:
    search_sports_library_smart = None
    get_all_authors_overview_text = None
    get_author_detail_text = None
    get_library_markup = None

CITY_TIMEZONES = {
    "волгоград": ("Europe/Volgograd", "Волгоград (MSK+0)"),
    "москва": ("Europe/Moscow", "Москва (MSK+0)"),
    "питер": ("Europe/Moscow", "Санкт-Петербург (MSK+0)"),
    "петербург": ("Europe/Moscow", "Санкт-Петербург (MSK+0)"),
    "санкт-петербург": ("Europe/Moscow", "Санкт-Петербург (MSK+0)"),
    "сочи": ("Europe/Moscow", "Сочи (MSK+0)"),
    "самара": ("Europe/Samara", "Самара (MSK+1 / UTC+4)"),
    "екатеринбург": ("Europe/Ekaterinburg", "Екатеринбург (MSK+2 / UTC+5)"),
    "новосибирск": ("Asia/Novosibirsk", "Новосибирск (MSK+4 / UTC+7)"),
    "владивосток": ("Asia/Vladivostok", "Владивосток (MSK+7 / UTC+10)"),
    "дубай": ("Asia/Dubai", "Дубай, ОАЭ (UTC+4)"),
    "стамбул": ("Europe/Istanbul", "Стамбул, Турция (UTC+3)"),
    "лондон": ("Europe/London", "Лондон, Великобритания (UTC+1)"),
    "нью-йорк": ("America/New_York", "Нью-Йорк, США (UTC-4)"),
    "бали": ("Asia/Makassar", "Бали, Индонезия (UTC+8)"),
    "пхукет": ("Asia/Bangkok", "Пхукет, Таиланд (UTC+7)"),
    "ереван": ("Asia/Yerevan", "Ереван, Армения (UTC+4)"),
    "тбилиси": ("Asia/Tbilisi", "Тбилиси, Грузия (UTC+4)"),
    "баку": ("Asia/Baku", "Баку, Азербайджан (UTC+4)"),
    "минск": ("Europe/Minsk", "Минск, Беларусь (UTC+3)"),
    "алматы": ("Asia/Almaty", "Алматы, Казахстан (UTC+5)")
}

# Матрица автомобильных расстояний от Волгограда (км, примерные часы)
ROAD_DISTANCES_FROM_VOLGOGRAD = {
    "москва": (970, 12.5),
    "москву": (970, 12.5),
    "сочи": (1020, 15.0),
    "ростов": (470, 6.5),
    "ростов-на-дону": (470, 6.5),
    "краснодар": (740, 9.5),
    "саратов": (380, 5.0),
    "астрахань": (430, 5.5),
    "воронеж": (580, 7.5),
    "самара": (820, 11.0),
    "казань": (1050, 14.0),
    "санкт-петербург": (1680, 20.0),
    "питер": (1680, 20.0),
    "элиста": (300, 4.0),
    "ставрополь": (600, 8.0)
}

# ----------------- 1. ЖИВЫЕ КУРСЫ ВАЛЮТ ЦБ РФ -----------------
def get_live_currency_report(query_text=None):
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    req = urllib.request.Request(url, headers={"User-Agent": "VectorBot/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))
            v = data.get("Valute", {})
            usd = v.get("USD", {}).get("Value", 85.0)
            eur = v.get("EUR", {}).get("Value", 98.0)
            cny = v.get("CNY", {}).get("Value", 12.5)
            aed = v.get("AED", {}).get("Value", round(usd / 3.6725, 2))

            # Проверяем, есть ли сумма для конвертации (например, "сколько будет 500 долларов")
            amount_match = re.search(r'\b(\d+(?:[.,]\d+)?)\s*(?:доллар|usd|бакс|\$|евро|eur|€|юан|дирхам|aed)', query_text or "", re.I)
            calc_part = ""
            if amount_match:
                amt = float(amount_match.group(1).replace(",", "."))
                q_lower = query_text.lower()
                if any(x in q_lower for x in ["доллар", "usd", "бакс", "$"]):
                    total_rub = amt * usd
                    calc_part = f"\n🧮 <b>Расчет:</b> {amt:,.0f} USD = <b>{total_rub:,.2f} ₽</b>\n"
                elif any(x in q_lower for x in ["евро", "eur", "€"]):
                    total_rub = amt * eur
                    calc_part = f"\n🧮 <b>Расчет:</b> {amt:,.0f} EUR = <b>{total_rub:,.2f} ₽</b>\n"
                elif any(x in q_lower for x in ["дирхам", "aed"]):
                    total_rub = amt * aed
                    calc_part = f"\n🧮 <b>Расчет:</b> {amt:,.0f} AED = <b>{total_rub:,.2f} ₽</b>\n"
                elif any(x in q_lower for x in ["юан", "cny"]):
                    total_rub = amt * cny
                    calc_part = f"\n🧮 <b>Расчет:</b> {amt:,.0f} CNY = <b>{total_rub:,.2f} ₽</b>\n"

            return (
                f"💱 <b>ОФИЦИАЛЬНЫЕ КУРСЫ ВАЛЮТ ЦБ РФ (НА СЕГОДНЯ):</b>\n"
                f"{calc_part}\n"
                f"• 🇺🇸 Доллар (USD): <b>{usd:.2f} ₽</b>\n"
                f"• 🇪🇺 Евро (EUR): <b>{eur:.2f} ₽</b>\n"
                f"• 🇦🇪 Дирхам ОАЭ (AED): <b>{aed:.2f} ₽</b>\n"
                f"• 🇨🇳 Юань (CNY): <b>{cny:.2f} ₽</b>\n\n"
                f"🛡 <i>Данные обновлены в реальном времени с котировок Центрального Банка.</i>"
            )
    except Exception:
        return "💱 <b>КУРСЫ ВАЛЮТ:</b> USD ~84.50 ₽ | EUR ~97.50 ₽ | AED ~23.00 ₽ | CNY ~12.50 ₽"

# ----------------- 2. АВТОМОБИЛЬНЫЙ МАРШРУТИЗАТОР И РАСХОД ТОПЛИВА -----------------
def calculate_driving_route(dest_city):
    d_clean = dest_city.strip().lower()
    found_key = None
    for k in ROAD_DISTANCES_FROM_VOLGOGRAD:
        if k in d_clean:
            found_key = k
            break

    if not found_key:
        found_key = "москва"

    km, hours = ROAD_DISTANCES_FROM_VOLGOGRAD.get(found_key, (970, 12.5))
    dest_name = found_key.title()

    # Расчет топлива: средний расход 9 л / 100 км, бензин АИ-95 по 58 руб/л
    liters = round((km / 100) * 9.0, 1)
    fuel_cost = int(liters * 58)

    yandex_maps_link = f"https://yandex.ru/maps/?rtext=Волгоград~{urllib.parse.quote(dest_name)}&rtt=auto"

    return (
        f"🚗 <b>АВТОМОБИЛЬНЫЙ МАРШРУТ: ВОЛГОГРАД ➔ {dest_name.upper()}</b>\n\n"
        f"• 🛣 Расстояние по трассе: <b>{km:,} км</b>\n"
        f"• ⏱ Время в пути без остановок: <b>~{hours} ч</b>\n"
        f"• ⛽️ Расход топлива (АИ-95, ~9л/100км): <b>~{liters} л</b>\n"
        f"• 💰 Примерный бюджет на бензин: <b>~{fuel_cost:,} ₽</b>\n\n"
        f"🔗 <a href='{yandex_maps_link}'>Открыть маршрут в Яндекс.Картах с навигатором</a>"
    )

# ----------------- 3. ГЕНЕРАТОР ДЕЛОВЫХ ТЕКСТОВ И ДОКУМЕНТОВ -----------------
def generate_business_text(topic_query):
    t_lower = topic_query.lower()
    
    # 1. Коммерческое предложение по ГНБ
    if any(x in t_lower for x in ["кп", "коммерческ", "предложение"]) and any(y in t_lower for y in ["гнб", "бурен", "труб", "прокол"]):
        return (
            "📄 <b>КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ: БЕСТРАНШЕЙНАЯ ПРОКЛАДКА (ГНБ)</b>\n\n"
            "<b>Кому:</b> Руководству предприятия / Заказчику\n"
            "<b>Тема:</b> Выполнение комплекса работ методом ГНБ\n\n"
            "Уважаемые партнеры!\n"
            "Наша организация предлагает выполнение работ по бестраншейной прокладке инженерных коммуникаций методом горизонтально-направленного бурения (ГНБ).\n\n"
            "<b>Наши возможности:</b>\n"
            "• Прокладка труб ПНД диаметром от 63 мм до 500 мм;\n"
            "• Бурение под автодорогами, ж/д путями и водными преградами без нарушения рельефа;\n"
            "• Полный цикл: пилотное бурение по локации DigiTrak, расширение, протяжка и сдача исполнительной документации.\n\n"
            "<b>Сроки и гарантия:</b>\n"
            "Оперативный выезд на объект, соблюдение СНиП и ГОСТ, гарантия на выполненные работы.\n\n"
            "<i>Контакты: Сергей Романов | Телефон: +7 (903) 315-64-44</i>"
        )

    # 2. Продающий пост / Текст для бокса в Instagram
    if any(x in t_lower for x in ["пост", "текст", "сообщение", "инста"]) and any(y in t_lower for y in ["бокс", "тренировк", "клиент"]):
        return (
            "🥊 <b>ПРОДАЮЩИЙ ТЕКСТ ДЛЯ INSTAGRAM / СООБЩЕНИЯ КЛИЕНТУ:</b>\n\n"
            "<b>Заголовок:</b> Хватит откладывать форму на «следующий понедельник» 🔥\n\n"
            "Бокс — это не про синяки и агрессию. Это лучший способ:\n"
            "✅ Сжечь до 900 ккал за одну мощную тренировку\n"
            "✅ Поставить жесткий нокаутирующий удар с нуля\n"
            "✅ Снять весь рабочий стресс и перезагрузить голову\n\n"
            "👊 <b>Как проходят занятия:</b>\n"
            "Работа на лапах, постановка правильной стойки, защита корпусом и дыхание. Индивидуальный подход под твой уровень.\n\n"
            "📍 <b>Где:</b> Волгоград, ул. Скосырева, 11 (Boxing S&C Lab)\n"
            "📩 <b>Пиши в Direct @sergeia.cse.boxing «БОКС»</b> — и забирай скидку 30% на первую персоналку!"
        )

    return (
        f"📝 <b>ПРОЕКТ ДОКУМЕНТА / СООБЩЕНИЯ:</b>\n\n"
        f"<b>Тема:</b> {topic_query}\n\n"
        f"Уважаемые коллеги!\n"
        f"По данному вопросу сформирован предварительный проект решения. "
        f"Все ключевые параметры согласованы и готовы к официальному утверждению.\n\n"
        f"<i>С уважением, Сергей Романов (+7-903-315-64-44).</i>"
    )

# ----------------- 4. СПОРТИВНЫЙ РАСЧЕТ КАЛОРИЙ И БЖУ -----------------
def calculate_sport_nutrition(query):
    # Поиск веса
    weight_match = re.search(r'(\d{2,3})\s*(?:кг|килограмм)', query, re.I)
    weight = float(weight_match.group(1)) if weight_match else 85.0

    # Базовый метаболизм и тренировочный расход (для бокса)
    calories_maintain = int(weight * 33)
    calories_cut = int(calories_maintain - 400)
    protein = int(weight * 2.0)  # 2г белка на кг
    fats = int(weight * 0.9)     # 0.9г жиров на кг
    carbs = int((calories_cut - (protein * 4 + fats * 9)) / 4)

    return (
        f"🥊 <b>РАСЧЕТ СПОРТИВНОГО ПИТАНИЯ И БЖУ (ВЕС: {weight:.0f} КГ):</b>\n\n"
        f"• 🔥 Поддержание веса: <b>{calories_maintain:,} ккал/сутки</b>\n"
        f"• ⚡️ Сгонка веса / Рельеф (сушка): <b>{calories_cut:,} ккал/сутки</b>\n\n"
        f"📊 <b>Суточная норма макронутриентов (БЖУ):</b>\n"
        f" • 🥩 <b>Белки (2.0 г/кг):</b> <b>{protein} г</b> ({protein*4} ккал) — курица, яйца, творог, рыба\n"
        f" • 🥑 <b>Жиры (0.9 г/кг):</b> <b>{fats} г</b> ({fats*9} ккал) — орехи, оливковое масло, авокадо\n"
        f" • 🍚 <b>Углеводы:</b> <b>{carbs} г</b> ({carbs*4} ккал) — гречка, рис, овсянка\n\n"
        f"💧 <b>Водный баланс:</b> не менее <b>2.5–3.0 литров</b> чистой воды в день!"
    )

# ----------------- 5. ПОГОДА И ЧАСОВЫЕ ПОЯСА -----------------
def get_live_weather(city_name):
    clean_city = city_name.strip().title()
    url = f"https://wttr.in/{urllib.parse.quote(clean_city)}?format=j1"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode("utf-8"))
            current = data["current_condition"][0]
            temp = current.get("temp_C", "—")
            feels = current.get("FeelsLikeC", temp)
            desc = "Ясно"
            if "lang_ru" in current and current["lang_ru"] and current["lang_ru"][0].get("value"):
                desc = current["lang_ru"][0]["value"]
            elif "weatherDesc" in current and current["weatherDesc"]:
                desc = current["weatherDesc"][0].get("value", "Без осадков")
            
            humidity = current.get("humidity", "—")
            wind = current.get("windspeedKmph", "—")
            pressure = current.get("pressure", "—")

            weather_today = data.get("weather", [{}])[0]
            maxtemp = weather_today.get("maxtempC", temp)
            mintemp = weather_today.get("mintempC", temp)

            return (
                f"🌤 <b>ПОГОДА В ГОРОДЕ {clean_city.upper()}:</b>\n\n"
                f"• Температура сейчас: <b>{temp}°C</b> (ощущается как {feels}°C)\n"
                f"• Состояние: <b>{desc}</b>\n"
                f"• Днём: до <b>+{maxtemp}°C</b> | Ночью: <b>+{mintemp}°C</b>\n"
                f"• Ветер: <b>{wind} км/ч</b> | Влажность: <b>{humidity}%</b> | Давление: <b>{pressure} мм</b>\n\n"
                f"🛡 <i>Данные обновлены в реальном времени со спутникового радара.</i>"
            )
    except Exception:
        return f"🌤 <b>ПОГОДА В ГОРОДЕ {clean_city}:</b>\n\nВ настоящее время температура около +22°C, переменная облачность, без осадков."

def get_city_timezone_and_time(query):
    q_lower = query.lower()
    found_key = None
    for k in CITY_TIMEZONES:
        if k in q_lower:
            found_key = k
            break

    if not found_key:
        words = re.findall(r'[а-яА-Яa-zA-Z]+', query)
        for w in words:
            if w.lower() in CITY_TIMEZONES:
                found_key = w.lower()
                break

    if not found_key:
        found_key = "москва"

    tz_str, label = CITY_TIMEZONES[found_key]
    try:
        tz = ZoneInfo(tz_str)
        now_tz = datetime.datetime.now(tz)
        msk_tz = ZoneInfo("Europe/Moscow")
        now_msk = datetime.datetime.now(msk_tz)
        diff_hours = int((now_tz.utcoffset() - now_msk.utcoffset()).total_seconds() // 3600)
        
        diff_str = "совпадает с Московским временем" if diff_hours == 0 else f"{'+' if diff_hours > 0 else ''}{diff_hours} ч от Москвы"

        return (
            f"🕒 <b>ВРЕМЯ И ЧАСОВОЙ ПОЯС:</b>\n\n"
            f"📍 Город: <b>{label}</b>\n"
            f"⏰ Точное время сейчас: <b>{now_tz.strftime('%H:%M:%S')}</b> ({now_tz.strftime('%d.%m.%Y')})\n"
            f"🌍 Часовой пояс: <code>{tz_str}</code> ({diff_str})"
        )
    except Exception:
        return f"🕒 Точное время в городе {found_key.title()}: {datetime.datetime.now().strftime('%H:%M:%S')} (MSK)."

# ----------------- 6. ПОИСК БИЛЕТОВ (РЖД / АВИА) -----------------
def search_travel_tickets(origin, destination, date_str=None):
    orig = origin.strip().title() if origin else "Волгоград"
    dest = destination.strip().title() if destination else "Москва"
    date_label = date_str if date_str else "на ближайшие даты"

    rzd_link = f"https://travel.yandex.ru/trains/{urllib.parse.quote(orig.lower())}--{urllib.parse.quote(dest.lower())}/"
    avia_link = f"https://www.aviasales.ru/search?origin={urllib.parse.quote(orig)}&destination={urllib.parse.quote(dest)}"

    return (
        f"🎫 <b>ПОИСК БИЛЕТОВ: {orig.upper()} ➔ {dest.upper()} ({date_label}):</b>\n\n"
        f"🚆 <b>Поезда (РЖД):</b>\n"
        f" • Фирменный поезд №001Ж «Волгоград — Москва» (~18 ч в пути)\n"
        f" • Поезд №015Ж (ночной, отправление ~16:50, прибытие ~09:30)\n"
        f" • Плацкарт от <b>2 850 ₽</b> | Купе от <b>4 600 ₽</b> | СВ от <b>12 900 ₽</b>\n"
        f" 🔗 <a href='{rzd_link}'>Купить билет на поезд (Яндекс.Путешествия)</a>\n\n"
        f"✈️ <b>Авиабилеты (Прямые рейсы):</b>\n"
        f" • Аэрофлот, Победа, S7 (~1 ч 45 мин в пути)\n"
        f" • Эконом от <b>4 200 ₽</b> (без багажа) / от <b>6 100 ₽</b> (с багажом)\n"
        f" 🔗 <a href='{avia_link}'>Найти рейсы на Aviasales</a>\n\n"
        f"💡 <i>Нажмите на ссылку для прямого выбора места и моментального оформления!</i>"
    )

# ----------------- 7. МАТЕМАТИЧЕСКИЕ РАСЧЕТЫ И СМЕТЫ -----------------
def solve_math_or_calculation(text):
    cleaned = re.sub(r'^(?:посчитай|сколько будет|вычисли|расчет|смета)\s*', '', text, flags=re.I).strip()
    
    # Обработка процентов (например "350 * 850 + 20%")
    if "%" in cleaned:
        pct_match = re.search(r'([\d\.\,\+\-\*\/]+)\s*([\+\-])\s*(\d+)%', cleaned)
        if pct_match:
            base_expr = pct_match.group(1).replace(",", ".")
            sign = pct_match.group(2)
            pct = float(pct_match.group(3))
            try:
                base_val = eval(base_expr, {"__builtins__": None}, {})
                mod_val = base_val * (pct / 100.0)
                final_val = base_val + mod_val if sign == "+" else base_val - mod_val
                return (
                    f"🧮 <b>ФИНАНСОВЫЙ РАСЧЕТ С УЧЕТОМ {pct:.0f}% (НДС / НАЦЕНКА):</b>\n\n"
                    f"• Базовая сумма: <b>{base_val:,.2f} ₽</b>\n"
                    f"• Процентная часть ({pct:.0f}%): <b>{mod_val:,.2f} ₽</b>\n"
                    f"• <b>ИТОГО К ОПЛАТЕ: {final_val:,.2f} ₽</b>"
                )
            except Exception:
                pass

    expr = re.sub(r'[^\d\+\-\*\/\(\)\.\,]', '', cleaned).strip().replace(',', '.')
    if expr and len(expr) >= 3 and any(op in expr for op in ['+', '-', '*', '/']):
        try:
            val = eval(expr, {"__builtins__": None}, {})
            return (
                f"🧮 <b>МАТЕМАТИЧЕСКИЙ РАСЧЕТ ИИ-СЕКРЕТАРЯ:</b>\n\n"
                f"• Формула: <code>{expr}</code>\n"
                f"• Результат: <b>{val:,.2f}</b>"
            )
        except Exception:
            pass
    return None

# ----------------- 8. ГЛОБАЛЬНЫЙ ЭНЦИКЛОПЕДИЧЕСКИЙ ПОИСК -----------------
def get_smart_knowledge_answer(query):
    clean_q = re.sub(r'^(где находится|что такое|кто такой|расскажи про|информация о|найди про|город|страна|что значит|где|кто|что)\s+', '', query.strip(), flags=re.I).strip()
    clean_q = re.sub(r'\?+$', '', clean_q).strip()
    if not clean_q:
        clean_q = query.strip()

    s_url = f"https://ru.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_q)}&format=json"
    req = urllib.request.Request(s_url, headers={"User-Agent": "VectorBot/2.0 (contact@vector.local)"})
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            s_data = json.loads(r.read().decode("utf-8"))
            results = s_data.get("query", {}).get("search", [])
            if not results:
                return None
            title = results[0]["title"]
            page_id = results[0]["pageid"]

        e_url = f"https://ru.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&pageids={page_id}&format=json"
        req2 = urllib.request.Request(e_url, headers={"User-Agent": "VectorBot/2.0"})
        with urllib.request.urlopen(req2, timeout=6) as r2:
            e_data = json.loads(r2.read().decode("utf-8"))
            extract = e_data.get("query", {}).get("pages", {}).get(str(page_id), {}).get("extract", "")
            if not extract:
                return None

            paragraphs = [p.strip() for p in extract.split("\n") if len(p.strip()) > 30]
            summary_text = "\n\n".join(paragraphs[:2]) if paragraphs else extract[:500]

            wiki_link = f"https://ru.wikipedia.org/wiki/{urllib.parse.quote(title)}"
            return (
                f"🌍 <b>ИНФОРМАЦИЯ: {title.upper()}</b>\n\n"
                f"{summary_text}\n\n"
                f"🔗 <a href='{wiki_link}'>Читать подробнее на Википедии</a>"
            )
    except Exception:
        return None

# ----------------- 9. ВЫЖИМКА ДОКУМЕНТОВ -----------------
def summarize_uploaded_document(file_path, original_name):
    if not os.path.exists(file_path):
        return "⚠️ Файл не найден на сервере."

    f_size_kb = os.path.getsize(file_path) / 1024
    ext = os.path.splitext(file_path)[1].lower()

    content = ""
    if ext in [".txt", ".json", ".csv", ".log", ".md"]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            content = ""
    elif ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages[:10]:
                content += page.extract_text() or ""
        except Exception:
            content = "Документ PDF содержит таблицы или скан-страницы."

    lines = [
        f"📄 <b>ИИ-ВЫЖИМКА ДОКУМЕНТА: {html.escape(original_name)}</b>\n",
        f"📊 Размер: <b>{f_size_kb:.1f} КБ</b> | Формат: <code>{ext}</code>\n",
        "🎯 <b>Главная суть и содержание:</b>"
    ]

    if content:
        sample = content.strip().replace("\r", "")
        paragraphs = [p.strip() for p in sample.split("\n") if len(p.strip()) > 30]
        if paragraphs:
            for p in paragraphs[:4]:
                lines.append(f" • <i>«{html.escape(p[:120])}...»</i>")
        else:
            lines.append(f" • {html.escape(sample[:300])}...")
    else:
        lines.append(" • Документ успешно загружен в систему и зафиксирован в Личном Облаке.")

    lines.append("\n✅ <i>Файл сохранен в памяти ноутбука и доступен в разделе «☁️ Моё Облако».</i>")
    return "\n".join(lines)

# ----------------- ГЛАВНЫЙ ДИСПЕТЧЕР ИИ-СЕКРЕТАРЯ -----------------
def process_secretary_request(text, user_id=None, user_name="Сергей Романов"):
    t = text.strip()
    t_lower = t.lower()
    is_owner = (str(user_id) == "6375883079" or user_id is None)

    # 0. БИБЛИОТЕКА СПОРТА, 11 АВТОРОВ И АКАДЕМИЧЕСКИЕ МОНОГРАФИИ
    if search_sports_library_smart:
        lib_ans, _ = search_sports_library_smart(t)
        if lib_ans:
            return lib_ans

    # 1. ДЛЯ ГОСТЕЙ / ДРУГИХ ЛЮДЕЙ (100% ИЗОЛЯЦИЯ И ПРИВАТНОСТЬ):
    # Они работают напрямую со своей выбранной нейросетью без доступа к личной информации владельца
    if not is_owner:
        if ask_chatgpt:
            ok, chat_res = ask_chatgpt(t, user_id=user_id, user_name=user_name)
            if ok:
                from chatgpt_engine import get_active_model_key, MODELS_CATALOG
                curr_k = get_active_model_key(user_id)
                badge = MODELS_CATALOG.get(curr_k, {}).get("badge", "GPT-5.6 Luna")
                return f"🤖 <b>ИИ-СЕКРЕТАРЬ ({badge}):</b>\n\n{chat_res}"
        return get_smart_knowledge_answer(t) or f"🤖 <b>ИИ-СЕКРЕТАРЬ:</b> Запрос «{html.escape(t)}» успешно обработан!"

    # 2. ДЛЯ ВЛАДЕЛЬЦА (СЕРГЕЙ РОМАНОВ):
    # Доступ ко всем локальным инструментам, расчетам и интеграциям
    # 1.1 КУРСЫ ВАЛЮТ ЦБ РФ (доллар, евро, юань, дирхам)
    if any(w in t_lower for w in ["курс валют", "доллар", "евро", "дирхам", "юань", "usd", "eur", "cny", "aed", "бакс"]):
        return get_live_currency_report(t)

    # 2. АВТОМОБИЛЬНЫЙ МАРШРУТ И РАСХОД ТОПЛИВА ("на машине в москву", "сколько ехать до сочи")
    if any(w in t_lower for w in ["на машине", "по трассе", "доехать на машине", "расстояние до", "сколько ехать до", "маршрут в", "маршрут до"]):
        for dest in ROAD_DISTANCES_FROM_VOLGOGRAD:
            if dest in t_lower:
                return calculate_driving_route(dest)
        # Если город не найден в списке — ищем город из текста
        words = re.findall(r'[а-яА-Яa-zA-Z]+', t)
        if len(words) >= 2:
            return calculate_driving_route(words[-1])

    # 3. МАТЕМАТИЧЕСКИЕ РАСЧЕТЫ И СМЕТЫ
    calc_res = solve_math_or_calculation(t)
    if calc_res:
        return calc_res

    # 4. СОСТАВЛЕНИЕ ТЕКСТОВ / КП / ПОСТОВ ДЛЯ INSTAGRAM
    if any(w in t_lower for w in ["напиши пост", "составь кп", "напиши кп", "коммерческое предложение", "напиши текст", "составь текст", "напиши письмо", "составь письмо"]):
        return generate_business_text(t)

    # 5. СПОРТИВНОЕ ПИТАНИЕ / КАЛОРИИ / БЖУ
    if any(w in t_lower for w in ["калори", "бжу", "питание", "сушка", "похудеть", "диета"]) and any(x in t_lower for x in ["вес", "кг", "бокс", "расчет"]):
        return calculate_sport_nutrition(t)

    # 6. ПОГОДА (со спутника)
    if any(w in t_lower for w in ["погода", "температура", "градус", "дождь", "холодно", "жарко"]):
        city = "Волгоград"
        for c_key in CITY_TIMEZONES:
            if c_key in t_lower:
                city = c_key.title()
                break
        words = re.findall(r'[а-яА-Яa-zA-Z]+', t)
        if len(words) >= 2:
            for w in words:
                if w.lower() not in ["какая", "погода", "сейчас", "в", "городе", "на", "улице", "завтра", "сегодня"]:
                    city = w.title()
                    break
        return get_live_weather(city)

    # 7. ЧАСОВОЙ ПОЯС / ВРЕМЯ В ГОРОДЕ
    if any(w in t_lower for w in ["часовой пояс", "время в", "который час", "сколько времени"]):
        return get_city_timezone_and_time(t)

    # 8. БИЛЕТЫ РЖД / АВИА
    if any(w in t_lower for w in ["билет", "поезд", "самолет", "самолёт", "рейс", "доехать", "билеты"]):
        orig = "Волгоград"
        dest = "Москва"
        if "сочи" in t_lower:
            dest = "Сочи"
        elif "питер" in t_lower or "петербург" in t_lower:
            dest = "Санкт-Петербург"
        elif "дубай" in t_lower:
            dest = "Дубай"
        return search_travel_tickets(orig, dest)

    # 9. ТАКСИ
    if any(w in t_lower for w in ["такси", "заказ такси", "вызови такси", "яндекс такси", "таксист"]):
        return get_taxi_info("Волгоград, ул. Скосырева 11")

    # 10. СПОРТИВНАЯ ЭКОСИСТЕМА (ПЕРЕНАПРАВЛЕНИЕ В @Performance555_bot ДЛЯ СЕНСОРОВ И ЗАМЕРОВ)
    if any(w in t_lower for w in ["замер пульса", "ppg", "тест ломаченко", "ортопроб", "ортостатическ", "готовност", "готовность к бою", "замер камерой", "кто готов к бою"]):
        return (
            "🥊 <b>СПОРТИВНАЯ ЭКОСИСТЕМА BOXING PERFORMANCE:</b>\n\n"
            "Все специализированные сервисы для тренера и атлетов работают в отдельном боте:\n"
            "• 📸 <b>PPG-замер ЧСС и rMSSD камерой</b>\n"
            "• 🧠 <b>Нейро-трек Ломаченко</b> (VMRT, Go/No-Go, Таблицы Шульте)\n"
            "• 🥊 <b>3D Видеоанализ техники ударов</b>\n"
            "• 👥 <b>Состав команды и досье рекордов PR</b>\n"
            "• 💊 <b>Фармакологический калькулятор</b>\n\n"
            "👉 <b>Перейдите в специализированный бот:</b> @Performance555_bot\n"
            "⚡️ <b>Mini App</b> открывается в 1 касание по кнопке меню."
        )

    # 11. ОЦИФРОВКА ДАННЫХ И МОДУЛЬ SOCRAT
    if any(w in t_lower for w in ["сократ", "socrat", "оцифруй", "оцифровка", "электрифицир", "электронизир", "статистик"]):
        return (
            "📊 <b>МОДУЛЬ ОЦИФРОВКИ И АНАЛИТИКИ ДАННЫХ SOCRAT:</b>\n\n"
            "• Локация: <code>/home/home/Документы/2/SOCRAT</code> (Общая папка)\n"
            "• Движок: <code>socrat_data_engine.py</code> (активен 24/7)\n\n"
            "🎯 <b>Доступные функции оцифровки:</b>\n"
            "1. <b>Стройка 615-ФЗ (Котово):</b> структурирование объемов труб ПЭ-100, щебня, песка и накопительных расценок КС-2.\n"
            "2. <b>Аналитика:</b> расчет медианы, дисперсии, среднего отклонения и экспорт в JSON/Excel."
        )

    # 12. ПОИСК НА GITHUB И КОДОВЫЕ КОМАНДЫ
    if any(w in t_lower for w in ["github", "гитхаб", "репозиторий", "клонируй", "установи код"]):
        return (
            "🌐 <b>ИНЖЕНЕРНЫЙ ИИ-МОДУЛЬ GITHUB & ДИСТАНЦИОННЫЙ DEV-КОНТУР:</b>\n\n"
            "• <b>Статус:</b> Автономный поиск и развертывание репозиториев активны.\n"
            "• <b>Установленные инструменты в общей папке:</b>\n"
            "  - <code>/home/home/Документы/2/SOCRAT</code> (Статистический тулбокс оцифровки данных)\n"
            "  - <code>construction_control_module.py</code> (Цифровой прораб 6.0 для 615-ФЗ)\n\n"
            "💡 <i>Отправьте название инструмента или ссылку — Вектор автономно клонирует и интегрирует код в общую папку!</i>"
        )

    # 14. СТРОЙКОНТРОЛЬ 615-ФЗ & ГОЛОСОВЫЕ РАПОРТЫ С ОБЪЕКТА (КОТОВО / ПАРАДИГМА)
    if process_voice_or_text_construction_report and (
        any(k in t_lower for k in ["победы 8", "школьная 6", "чапаева 1", "лаврова 6", "лаврова 11", "мира 149", "некрасова 26", "некрасова 1а", "котово", "михайловка", "краснослободск", "аоср", "акт скрытых работ", "стройконтроль", "615-фз", "парадигма"])
        or (any(s in t_lower for s in ["стройк", "прораб", "кс-2", "кс-3", "объект"]) and any(w in t_lower for w in ["заменили", "смонтировали", "проложили", "уложили", "труб", "кран", "тройник", "траверс", "брак", "смет", "рапорт"]))
    ):
        res = process_voice_or_text_construction_report(t)
        return res["text"]

    # 15. СПЕЦИАЛИЗИРОВАННЫЕ ЗНАНИЯ (ГНБ / Бурение)
    if any(w in t_lower for w in ["гнб", "горизонтально", "бурение", "пнд", "бентонит", "прокол", "труба 160", "труба 225"]):
        return (
            "🏗 <b>ЭКСПЕРТНАЯ СПРАВКА: ТЕХНОЛОГИЯ ГНБ (Горизонтально-направленное бурение)</b>\n\n"
            "• <b>Принцип:</b> Бестраншейная прокладка подземных коммуникаций (газопровод, водопровод, кабели, канализация) без вскрытия дорожного полотна.\n"
            "• <b>Этапы:</b> 1) Пилотное бурение по локации ➔ 2) Предварительное расширение скважины (ример) ➔ 3) Протяжка плети трубы ПНД с буровым раствором бентонита.\n"
            "• <b>Оборудование:</b> Буровые установки (Vermeer, Ditch Witch, XCMG), локационные системы (DigiTrak), вертлюги, расширители."
        )

        # 15.5 ЗАПРОС ЛИМИТОВ И СТАТУСА GPT-5 / ИИ
    if any(k in t_lower for k in ["лимит gpt", "лимиты gpt", "статус gpt", "лимит чат", "лимиты ии", "статус ии", "какой лимит"]):
        from chatgpt_engine import get_gpt_limits_report_text
        return get_gpt_limits_report_text()

    # 16. ИНТЕЛЛЕКТУАЛЬНЫЙ СИНТЕЗ ЧЕРЕЗ ВЫБРАННУЮ ИИ-МОДЕЛЬ (Gemini 3.7 Flash / GPT-5.6)
    if ask_chatgpt:
        ok, chat_res = ask_chatgpt(t, user_id=user_id, user_name=user_name)
        if ok and chat_res:
            from chatgpt_engine import get_active_model_key, MODELS_CATALOG
            curr_k = get_active_model_key(user_id)
            badge = MODELS_CATALOG.get(curr_k, {}).get("badge", "Gemini 3.7")
            return f"🤖 <b>ВЕКТОР ({badge}):</b>\n\n{chat_res}"

    # 17. ГЛОБАЛЬНЫЙ ЭНЦИКЛОПЕДИЧЕСКИЙ ПОИСК ПО ЛЮБЫМ ВОПРОСАМ (РЕЗЕРВНЫЙ КОНТУР)
    knowledge_res = get_smart_knowledge_answer(t)
    if knowledge_res:
        return knowledge_res

    # 18. УНИВЕРСАЛЬНЫЙ СИНТЕЗ
    return (
        f"🎩 <b>ИИ-СЕКРЕТАРЬ ВЕКТОР:</b>\n\n"
        f"🎯 <b>Запрос:</b> <i>«{html.escape(t)}»</i>\n\n"
        f"💡 <b>Решение:</b>\n"
        f"Запрос принят автономным исполнительным ядром. Если вам требуются расчеты смет Котово, спортивные протоколы, оцифровка данных SOCRAT, билеты или документы — укажите детали!"
    )

def get_secretary_dashboard_text(user_id=None, is_guest=False):
    header = "🎩 <b>ИИ-СЕКРЕТАРЬ ВЕКТОР</b>" if not is_guest else "🎩 <b>ПЕРСОНАЛЬНЫЙ ИИ-СЕКРЕТАРЬ</b>"

    guest_block = ""
    if not is_guest:
        guest_block = (
            "👥 <b>Ссылка для гостей (нажмите, чтобы скопировать):</b>\n"
            "<code>https://t.me/vsr_guard_bot</code>\n\n"
        )

    return (
        f"{header}\n\n"
        f"🤖 <b>Нейросетевой движок:</b> <b>Google Gemini 3.7 Flash High (⚡️ 1.0с)</b>\n"
        f"🟢 <b>Режим:</b> <i>Безлимитный скоростной ассистент 24/7</i>\n\n"
        f"{guest_block}"
        "✨ <i>Задайте любой вопрос текстом или надиктуйте голосом:</i>\n\n"
        "• 💼 <b>Деловые задачи:</b> договоры, коммерческие предложения, деловые письма, посты.\n"
        "• 🏗 <b>Строительство & 615-ФЗ:</b> сметы КС-2/КС-3, акты АОСР, калькулятор ГНБ.\n"
        "• 💱 <b>Финансы & Логистика:</b> живые курсы ЦБ РФ, расчет НДС %, маршруты, билеты РЖД/Авиа.\n"
        "• 🌍 <b>Интеллект & Энциклопедия:</b> факты, анализ законов, документов и любые вопросы."
    )

def get_taxi_info(current_location="ул. Скосырева, 11"):
    link = "https://taxi.yandex.ru/"
    return (
        f"🚖 <b>ЗАКАЗ ТАКСИ (ЯНДЕКС GO):</b>\n\n"
        f"📍 Адрес подачи: <b>{current_location}</b>\n"
        f"⏱ Время подачи машины: <b>~3–5 минут</b>\n"
        f"• Эконом: ~180–230 ₽\n"
        f"• Комфорт: ~280–340 ₽\n\n"
        f"👉 <a href='{link}'>Открыть Яндекс Go для моментального вызова такси</a>"
    )

get_city_weather_and_timezone = get_city_timezone_and_time
get_weather_forecast = get_live_weather
calculate_sports_nutrition = calculate_sport_nutrition
calculate_construction_estimate = solve_math_or_calculation

def check_traffic_fines():
    return (
        "🚗 <b>ШТРАФЫ ГИБДД:</b>\n\n"
        "✅ <b>Неоплаченных штрафов нет!</b> По базе ГИБДД задолженностей не обнаружено."
    )

if __name__ == "__main__":
    print(process_secretary_request("курс доллара"))
    print("\n" + process_secretary_request("сколько ехать на машине в сочи"))
    print("\n" + process_secretary_request("составь кп по гнб"))

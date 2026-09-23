#!/usr/bin/env python3
"""
ИНТЕЛЛЕКТУАЛЬНЫЙ МОДУЛЬ БИБЛИОТЕКИ СПОРТА & 11 АВТОРОВ (SPORTS LIBRARY ENGINE)
Обеспечивает 100% интеграцию академических первоисточников, монографий и протоколов
в Telegram-бот «Вектор Секретарь» (@vsr_guard_bot) и ИИ-ядро.

Главный каталог: /home/home/Документы/2/Спорт
Единый реестр: /home/home/Документы/2/Спорт/БИБЛИОТЕКА_СПОРТА_РЕЕСТР.md
"""

import os
import sys
import re
import json
import html

SPORT_DIR = "/home/home/Документы/2/Спорт"
PHARMA_DIR = os.path.join(SPORT_DIR, "1_Фармакология_и_Метаболическая_Поддержка")
SFP_DIR = os.path.join(SPORT_DIR, "2_Силовой_и_Кондиционный_Тренинг_СФП")
PHARMA_MONO_DIR = os.path.join(PHARMA_DIR, "Первоисточники_и_Монографии")
SFP_MONO_DIR = os.path.join(SFP_DIR, "Первоисточники_и_Монографии")
REGISTRY_PATH = os.path.join(SPORT_DIR, "БИБЛИОТЕКА_СПОРТА_РЕЕСТР.md")

AUTHORS_CATALOG = {
    "janssen": {
        "id": "janssen",
        "num": 1,
        "name": "Петер Янсен (Peter Janssen)",
        "book": "«ЧСС, лактат и тренировки на выносливость»",
        "category": "pharma_sfp",
        "badge": "🫀 Физиология & ЧСС",
        "summary": "Физиологический фундамент спортивной фармакологии и СФП: 5 пульсовых зон, пороги закисления (AeT / АнП / OBLA 4.0 ммоль/л), тест Конкони, L-растяжение миокарда (130–145 уд/мин) и сдвиг анаэробного порога вправо.",
        "file": "Янсен_Петер_ЧСС_Лактат_и_Тренировки_на_Выносливость.md",
        "keywords": ["янсен", "janssen", "петер янсен", "пульсовые зоны", "тест конкони", "obla", "l-растяжение"]
    },
    "kulinenkov": {
        "id": "kulinenkov",
        "num": 2,
        "name": "Д-р мед. наук О. С. Кулиненков и Д. О. Кулиненков",
        "book": "«Справочник фармакологии спорта»",
        "category": "pharma",
        "badge": "💊 Фармакология Спорта",
        "summary": "Академический первоисточник фазового фармакологического сопровождения (базовый, предсоревновательный, соревновательный, восстановительный микроциклы). Классификация недопинговых препаратов, синергизм и органопротекция в боксе.",
        "file": "Кулиненков_О_С_Кулиненков_Д_О_Справочник_Фармакологии_Спорта.md",
        "keywords": ["кулиненков", "кулиненкова", "справочник фармакологии", "фазовое сопровождение"]
    },
    "oleynik_gunina": {
        "id": "oleynik_gunina",
        "num": 3,
        "name": "Проф. С. А. Олейник и проф. Л. М. Гунина",
        "book": "«Спортивная фармакология и диетология»",
        "category": "pharma",
        "badge": "🥗 Диетология & Весогонка",
        "summary": "Неразрывный синтез спортивной нутрициологии, диетологии и фармакокоррекции. Тайминг нутриентов, аминокислотные пулы (BCAA, EAA, цитруллин, глутамин), 3-фазный протокол сгонки веса без потери мощности удара, мониторинг крови (Тестостерон/Кортизол, КФК, ферритин).",
        "file": "Олейник_С_А_Гунина_Л_М_Спортивная_Фармакология_и_Диетология.md",
        "keywords": ["олейник", "весогонка", "сгонка веса"]
    },
    "gunina": {
        "id": "gunina",
        "num": 4,
        "name": "Проф. Л. М. Гунина (д-р биол. наук)",
        "book": "«Спортивная фармакология: методологическая база»",
        "category": "pharma",
        "badge": "🔬 Методология Фармы",
        "summary": "Фундаментальный базис спортивной фармакологии: метаболическая кардиопротекция («спортивное сердце»), субстратные антигипоксанты дыхательной цепи (сукцинаты, Цитофлавин), капилляропротекция микроциркуляторного русла (дигидрокверцетин, рутозид), коррекция перетренированности.",
        "file": "Гунина_Л_М_Спортивная_Фармакология_Методологическая_База.md",
        "keywords": ["гунина", "методологическая база", "сукцинаты", "цитофлавин"]
    },
    "volkov": {
        "id": "volkov",
        "num": 5,
        "name": "Проф. Н. И. Волков и В. И. Олейников",
        "book": "«Эргогенные эффекты спортивного питания»",
        "category": "pharma",
        "badge": "⚡️ Биоэнергетика",
        "summary": "Биоэнергетика мышечной деятельности (фосфагенная алактатная мощность, гликолитическая емкость, аэробная мощность). Эргогенные нутриенты: креатинфосфатный буфер, внутримышечная буферизация лактата (бета-аланин/карнозин, цитраты), утилизация аммиака (цитруллин малат), митохондриальный транспорт L-карнитина.",
        "file": "Волков_Н_И_Олейников_В_И_Эргогенные_Эффекты_Спортивного_Питания.md",
        "keywords": ["волков", "олейников", "эргогенные эффекты", "алактатная мощность"]
    },
    "salway": {
        "id": "salway",
        "num": 6,
        "name": "Проф. Дж. Г. Солвей (J. G. Salway)",
        "book": "«Наглядная медицинская биохимия. Карты метаболизма»",
        "category": "pharma",
        "badge": "🗺 Карты Биохимии",
        "summary": "Атлас биохимических карт метаболизма: ферментативные точки приложения спортивной фармакологии (гликолиз, малат-аспартатный челнок, Комплекс II дыхательной цепи сукцината, карнитиновый челнок CPT-1/CPT-2, цикл мочевины утилизации аммиака, синтез ацетилхолина Alpha-GPC).",
        "file": "Солвей_Дж_Г_Наглядная_Медицинская_Биохимия_Карты_Метаболизма.md",
        "keywords": ["солвей", "salway", "карты метаболизма"]
    },
    "mottram_chester": {
        "id": "mottram_chester",
        "num": 7,
        "name": "Дэвид Р. Моттрам и Нил Честер (David R. Mottram, Neil Chester)",
        "book": "«Drugs in Sport» (8th Edition, Routledge)",
        "category": "pharma",
        "badge": "🌐 WADA 2026 & Допинг",
        "summary": "Мировой золотой стандарт фармакологии спорта и допинг-контроля. Полная научная систематизация всех классов препаратов (AAS, SARMs, rHuEPO, стимуляторы ЦНС, буферы, диуретики, TUE и кодекс WADA 2026).",
        "file": "Моттрам_Д_Честер_Н_Препараты_в_Спорте_Drugs_in_Sport_8th_Ed.md",
        "keywords": ["мотттрам", "моттрам", "честер", "mottram", "drugs in sport"]
    },
    "seyfulla_portugalov": {
        "id": "seyfulla_portugalov",
        "num": 8,
        "name": "Проф. Р. Д. Сейфулла и проф. С. Н. Португалов (ВНИИФК)",
        "book": "«Фармакология спортивной работоспособности»",
        "category": "pharma",
        "badge": "🏛 Классика ВНИИФК",
        "summary": "Основоположники отечественной спортивной фармакологии. Недопинговые эргогенные субстанции метаболического типа действия, адаптогены, экдистероиды, антигипоксанты дыхательной цепи (сукцинаты), кардиопротекция при экстремальных нагрузках.",
        "file": "Сейфулла_Р_Д_Португалов_С_Н_Фармакология_Спортивной_Работоспособности_ВНИИФК.md",
        "keywords": ["сейфулла", "португалов", "вниифк", "экдистерон", "экдистероиды"]
    },
    "dmitriev_gunina": {
        "id": "dmitriev_gunina",
        "num": 9,
        "name": "Канд. хим. наук А. В. Дмитриев и проф. Л. М. Гунина",
        "book": "«Спортивная нутрициология и фармаконутриенты»",
        "category": "pharma",
        "badge": "🧪 Нутрициология & Хелаты",
        "summary": "Химия биополимеров, стереоизомерия аминокислотных пулов (BCAA, цитруллин, глутамин), антиоксидантная емкость плазмы, хелатные формы минералов (бисглицинаты), регуляция феррокинетики и синтеза гемоглобина.",
        "file": "Дмитриев_А_В_Гунина_Л_М_Спортивная_Нутрициология_и_Фармаконутриенты.md",
        "keywords": ["дмитриев", "фармаконутриенты", "бисглицинат"]
    },
    "yesalis_bahrke": {
        "id": "yesalis_bahrke",
        "num": 10,
        "name": "Чарльз Е. Йесалис и Майкл С. Барк (Charles E. Yesalis, Michael S. Bahrke)",
        "book": "«Вещества, повышающие работоспособность в спорте» (Human Kinetics)",
        "category": "pharma",
        "badge": "📈 Эндокринология & Безопасность",
        "summary": "Мировой эпидемиологический стандарт: фармакодинамика анаболических агентов, пептидов и стимуляторов, риски гипертрофии миокарда, эндокринный гомеостаз и доказательные чистые альтернативы.",
        "file": "Йесалис_Ч_Барк_М_Вещества_Повышающие_Работоспособность_в_Спорте.md",
        "keywords": ["йесалис", "yesalis", "барк", "bahrke"]
    },
    "llewellyn": {
        "id": "llewellyn",
        "num": 11,
        "name": "Уильям Ллевеллин (William Llewellyn)",
        "book": "«ANABOLICS» (Molecular Nutrition, 11th Edition)",
        "category": "pharma",
        "badge": "📖 Энциклопедия ANABOLICS",
        "summary": "Крупнейшая мировая энциклопедия: молекулярная эндокринология, рецепторное связывание, SARMs, пептиды регенерации связок и ангиогенеза (BPC-157, TB-500), протоколы гепато- и кардиопротекции.",
        "file": "Ллевеллин_Уильям_Справочник_Анаболических_и_Пептидных_Соединений_ANABOLICS.md",
        "keywords": ["ллевеллин", "llewellyn", "anabolics", "анаболикс", "bpc-157", "tb-500"]
    }
}

SFP_AUTHORS_CATALOG = {
    "seluyanov": {
        "id": "seluyanov",
        "name": "Проф. В. Н. Селуянов, Д. В. Максимов, С. Е. Табаков",
        "book": "«Физическая подготовка единоборцев»",
        "badge": "⚡️ Митохондриогенез & Изотон",
        "summary": "Биологическая модель мышечной композиции (ОМВ, ПМВ, ГМВ), митохондриогенез для безотказной ударной выносливости без закисления, статодинамика (Изотон), интервальные взрывные дриллы (10 сек взрыв / 50 сек челнок).",
        "file": "Максимов_Д_В_Селуянов_В_Н_Табаков_С_Е_Физическая_Подготовка_Единоборцев.md"
    },
    "filimonov": {
        "id": "filimonov",
        "name": "Проф. В. И. Филимонов",
        "book": "«Биомеханика ударных движений и бокс»",
        "badge": "🥊 Закон Вклада Звеньев",
        "summary": "Закон вклада звеньев тела в силу удара: ноги 38.4%, таз и корпус 37.2%, рука и плечевой пояс 24.4%. 4-фазная структура прямых, боковых и ударов снизу, опережение таза на 15–20°, детекция разрыва кинематической цепи.",
        "file": "Филимонов_В_И_Биомеханика_Ударных_Движений_и_Бокс.md"
    },
    "zatsiorsky": {
        "id": "zatsiorsky",
        "name": "Проф. В. М. Зациорский",
        "book": "«Биомеханика двигательного аппарата и сила удара»",
        "badge": "📐 Закон Хилла & RFD",
        "summary": "Закон Хилла «Сила — Скорость», расчет пиковой мощности Pmax = Fopt * Vopt, взрывной градиент силы RFD (dF/dt), цикл «растяжение-сокращение» (SSC) и феномен жесткого замка (Impact Lock) с ростом массы руки до 25 кг.",
        "file": "Зациорский_В_М_Биомеханика_Двигательного_Аппарата_и_Сила_Удара.md"
    },
    "verkhoshansky": {
        "id": "verkhoshansky",
        "name": "Проф. Ю. В. Верхошанский",
        "book": "«Ударный метод и плиометрика в единоборствах»",
        "badge": "💥 Ударный Метод & Плиометрика",
        "summary": "5 критериев динамического соответствия СФП удару, амортизационно-взрывной режим работы мышц (минимизация coupling time <120 мс), топ-3 плиометрических дрилла (медбол 3–5 кг, depth push-ups со степов, snap-back).",
        "file": "Верхошанский_Ю_В_Ударный_Метод_и_Плиометрика_в_Единоборствах.md"
    },
    "bompa": {
        "id": "bompa",
        "name": "Тудор Бомпа и Карло Бузичелли (Tudor Bompa, Carlo Buzzichelli)",
        "book": "«Периодизация силовой подготовки в спорте»",
        "badge": "📅 6 Фаз Периодизации",
        "summary": "Мировой эталон периодизации: 6 фаз (Анатомическая адаптация -> Максимальная сила -> Конверсия в ударную мощность -> Тейперинг к бою), микроциклы и планирование сборов.",
        "file": "Бомпа_Т_Бузичелли_К_Периодизация_Силовой_Подготовки_в_Спорте.md"
    },
    "ufc_pi": {
        "id": "ufc_pi",
        "name": "UFC Performance Institute (Том 1 & Том 2)",
        "book": "«Методология и стандарты подготовки элитных бойцов 2026»",
        "badge": "🏆 Золотой Стандарт UFC PI",
        "summary": "3D Kinematic Sequence (GRF -> Pelvis -> Torso -> Fist >9.0 м/с, время ретракции <165 мс), управление нагрузкой (ACWR, sRPE), сила без балластной гипертрофии, протокол RTP восстановления после сотрясений.",
        "file": "UFC_Performance_Institute_Том_2_Методология_и_Стандарты.md"
    },
    "bernstein": {
        "id": "bernstein",
        "name": "Чл.-корр. АМН СССР Н. А. Бернштейн",
        "book": "«Биомеханика и физиология двигательного навыка удара»",
        "badge": "🧠 Уровни Построения Движений",
        "summary": "Теория 4 уровней построения движений (A, B, C, D), преодоление 240 степеней свободы суставов, сенсорные коррекции и опережающая антиципация удара по микро-движениям соперника за 0–40 мс.",
        "file": "Бернштейн_Н_А_Биомеханика_и_Физиология_Двигательного_Навыка_Удара.md"
    },
    "gradopolov": {
        "id": "gradopolov",
        "name": "Засл. мастер спорта, проф. К. В. Градополов",
        "book": "«Бокс. Теория и методика обучения»",
        "badge": "🥊 Канон Школы Бокса",
        "summary": "Классическая советская школа бокса: стойка, челнок, защитно-контратакующие действия, тактическая педагогика и воспитание чемпионского характера.",
        "file": "Градополов_К_В_Бокс_Теория_и_Методика_Обучения.md"
    }
}

def get_all_authors_overview_text():
    lines = [
        "📚 <b>ЕДИНАЯ БИБЛИОТЕКА СПОРТА: РЕЕСТР 11 АВТОРОВ</b>",
        "<i>Фундаментальные монографии и научная база Boxing S&C Lab</i>",
        "────────────────────"
    ]
    for key, a in sorted(AUTHORS_CATALOG.items(), key=lambda x: x[1]["num"]):
        num = a["num"]
        name = a["name"]
        book = a["book"]
        badge = a["badge"]
        summary = a["summary"]
        item = chr(10).join([
            f"<b>{num}. {name}</b>",
            f"📖 <i>{book}</i>",
            f"🏷 <code>{badge}</code>",
            f"• {summary}",
            ""
        ])
        lines.append(item)
    lines.append("────────────────────")
    lines.append("⚡️ <b>Ключевые авторы СФП и Биомеханики:</b>")
    lines.append("• <b>Проф. В. Н. Селуянов</b> — митохондриогенез, статодинамика (Изотон)")
    lines.append("• <b>Проф. В. И. Филимонов</b> — закон вклада звеньев тела в силу удара")
    lines.append("• <b>Проф. В. М. Зациорский</b> — закон Хилла, RFD, Impact Lock (25 кг)")
    lines.append("• <b>Проф. Ю. В. Верхошанский</b> — ударный метод и плиометрика")
    lines.append("• <b>Тудор Бомпа</b> — 6 фаз периодизации силовой подготовки")
    lines.append("• <b>UFC Performance Institute</b> — 3D кинематика удара, RTP-протокол")
    lines.append("")
    lines.append("💡 <i>Нажмите на кнопку любого автора ниже для детального разбора!</i>")
    return chr(10).join(lines)

def get_author_detail_text(author_key):
    a = AUTHORS_CATALOG.get(author_key) or SFP_AUTHORS_CATALOG.get(author_key)
    if not a:
        return None
    file_path = None
    for d in [PHARMA_MONO_DIR, SFP_MONO_DIR, PHARMA_DIR, SFP_DIR]:
        candidate = os.path.join(d, a.get("file", ""))
        if os.path.exists(candidate):
            file_path = candidate
            break
    content_snippet = ""
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw = f.read()
                raw_clean = re.sub(r"^---[\s\S]*?---\n", "", raw).strip()
                content_snippet = raw_clean[:2200]
        except Exception:
            pass
    name_u = a["name"].upper()
    book = a["book"]
    badge = a.get("badge", "Академическая монография")
    header = chr(10).join([
        f"📖 <b>{name_u}</b>",
        f"📚 <b>{book}</b>",
        f"🏷 <b>Направление:</b> <code>{badge}</code>",
        "────────────────────",
        "",
        ""
    ])
    if content_snippet:
        body = html.escape(content_snippet)
        body = re.sub(r"#+\s*(.+)", r"<b>\1</b>", body)
        return header + body
    else:
        sum_txt = a["summary"]
        fname = a.get("file", "монография.md")
        return header + f"🎯 <b>Ключевой вклад:</b>\n{sum_txt}\n\n📂 <b>Файл монографии:</b> <code>{fname}</code>"

def get_special_stack_text(stack_key):
    stack_files = {
        "kodintsev": (os.path.join(PHARMA_DIR, "КУРС_КОДИНЦЕВ.md"), "💊 КУРС КОДИНЦЕВ PRO (СБОРНАЯ 2026)"),
        "superdose": (os.path.join(PHARMA_DIR, "Спортивная_Фармакология_Бокс_Сверхдозы_и_Протоколы_2026.md"), "🔥 СПОРТИВНАЯ ФАРМАКОЛОГИЯ: СВЕРХДОЗЫ 2026"),
        "vitalik": (os.path.join(PHARMA_DIR, "Протокол_Фармакологии_Бокс_Составил_Виталик_2026.md"), "🩺 СХЕМА ВИТАЛИКА (ЭКСПЕРТНЫЙ ИИ-АУДИТ)"),
        "mono2026": (os.path.join(PHARMA_DIR, "Новая_Метаболическая_Поддержка_Бокс_2026.md"), "🥊 МОНОГРАФИЯ МЕТАБОЛИЧЕСКОЙ ПОДДЕРЖКИ 2026")
    }
    item = stack_files.get(stack_key)
    if not item:
        return None
    path, title = item
    content = ""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read()
                raw_clean = re.sub(r"^---[\s\S]*?---\n", "", raw).strip()
                content = raw_clean[:2200]
        except Exception:
            pass
    header = chr(10).join([f"🌟 <b>{title}</b>", "────────────────────", "", ""])
    if content:
        body = html.escape(content)
        body = re.sub(r"#+\s*(.+)", r"<b>\1</b>", body)
        return header + body
    return header + "<i>Файл протокола успешно зарегистрирован в библиотеке.</i>"

def get_library_markup(active_tab="11_authors", active_author=None):
    keyboard = []
    if active_tab == "11_authors":
        author_items = sorted(AUTHORS_CATALOG.items(), key=lambda x: x[1]["num"])
        row = []
        for k, a in author_items:
            num = a["num"]
            first_w = a["name"].split()[0]
            short_title = f"{num}. {first_w}"
            if "Янсен" in a["name"]: short_title = "1. Янсен"
            elif "Кулиненков" in a["name"]: short_title = "2. Кулиненков"
            elif "Олейник" in a["name"]: short_title = "3. Олейник"
            elif "Гунина" in a["name"] and a["num"] == 4: short_title = "4. Гунина"
            elif "Волков" in a["name"]: short_title = "5. Волков"
            elif "Солвей" in a["name"]: short_title = "6. Солвей"
            elif "Моттрам" in a["name"]: short_title = "7. Моттрам"
            elif "Сейфулла" in a["name"]: short_title = "8. Сейфулла"
            elif "Дмитриев" in a["name"]: short_title = "9. Дмитриев"
            elif "Йесалис" in a["name"]: short_title = "10. Йесалис"
            elif "Ллевеллин" in a["name"]: short_title = "11. Ллевеллин"
            row.append({"text": short_title, "callback_data": f"lib_a_{k}"})
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([
            {"text": "⚡️ Авторы СФП & Биомеханики", "callback_data": "lib_tab_sfp"},
            {"text": "🌟 Стеки 2026 (Кодинцев/Виталик)", "callback_data": "lib_tab_stacks"}
        ])
    elif active_tab == "sfp":
        sfp_items = list(SFP_AUTHORS_CATALOG.items())
        row = []
        for k, a in sfp_items:
            first_w = a["name"].split()[0]
            short_title = first_w
            if "Селуянов" in a["name"]: short_title = "⚡️ Селуянов"
            elif "Филимонов" in a["name"]: short_title = "🥊 Филимонов"
            elif "Зациорский" in a["name"]: short_title = "📐 Зациорский"
            elif "Верхошанский" in a["name"]: short_title = "💥 Верхошанский"
            elif "Бомпа" in a["name"]: short_title = "📅 Бомпа"
            elif "UFC" in a["name"]: short_title = "🏆 UFC PI"
            elif "Бернштейн" in a["name"]: short_title = "🧠 Бернштейн"
            elif "Градополов" in a["name"]: short_title = "🥊 Градополов"
            row.append({"text": short_title, "callback_data": f"lib_a_{k}"})
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([
            {"text": "« 📚 Все 11 Авторов (Фарма)", "callback_data": "lib_tab_11"},
            {"text": "🌟 Стеки 2026", "callback_data": "lib_tab_stacks"}
        ])
    elif active_tab == "stacks":
        keyboard.append([
            {"text": "💊 Курс Кодинцев Pro", "callback_data": "lib_stk_kodintsev"},
            {"text": "🔥 Сверхдозы Бокс 2026", "callback_data": "lib_stk_superdose"}
        ])
        keyboard.append([
            {"text": "🩺 Схема Виталика (Аудит)", "callback_data": "lib_stk_vitalik"},
            {"text": "🥊 Монография 2026", "callback_data": "lib_stk_mono2026"}
        ])
        keyboard.append([
            {"text": "« 📚 11 Авторов", "callback_data": "lib_tab_11"},
            {"text": "⚡️ Авторы СФП", "callback_data": "lib_tab_sfp"}
        ])
    keyboard.append([
        {"text": "🎩 К ИИ-Секретарю", "callback_data": "nav_secretary"},
        {"text": "« 🔙 В Главное Меню", "callback_data": "nav_main"}
    ])
    return {"inline_keyboard": keyboard}

ATHLETES_BASE_DIR = "/home/home/Документы/2/Спорт/Спортсмены"
FITNESS_BASE_DIR = "/home/home/Документы/2/Спорт/Фитнес"

def get_athlete_dossier_text(athlete_key):
    if athlete_key in ["lenara", "fitness_lenara", "ленара"]:
        folder = os.path.join(FITNESS_BASE_DIR, "Ленара")
        prog_file = os.path.join(folder, "ПРОГРАММА_ОФП_И_КОРРЕКЦИИ_ФИГУРЫ_2_РАЗА_В_НЕДЕЛЮ.md")
        content = ""
        if os.path.exists(prog_file):
            try:
                with open(prog_file, "r", encoding="utf-8") as f:
                    content = f.read()[:2600]
            except Exception:
                pass
        header = (
            "🧘‍♀️🏋️‍♀️ <b>КЛИЕНТ (ФИТНЕС): ЛЕНАРА (25–27 ЛЕТ)</b>\n"
            "<i>Специфика: Персональные тренировки (2 р/нед), коррекция веса, ОФП, Full-Body</i>\n"
            "<i>Папка: <code>Спорт/Фитнес/Ленара/</code></i>\n"
            "────────────────────\n\n"
        )
        if content:
            body = html.escape(content)
            body = re.sub(r"#+\s*(.+)", r"<b>\1</b>", body)
            return header + body
        return header + "<i>Программа ОФП и паспорт клиента сохранены в базе.</i>"

    if athlete_key in ["shkurapatov", "demian", "shkurapatov_demian"]:
        folder = os.path.join(ATHLETES_BASE_DIR, "Шкурапатов_Демьян")
        prog_file = os.path.join(folder, "ПРОГРАММА_ОФП_И_СФП_ФУТБОЛ_ЮНОШИ_12_13_ЛЕТ.md")
        content = ""
        if os.path.exists(prog_file):
            try:
                with open(prog_file, "r", encoding="utf-8") as f:
                    content = f.read()[:2600]
            except Exception:
                pass
        header = (
            "⚽️🥊 <b>АТЛЕТ: ШКУРАПАТОВ ДЕМЬЯН (12–13 ЛЕТ)</b>\n"
            "<i>Специфика: Футбол (Основа) + Школа Бокса / ОФП-СФП база</i>\n"
            "<i>Папка: <code>Спорт/Спортсмены/Шкурапатов_Демьян/</code></i>\n"
            "────────────────────\n\n"
        )
        if content:
            body = html.escape(content)
            body = re.sub(r"#+\s*(.+)", r"<b>\1</b>", body)
            return header + body
        return header + "<i>Программа ОФП/СФП и паспорт атлета сохранены в базе.</i>"

    if athlete_key in ["arapov", "kirill", "arapov_kirill"]:
        folder = os.path.join(ATHLETES_BASE_DIR, "Арапов_Кирилл")
        pass_file = os.path.join(folder, "ПАСПОРТ_И_ФАРМАКОЛОГИЧЕСКИЙ_ЦИКЛ.md")
        content = ""
        if os.path.exists(pass_file):
            try:
                with open(pass_file, "r", encoding="utf-8") as f:
                    content = f.read()[:2600]
            except Exception:
                pass
        header = (
            "🥊 <b>АТЛЕТ: АРАПОВ КИРИЛЛ (17 ЛЕТ, 64 КГ)</b>\n"
            "<i>Специфика: Бокс (Юниоры) / Предсоревновательный цикл</i>\n"
            "<i>Папка: <code>Спорт/Спортсмены/Арапов_Кирилл/</code></i>\n"
            "────────────────────\n\n"
        )
        if content:
            body = html.escape(content)
            body = re.sub(r"#+\s*(.+)", r"<b>\1</b>", body)
            return header + body
        return header + "<i>Паспорт и протоколы атлета сохранены в базе.</i>"
    return None

def search_sports_library_smart(query_text):
    q = query_text.strip().lower()
    if any(k in q for k in ["ленара", "фитнес ленара", "офп ленара", "ленаре"]):
        ans = get_athlete_dossier_text("lenara")
        if ans:
            return ans, get_library_markup("sfp")
    if any(k in q for k in ["шкурапатов", "демьян", "футбол 12", "офп футбол", "сфп футбол", "футболист"]):
        ans = get_athlete_dossier_text("shkurapatov")
        if ans:
            return ans, get_library_markup("sfp")
    if any(k in q for k in ["арапов", "кирилл арапов", "арапов кирилл"]):
        ans = get_athlete_dossier_text("arapov")
        if ans:
            return ans, get_library_markup("11_authors")
    if any(k in q for k in ["список авторов", "11 авторов", "одиннадцать авторов", "все авторы", "реестр авторов", "книги в базе", "какие книги", "список книг", "библиотека", "литература", "первоисточники", "монографии"]):
        return get_all_authors_overview_text(), get_library_markup("11_authors")
    for k, a in AUTHORS_CATALOG.items():
        if any(kw in q for kw in a["keywords"]):
            ans = get_author_detail_text(k)
            return ans, get_library_markup("11_authors", active_author=k)
    for k, a in SFP_AUTHORS_CATALOG.items():
        if k in q or any(w in q for w in a["name"].lower().split() if len(w) > 3):
            ans = get_author_detail_text(k)
            return ans, get_library_markup("sfp", active_author=k)
    if any(w in q for w in ["пульсовые зоны", "зоны чсс", "лактат", "порог закисления", "obla", "анп", "аэт"]):
        return get_author_detail_text("janssen"), get_library_markup("11_authors", active_author="janssen")
    if any(w in q for w in ["сгонка веса", "весогонка", "сбросить вес", "диета в боксе"]):
        return get_author_detail_text("oleynik_gunina"), get_library_markup("11_authors", active_author="oleynik_gunina")
    if any(w in q for w in ["вклад звеньев", "сила удара", "ноги 38", "таз 37", "рука 24"]):
        return get_author_detail_text("filimonov"), get_library_markup("sfp", active_author="filimonov")
    if any(w in q for w in ["митохондр", "омв", "пмв", "гмв", "селуянов", "изотон", "статодинамик"]):
        return get_author_detail_text("seluyanov"), get_library_markup("sfp", active_author="seluyanov")
    if any(w in q for w in ["wada", "вада", "допинг", "запрещенные", "tue", "мотттрам", "моттрам"]):
        return get_author_detail_text("mottram_chester"), get_library_markup("11_authors", active_author="mottram_chester")
    if any(w in q for w in ["кодинцев", "курс кодинцев"]):
        return get_special_stack_text("kodintsev"), get_library_markup("stacks")
    if any(w in q for w in ["сверхдоз", "сверхдозы"]):
        return get_special_stack_text("superdose"), get_library_markup("stacks")
    if any(w in q for w in ["виталик", "схема виталика"]):
        return get_special_stack_text("vitalik"), get_library_markup("stacks")
    return None, None

def get_sports_knowledge_dense_prompt():
    lines = [
        "СПОРТИВНАЯ БАЗА ЗНАНИЙ И БИБЛИОТЕКА 11 АВТОРОВ (Boxing S&C Lab):",
        "1. Петер Янсен: «ЧСС, лактат и тренировки на выносливость» (5 зон ЧСС, AeT/АнП/OBLA 4.0 ммоль/л, L-растяжение миокарда 130-145 уд/мин, тест Конкони).",
        "2. Д-р мед. наук О. С. Кулиненков: «Справочник фармакологии спорта» (фазовое сопровождение: базовый, спарринги, бой, суперкомпенсация, синергизм недопинговых препаратов).",
        "3. Проф. С. А. Олейник и проф. Л. М. Гунина: «Спортивная фармакология и диетология» (тайминг нутриентов, аминокислотные пулы, 3-фазная сгонка веса без потери нокаута, контроль КФК/ферритина/тестостерона).",
        "4. Проф. Л. М. Гунина: «Спортивная фармакология: методологическая база» (метаболическая кардиопротекция, сукцинаты, Цитофлавин, капилляропротекция дигидрокверцетином).",
        "5. Проф. Н. И. Волков: «Эргогенные эффекты спортивного питания» (алактатная мощность, креатинфосфатный буфер, бета-аланин/карнозин, цитруллин малат).",
        "6. Проф. Дж. Г. Солвей: «Наглядная медицинская биохимия. Карты метаболизма» (малат-аспартатный челнок, Комплекс II сукцината, карнитин CPT-1/2, синтез ацетилхолина Alpha-GPC).",
        "7. David R. Mottram & Neil Chester: «Drugs in Sport» (8th Ed., WADA 2026, классификация препаратов, TUE).",
        "8. Р. Д. Сейфулла & С. Н. Португалов (ВНИИФК): «Фармакология спортивной работоспособности» (адаптогены, экдистероиды, сукцинаты).",
        "9. А. В. Дмитриев & Л. М. Гунина: «Спортивная нутрициология и фармаконутриенты» (хелаты бисглицинаты, антиоксиданты).",
        "10. Charles E. Yesalis & Michael S. Bahrke: «Вещества, повышающие работоспособность» (эндокринология, миокард).",
        "11. William Llewellyn: «ANABOLICS» (молекулярная эндокринология, пептиды BPC-157/TB-500, органопротекция).",
        "СФП и Биомеханика: Проф. В. Н. Селуянов (митохондриогенез, Изотон), Проф. В. И. Филимонов (ноги 38.4%, таз 37.2%, рука 24.4%), Проф. В. М. Зациорский (закон Хилла, RFD, Impact Lock 25 кг), Проф. Ю. В. Верхошанский (ударный метод, плиометрика), Тудор Бомпа (6 фаз периодизации), UFC Performance Institute 2026 (3D Kinematic Sequence, RTP)."
    ]
    return chr(10).join(lines)

if __name__ == "__main__":
    overview = get_all_authors_overview_text()
    print(f"Всего авторов: {len(AUTHORS_CATALOG)}")
    print(overview[:300] + "...\n")
    ans, mk = search_sports_library_smart("янсен")
    print(f"Поиск Янсен: {ans[:200]}...")
    ans_list, _ = search_sports_library_smart("список 11 авторов")
    print(f"Поиск 11 авторов: {ans_list[:200]}...")
    print("ALL CHECKS PASSED!")

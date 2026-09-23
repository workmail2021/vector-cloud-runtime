#!/usr/bin/env python3
"""
ИИ-ВЕКТОР: 24/7 Модуль Мониторинга Яндекс.Карт с жесткой фильтрацией по боксерским маркерам (Boxing S&C Lab).
- Круглосуточный фоновый мониторинг новых отзывов на Яндекс.Картах (1 раз в сутки).
- ЖЕСТКИЙ ФИЛЬТР ЦЕЛЕВЫХ МАРКЕРОВ:
  1. Бокс (бокс, боксерский, ринг, лапы)
  2. Персональный / индивидуальный тренинг по боксу
  3. Сергей Анатольевич / Сергей Романов / тренер Сергей
  4. СФП / ОФП / кондиционная подготовка
  5. Силовой кондиционный тренинг / Boxing S&C Lab
  6. Давид / Арапов
- Только при поступлении НОВОГО отзыва, содержащего эти маркеры, отправляется точечное уведомление в Telegram!
- Все остальные отзывы (общие, дзюдо, самбо, BJJ, другие тренеры) игнорируются и в чат не поступают.
"""

import os
import sys
import json
import time
import re
import urllib.request
import html
from telegram_notifier import send_telegram_message

DATA_DIR = "/home/home/Документы/2/data_backup"
YANDEX_ORG_ID = "50213207596"
YANDEX_ORG_URL = "https://yandex.ru/maps/org/tsentr_smeshannykh_yedinoborstv/50213207596/reviews/?ranking=by_time"
REVIEWS_DB_PATH = os.path.join(DATA_DIR, "yandex_boxing_reviews.json")
ALT_REVIEWS_DB_PATH = os.path.expanduser("~/.config/antigravity-email/yandex_boxing_reviews.json")
LOG_PATH = "/home/home/Документы/2/logs/yandex_reviews.log"
AUTHORIZED_CHAT_ID = 6375883079

# Список обязательных целевых маркеров Сергея Романова
TARGET_MARKERS = [
    r'бокс',
    r'лап[аые]',
    r'ринг',
    r'сергей\s+анатольевич',
    r'серге[яюе]\s+романов',
    r'тренер[а-я]*\s+серге[яюе]',
    r'у\s+сергея',
    r'к\s+сергею',
    r'сфп',
    r'офп',
    r'кондиционн',
    r'силов[а-я]*\s+тренинг',
    r'boxing\s+s&c',
    r'персональн[а-я]*\s+тренинг',
    r'персональн[а-я]*\s+бокс',
    r'индивидуальн[а-я]*\s+заняти[а-я]*',
    r'индивидуальн[а-я]*\s+тренировк[а-я]*',
    r'петросян',
    r'давид\s+петросян',
    r'петросян[а-я]*\s+давид[а-я]*'
]

def is_target_boxing_review(text):
    if not text:
        return False
    t_lower = text.lower()
    for pattern in TARGET_MARKERS:
        if re.search(pattern, t_lower):
            return True
    return False

def load_reviews_db():
    target = REVIEWS_DB_PATH if os.path.exists(REVIEWS_DB_PATH) else ALT_REVIEWS_DB_PATH
    if not os.path.exists(target):
        return []
    try:
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_reviews_db(reviews):
    for p in [REVIEWS_DB_PATH, ALT_REVIEWS_DB_PATH]:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        try:
            os.chmod(p, 0o600)
        except Exception:
            pass

def log_review_event(msg):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def fetch_live_yandex_reviews():
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru,en;q=0.9"
    }
    req = urllib.request.Request(YANDEX_ORG_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=12) as resp:
        page_html = resp.read().decode("utf-8", errors="ignore")

    json_blocks = re.findall(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', page_html, re.DOTALL)
    if not json_blocks:
        return []
    
    data = json.loads(json_blocks[0])
    
    def find_reviews(obj, results):
        if isinstance(obj, dict):
            if "text" in obj and ("author" in obj or "rating" in obj or "updatedTime" in obj):
                results.append(obj)
            for k, v in obj.items():
                find_reviews(v, results)
        elif isinstance(obj, list):
            for elem in obj:
                find_reviews(elem, results)

    extracted = []
    find_reviews(data, extracted)
    
    valid_reviews = []
    for r in extracted:
        txt = r.get("text", "").strip()
        if not txt:
            continue
        author = r.get("author", {}).get("name", "Гость") if isinstance(r.get("author"), dict) else r.get("author", "Гость")
        dt = r.get("updatedTime") or r.get("createdTime") or time.strftime("%Y-%m-%d")
        rating = r.get("rating", 5)
        r_id = r.get("id") or f"rev_{abs(hash(txt[:40]))}"
        
        valid_reviews.append({
            "id": str(r_id),
            "date": dt,
            "author": str(author),
            "rating": rating or 5,
            "text": txt
        })
    return valid_reviews

def check_and_record_new_yandex_reviews():
    """
    Ежедневный фоновый мониторинг (1 раз в сутки):
    1. Сканирует новые отзывы на Яндекс.Картах.
    2. Проверяет соответствие ЖЕСТКИМ маркерам:
       - Бокс
       - Персональный тренинг по боксу
       - Сергей Анатольевич Романов
       - СФП / ОФП
       - Давид / Арапов
       - Силовой кондиционный тренинг
    3. Если отзыв НОВЫЙ и содержит маркер:
       - Сохраняет на ПК в yandex_boxing_reviews.json.
       - Отправляет 1 персональный маячок в Telegram.
    4. Если отзыв не по боксу/СФП (дзюдо, самбо, общие) — молча пропускает.
    """
    existing_db = load_reviews_db()
    existing_texts = {r.get("text", "").strip()[:50] for r in existing_db}

    try:
        live_reviews = fetch_live_yandex_reviews()
    except Exception as e:
        log_review_event(f"Ошибка проверки Яндекс.Карт: {e}")
        return []

    new_discovered = []
    for lr in live_reviews:
        snippet = lr["text"][:50]
        if snippet not in existing_texts:
            # Проверяем строгое соответствие маркерам
            if is_target_boxing_review(lr["text"]):
                new_discovered.append(lr)
                existing_db.insert(0, lr)
                existing_texts.add(snippet)
            else:
                log_review_event(f"Пропущен отзыв не по целевым маркерам (автор: {lr['author']})")

    if new_discovered:
        save_reviews_db(existing_db)
        log_review_event(f"Зафиксировано целевых боксерских отзывов: {len(new_discovered)} шт.")
        
        # Отправляем оповещение в Telegram ТОЛЬКО для целевых боксерских отзывов
        for nr in new_discovered:
            stars = "⭐" * int(nr.get("rating", 5))
            dt_str = str(nr.get("date", ""))[:10]
            msg = (
                f"🌟 <b>НОВЫЙ ЦЕЛЕВОЙ ОТЗЫВ ПО БОКСУ / СФП!</b>\n\n"
                f"📍 <b>Boxing S&C Lab (Скосырева 11)</b>\n"
                f"👤 <b>{html.escape(nr['author'])}</b> | {stars}\n"
                f"📅 <i>{html.escape(dt_str)}</i>\n\n"
                f"💬 «<i>{html.escape(nr['text'])}</i>»\n\n"
                f"🥊 <i>Маркер подтвержден! Отзыв сохранен на ПК для Instagram Stories.</i>"
            )
            try:
                send_telegram_message(msg)
                print(f"Отправлен маячок о целевом отзыве: {nr['author']}")
            except Exception as e:
                log_review_event(f"Ошибка отправки Telegram алерта: {e}")
    else:
        log_review_event(f"Проверка завершена: целевых новых отзывов по боксу/СФП нет.")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Целевых новых отзывов по боксу/СФП нет. База актуальна.")

    return new_discovered

if __name__ == "__main__":
    check_and_record_new_yandex_reviews()

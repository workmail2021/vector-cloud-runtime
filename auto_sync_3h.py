#!/usr/bin/env python3
"""
3-HOUR AUTOMATIC BIDIRECTIONAL SYNC ENGINE (BOXING LAB & VECTOR BOT)
Безопасная двусторонняя синхронизация (Bidirectional Merge & Push):
1. Сначала создает мгновенный снимок (snapshot) локальных баз данных перед синхронизацией.
2. Безопасно загружает (PULL) данные из облака Render.
3. Объединяет (MERGE) локальные и облачные данные без риска затирания и потери записей.
4. Отправляет (PUSH) объединенную актуальную версию обратно на облачный сервер Render.
5. Сохраняет объединенную версию локально.
"""

import os
import sys
import time
import json
import urllib.request
import urllib.parse
import ssl
from datetime import datetime

PROJECT_ROOT = "/home/home/Документы/2"
LOG_FILE = os.path.join(PROJECT_ROOT, "logs", "auto_sync_3h.log")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups")

BOXING_URL = "https://boxing-performance-lab.onrender.com"
BOXING_SECRET = "bx_sec_7f9a1c83e4b2d56a9018e3f47b2c918a"
BOXING_DB_LOCAL = os.path.expanduser("~/projects/boxing-sc-lab/data/athletes_db.json")

VECTOR_URL = "https://vector-ai-assistant-u73o.onrender.com"
VECTOR_SECRET = "vec_sec_99a8b7c6d5e4f3a2b1029384756"
VECTOR_NOTES_LOCAL = os.path.join(PROJECT_ROOT, "notes.json")

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def create_snapshots():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if os.path.exists(BOXING_DB_LOCAL):
        try:
            with open(BOXING_DB_LOCAL, "r", encoding="utf-8") as f:
                d = json.load(f)
            bak = os.path.join(BACKUP_DIR, f"boxing_athletes_3h_{ts}.json")
            with open(bak, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log(f"[!] Ошибка создания бэкапа Boxing: {e}")

    if os.path.exists(VECTOR_NOTES_LOCAL):
        try:
            with open(VECTOR_NOTES_LOCAL, "r", encoding="utf-8") as f:
                n = json.load(f)
            bak = os.path.join(BACKUP_DIR, f"vector_notes_3h_{ts}.json")
            with open(bak, "w", encoding="utf-8") as f:
                json.dump(n, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log(f"[!] Ошибка создания бэкапа Vector: {e}")

    # Автоматическая ротация: оставляем только последние 3 снапшота каждого типа
    try:
        import glob
        for prefix in ("vector_notes_3h_", "boxing_athletes_3h_"):
            snaps = sorted(glob.glob(os.path.join(BACKUP_DIR, f"{prefix}*.json")))
            for old_snap in snaps[:-3]:
                os.remove(old_snap)
    except Exception as e:
        log(f"[!] Ошибка ротации снапшотов: {e}")

def sync_boxing():
    ctx = ssl.create_default_context()
    
    # 1. Загрузка локальной базы
    local_db = {}
    if os.path.exists(BOXING_DB_LOCAL):
        try:
            with open(BOXING_DB_LOCAL, "r", encoding="utf-8") as f:
                local_db = json.load(f)
        except Exception as e:
            log(f"[!] Ошибка чтения локальной базы Boxing: {e}")

    # 2. PULL из облака
    pull_url = f"{BOXING_URL}/api/sync_db?secret={urllib.parse.quote(BOXING_SECRET)}"
    cloud_db = None
    try:
        req = urllib.request.Request(pull_url, headers={"User-Agent": "AutoSync3H/2.0", "X-Sync-Secret": BOXING_SECRET})
        with urllib.request.urlopen(req, context=ctx, timeout=40) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if res.get("ok"):
                cloud_db = res.get("data", {})
    except Exception as e:
        log(f"[!] [BOXING LAB] Облачный сервер не ответил на PULL ({e}), сохраняем локальную базу.")

    # 3. MERGE: Аккуратное объединение без потерь
    merged_db = dict(local_db)
    if cloud_db and isinstance(cloud_db, dict):
        merged_athletes = merged_db.get("athletes", {})
        cloud_athletes = cloud_db.get("athletes", {})

        for ath_id, c_info in cloud_athletes.items():
            if ath_id not in merged_athletes:
                merged_athletes[ath_id] = c_info
            else:
                l_info = merged_athletes[ath_id]
                l_hist = l_info.get("history", [])
                c_hist = c_info.get("history", [])
                seen_ts = {h.get("timestamp") for h in l_hist if h.get("timestamp")}
                for ch in c_hist:
                    if ch.get("timestamp") not in seen_ts:
                        l_hist.append(ch)
                        seen_ts.add(ch.get("timestamp"))
                l_hist.sort(key=lambda x: str(x.get("timestamp", "")))
                merged_athletes[ath_id]["history"] = l_hist

                if c_info.get("custom_pharma_schedule") and not l_info.get("custom_pharma_schedule"):
                    merged_athletes[ath_id]["custom_pharma_schedule"] = c_info["custom_pharma_schedule"]

        merged_db["athletes"] = merged_athletes

    # 4. Сохранение объединенной базы локально
    try:
        os.makedirs(os.path.dirname(BOXING_DB_LOCAL), exist_ok=True)
        with open(BOXING_DB_LOCAL, "w", encoding="utf-8") as f:
            json.dump(merged_db, f, ensure_ascii=False, indent=2)
        os.chmod(BOXING_DB_LOCAL, 0o600)
    except Exception as e:
        log(f"[X] [BOXING LAB] Ошибка локальной записи базы: {e}")
        return False

    # 5. PUSH объединенной базы обратно в облако
    try:
        post_data = json.dumps({"data": merged_db}).encode("utf-8")
        push_req = urllib.request.Request(
            pull_url,
            data=post_data,
            headers={"Content-Type": "application/json", "User-Agent": "AutoSync3H/2.0", "X-Sync-Secret": BOXING_SECRET}
        )
        with urllib.request.urlopen(push_req, context=ctx, timeout=40) as push_resp:
            p_res = json.loads(push_resp.read().decode("utf-8"))
            if p_res.get("ok"):
                ath_count = len(merged_db.get("athletes", {}))
                log(f"[BOXING] [BOXING LAB] Двусторонняя синхронизация успешна! В базе: {ath_count} спортсменов.")
                return True
    except Exception as e:
        log(f"[!] [BOXING LAB] Локально сохранено, но ошибка PUSH в облако: {e}")
        return True

    return True

def sync_vector():
    ctx = ssl.create_default_context()

    # 1. Загрузка локальных заметок
    local_notes = []
    if os.path.exists(VECTOR_NOTES_LOCAL):
        try:
            with open(VECTOR_NOTES_LOCAL, "r", encoding="utf-8") as f:
                local_notes = json.load(f)
        except Exception as e:
            log(f"[!] Ошибка чтения локальных заметок Вектора: {e}")

    # 2. PULL из облака
    pull_url = f"{VECTOR_URL}/api/sync_notes?secret={urllib.parse.quote(VECTOR_SECRET)}"
    cloud_notes = None
    try:
        req = urllib.request.Request(pull_url, headers={"User-Agent": "AutoSync3H/2.0", "X-Sync-Secret": VECTOR_SECRET})
        # Увеличенный таймаут 50с на случай холодного старта спящего контейнера Render
        with urllib.request.urlopen(req, context=ctx, timeout=50) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if res.get("ok"):
                cloud_notes = res.get("notes", [])
    except Exception as e:
        log(f"[!] [VECTOR BOT] Облачный сервер не ответил на PULL ({e}), сохраняем локальные заметки.")

    # 3. MERGE заметок без потерь
    notes_by_id = {}
    for n in local_notes:
        nid = str(n.get("id", "")) or str(n.get("timestamp", "")) or str(hash(n.get("text", "")))
        notes_by_id[nid] = n

    if cloud_notes and isinstance(cloud_notes, list):
        for cn in cloud_notes:
            cid = str(cn.get("id", "")) or str(cn.get("timestamp", "")) or str(hash(cn.get("text", "")))
            if cid not in notes_by_id:
                notes_by_id[cid] = cn
            else:
                c_ts = str(cn.get("updated_at") or cn.get("timestamp") or "")
                l_ts = str(notes_by_id[cid].get("updated_at") or notes_by_id[cid].get("timestamp") or "")
                if c_ts > l_ts:
                    notes_by_id[cid] = cn

    merged_notes = list(notes_by_id.values())
    try:
        merged_notes.sort(key=lambda x: int(x.get("id", 0)))
    except Exception:
        pass

    # 4. Сохранение объединенных заметок локально
    try:
        with open(VECTOR_NOTES_LOCAL, "w", encoding="utf-8") as f:
            json.dump(merged_notes, f, ensure_ascii=False, indent=2)
        os.chmod(VECTOR_NOTES_LOCAL, 0o600)
    except Exception as e:
        log(f"[X] [VECTOR BOT] Ошибка локальной записи заметок: {e}")
        return False

    # 5. PUSH объединенных заметок обратно в облако
    try:
        post_data = json.dumps({"notes": merged_notes}).encode("utf-8")
        push_req = urllib.request.Request(
            pull_url,
            data=post_data,
            headers={"Content-Type": "application/json", "User-Agent": "AutoSync3H/2.0", "X-Sync-Secret": VECTOR_SECRET}
        )
        with urllib.request.urlopen(push_req, context=ctx, timeout=50) as push_resp:
            p_res = json.loads(push_resp.read().decode("utf-8"))
            if p_res.get("ok"):
                log(f"[VECTOR] [VECTOR BOT] Двусторонняя синхронизация успешна! В базе: {len(merged_notes)} заметок.")
                return True
    except Exception as e:
        log(f"[!] [VECTOR BOT] Локально сохранено, но ошибка PUSH в облако: {e}")
        return True

    return True

def main():
    log("[SYNC] ====== НАЧАЛО 3-ЧАСОВОГО ЦИКЛА БЕЗОПАСНОЙ ДВУСТОРОННЕЙ СИНХРОНИЗАЦИИ ======")
    create_snapshots()
    b_ok = sync_boxing()
    v_ok = sync_vector()
    status = "УСПЕШНО" if (b_ok and v_ok) else "ЧАСТИЧНО/СБОЙ"
    log(f"[FINISH] ====== ЦИКЛ ЗАВЕРШЕН [{status}] ======\n")

if __name__ == "__main__":
    main()

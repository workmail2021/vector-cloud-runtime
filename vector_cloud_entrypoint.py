#!/usr/bin/env python3
"""
ИИ-ВЕКТОР 2026 // 24/7 CLOUD AUTONOMOUS CONTAINER ENTRYPOINT (TIER-1 SECURITY HARDENED)
Запускает защищенный HTTP/REST шлюз и демона Vector Telegram Bot (@vsr_guard_bot) в одном контейнере.
Оснащен:
- In-Memory Sliding Window Rate Limiter (Anti-DDoS / Anti-Flood)
- DoS & Memory Guard (лимит размера тела 1 МБ)
- Timing-Attack Safe Secret Verification (hmac.compare_digest)
- Strict Security Headers (nosniff, XSS-block, CSP)
"""

import os
import sys
import time
import json
import hmac
import threading
import urllib.parse
from collections import defaultdict
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

PORT = int(os.environ.get("PORT", 8088))
SYNC_SECRET = os.environ.get("VECTOR_SYNC_SECRET", "vec_sec_99a8b7c6d5e4f3a2b1029384756")
MAX_PAYLOAD_SIZE = 1024 * 1024  # 1 МБ

REDIS_URL = os.environ.get("REDIS_URL")
REDIS_CLIENT = None
if REDIS_URL:
    try:
        import redis
        REDIS_CLIENT = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        print("🧠 [REDIS] Успешное подключение к облачному хранилищу данных!")
        # Авто-восстановление notes.json из Redis при холодном старте контейнера
        notes_f = os.path.join(BASE_DIR, "notes.json")
        if (not os.path.exists(notes_f) or os.path.getsize(notes_f) < 5):
            saved_notes = REDIS_CLIENT.get("vector:notes")
            if saved_notes:
                with open(notes_f, "w", encoding="utf-8") as nf:
                    nf.write(saved_notes)
                print(f"📦 [REDIS] Восстановлены заметки из Redis хранилища!")
    except Exception as re_err:
        print(f"⚠️ [REDIS ERROR] Не удалось подключиться к Redis: {re_err}")


class SlidingWindowRateLimiter:
    def __init__(self, window_seconds: int = 60, max_requests: int = 60):
        self.window = window_seconds
        self.max_requests = max_requests
        self.history = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, client_ip: str) -> tuple[bool, int]:
        now = time.time()
        with self.lock:
            valid_times = [t for t in self.history[client_ip] if now - t < self.window]
            self.history[client_ip] = valid_times
            if len(valid_times) >= self.max_requests:
                earliest = valid_times[0] if valid_times else now
                retry_after = max(1, int(self.window - (now - earliest)))
                return False, retry_after
            self.history[client_ip].append(now)
            return True, 0

general_limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=60)
sync_limiter = SlidingWindowRateLimiter(window_seconds=60, max_requests=20)

class VectorCloudHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def _get_client_ip(self) -> str:
        forwarded = self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = self.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        return self.client_address[0] if self.client_address else "127.0.0.1"

    def _check_rate_limit(self, is_sync: bool = False) -> bool:
        ip = self._get_client_ip()
        limiter = sync_limiter if is_sync else general_limiter
        allowed, retry_after = limiter.is_allowed(ip)
        if not allowed:
            self.send_response(429)
            self.send_header("Retry-After", str(retry_after))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._apply_security_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": False,
                "error": f"Rate limit exceeded. Retry after {retry_after}s."
            }, ensure_ascii=False).encode("utf-8"))
            return False
        return True

    def _apply_security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-XSS-Protection", "1; mode=block")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")

    def _send_json(self, data: dict, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self._apply_security_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Sync-Secret")
        self._apply_security_headers()
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._apply_security_headers()
        self.end_headers()

    def do_GET(self):
        if not self._check_rate_limit(is_sync=False):
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ["/", "/api/status", "/api/health"]:
            return self._send_json({
                "ok": True,
                "status": "healthy",
                "service": "Vector AI Assistant 2026 24/7",
                "bot": "@vsr_guard_bot",
                "owner": "Сергей Романов",
                "timestamp": int(time.time())
            })

        if path == "/api/sync_notes":
            if not self._check_rate_limit(is_sync=True):
                return
            req_sec = query.get("secret", [""])[0] or self.headers.get("X-Sync-Secret", "")
            if not hmac.compare_digest(str(req_sec).strip(), str(SYNC_SECRET).strip()):
                return self._send_json({"ok": False, "error": "Unauthorized"}, 401)
            
            notes_file = os.path.join(BASE_DIR, "notes.json")
            notes_data = []
            if os.path.exists(notes_file):
                try:
                    with open(notes_file, "r", encoding="utf-8") as f:
                        notes_data = json.load(f)
                except Exception:
                    pass
            return self._send_json({"ok": True, "notes_count": len(notes_data), "notes": notes_data})

        # Защита от утечки любых статических файлов (Zero-File-Leak)
        return self._send_json({"ok": False, "error": "Access Denied: Protected System Endpoint"}, 403)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if not self._check_rate_limit(is_sync=(path == "/api/sync_notes")):
            return

        # DoS & Payload Guard
        try:
            content_len = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            content_len = 0

        if content_len > MAX_PAYLOAD_SIZE:
            return self._send_json({"ok": False, "error": "Payload Too Large (Max 1MB allowed)"}, 413)

        if path == "/api/sync_notes":
            req_sec = query.get("secret", [""])[0] or self.headers.get("X-Sync-Secret", "")
            if not hmac.compare_digest(str(req_sec).strip(), str(SYNC_SECRET).strip()):
                return self._send_json({"ok": False, "error": "Unauthorized"}, 401)

            if content_len == 0:
                return self._send_json({"ok": False, "error": "Empty body"}, 400)

            try:
                body = self.rfile.read(content_len).decode("utf-8")
                incoming = json.loads(body)
                notes_data = incoming.get("notes", incoming) if isinstance(incoming, dict) else incoming
                notes_file = os.path.join(BASE_DIR, "notes.json")
                with open(notes_file, "w", encoding="utf-8") as f:
                    json.dump(notes_data, f, ensure_ascii=False, indent=2)
                if REDIS_CLIENT:
                    try:
                        REDIS_CLIENT.set("vector:notes", json.dumps(notes_data, ensure_ascii=False))
                    except Exception as re_e:
                        print(f"⚠️ [REDIS SAVE ERROR] {re_e}")
                return self._send_json({"ok": True, "status": "saved", "count": len(notes_data) if isinstance(notes_data, list) else 1})
            except Exception as e:
                return self._send_json({"ok": False, "error": str(e)}, 500)

        return self._send_json({"ok": False, "error": "Endpoint not found"}, 404)

def run_vector_polling():
    if os.environ.get("ENABLE_CLOUD_POLLING", "0") != "1":
        print("ℹ️ [VECTOR RUNNER] Облачный polling отключен (Бот обслуживается 24/7 основным сервером на ПК).")
        return
    time.sleep(3)
    print("🤖 [VECTOR RUNNER] Запуск Telegram-бота демона @vsr_guard_bot 24/7...")
    try:
        import vector_polling
        vector_polling.main_polling_loop()
    except Exception as e:
        print(f"⚠️ [VECTOR BOT ERROR] {e}")

def main():
    print("🎛⚡️ ========================================================")
    print(f"🎛⚡️ VECTOR BOT 2026 // 24/7 CLOUD AUTONOMOUS CONTAINER (PORT {PORT})")
    print("🎛⚡️ ========================================================")

    # 1. Запуск бота в фоновом потоке
    threading.Thread(target=run_vector_polling, daemon=True).start()

    # 2. Запуск защищенного HTTP сервера
    host = "0.0.0.0" if os.environ.get("RENDER") or os.environ.get("PORT") else "127.0.0.1"
    server_address = (host, PORT)
    httpd = ThreadingHTTPServer(server_address, VectorCloudHandler)
    print(f"🚀 [VECTOR SERVER] Защищенный HTTP/REST шлюз активен: http://{host}:{PORT}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("🛑 Остановка сервиса Вектор...")
        httpd.server_close()

if __name__ == "__main__":
    main()

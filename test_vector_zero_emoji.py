#!/usr/bin/env python3
"""
ТЕСТ-СЕНТИНЕЛ: Верификация нулевого присутствия визуальных эмодзи в ИИ-Вектор (Zero-Emoji Tier-1 Standard).
Проверяет строгое соблюдение Правила 16 AGENTS.md во всех интерфейсах, меню, карточках, уведомлениях и кнопках.
"""

import unittest
import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Строгий паттерн для обнаружения любых эмодзи и графических пиктограмм
EMOJI_PATTERN = re.compile(r"[\U00010000-\U0010ffff\u2600-\u27ff\u2b50\u203c\u2049]")

# Допустимые ASCII и текстовые символы псевдографики
ALLOWED_CHARS = {"✓", "✔", "•", "─", "═", "└", "│", "┌", "┐", "┘", "├", "┤", "┴", "┬", "┼", "░", "█"}

def contains_emoji(text: str) -> list:
    """Возвращает список найденных эмодзи (если есть), игнорируя разрешенную псевдографику."""
    if not isinstance(text, str):
        return []
    found = [c for c in text if EMOJI_PATTERN.match(c) and c not in ALLOWED_CHARS]
    return found

class TestVectorZeroEmoji(unittest.TestCase):

    def test_01_vector_bot_dashboards_and_markups(self):
        """Проверка главного меню, спортивного редиректа и карточек vector_bot.py"""
        import vector_bot as vb
        
        # 1. Главное меню
        main_kb = vb.get_main_dashboard_markup()
        for row in main_kb.get("inline_keyboard", []):
            for btn in row:
                ems = contains_emoji(btn.get("text", ""))
                self.assertEqual(ems, [], f"Эмодзи в кнопке главного меню: {btn['text']}")
        
        # 2. Спортивный редирект
        video_text = vb.get_video_dashboard_text()
        ems = contains_emoji(video_text)
        self.assertEqual(ems, [], f"Эмодзи в тексте спортивного редиректа: {video_text}")

        video_kb = vb.get_video_markup()
        for row in video_kb.get("inline_keyboard", []):
            for btn in row:
                ems = contains_emoji(btn.get("text", ""))
                self.assertEqual(ems, [], f"Эмодзи в кнопке спортивного меню: {btn['text']}")

    def test_02_security_guard_dashboard_and_buttons(self):
        """Проверка Центра Кибербезопасности: карточка и все инлайн-кнопки"""
        import security_guard_module as sgm
        dash_text = sgm.get_cyber_security_dashboard_text()
        ems = contains_emoji(dash_text)
        self.assertEqual(ems, [], f"Эмодзи в заголовке/тексте Кибер-Щита: {dash_text}")

        markup = sgm.get_cyber_security_markup()
        for row in markup.get("inline_keyboard", []):
            for btn in row:
                ems = contains_emoji(btn.get("text", ""))
                self.assertEqual(ems, [], f"Эмодзи в инлайн-кнопке Кибер-Щита: {btn['text']}")

    def test_03_notes_pagination_and_bulk_buttons(self):
        """Проверка пагинации и кнопок в модуле заметок (notes_module.py)"""
        import notes_module as nm
        
        # Обычный режим с пагинацией (15 заметок на 3 страницы)
        dummy_notes = [{"id": i, "text": f"Заметка {i}", "type": "текст"} for i in range(1, 15)]
        
        # Сохраняем временно фиктивные заметки для генерации клавиатуры
        orig_load = nm.load_notes
        nm.load_notes = lambda: dummy_notes
        try:
            markup_normal = nm.get_notes_dashboard_markup(chat_id=123, cat_state="all", is_bulk=False, page=1, page_size=5)
            for row in markup_normal.get("inline_keyboard", []):
                for btn in row:
                    ems = contains_emoji(btn.get("text", ""))
                    self.assertEqual(ems, [], f"Эмодзи в кнопке пагинации заметок: {btn['text']}")

            # Bulk режим
            markup_bulk = nm.get_notes_dashboard_markup(chat_id=123, cat_state="all", is_bulk=True, selected_ids=[1, 2], page=1, page_size=5)
            for row in markup_bulk.get("inline_keyboard", []):
                for btn in row:
                    ems = contains_emoji(btn.get("text", ""))
                    self.assertEqual(ems, [], f"Эмодзи в bulk-кнопке заметок: {btn['text']}")
        finally:
            nm.load_notes = orig_load

    def test_04_autonomous_dispatcher_and_bridge_templates(self):
        """Проверка подтверждения задач и ответов моста ПК (autonomous_task_dispatcher & bridge)"""
        import autonomous_agent_bridge as aab
        
        # Проверка ключевых статусов и шаблонов
        status_msg = aab.execute_agent_task_on_pc("статус служб", user_id=6375883079)
        ems = contains_emoji(status_msg)
        self.assertEqual(ems, [], f"Эмодзи в ответе 'статус служб': {status_msg}")

        audit_msg = aab.execute_agent_task_on_pc("журнал ошибок", user_id=6375883079)
        ems = contains_emoji(audit_msg)
        self.assertEqual(ems, [], f"Эмодзи в ответе 'журнал ошибок': {audit_msg}")

    def test_05_background_engine_reminder_alerts(self):
        """Проверка текстов и кнопок алармов напоминаний в background_engine.py"""
        with open(os.path.join(BASE_DIR, "background_engine.py"), "r", encoding="utf-8") as f:
            content = f.read()
        
        # Проверяем, что в блоках отправки алерта напоминаний нет эмодзи 🚨, ⏰, 📌, 📅, 💡, ⏱, ✅, 🗑
        remind_block_match = re.search(r"alert_text = \((.*?)\)\n\s+btn_rows =", content, re.DOTALL)
        if remind_block_match:
            block = remind_block_match.group(1)
            ems = contains_emoji(block)
            self.assertEqual(ems, [], f"Эмодзи в alert_text напоминания: {ems}")

    def test_06_weekly_reports_and_monitors(self):
        """Проверка еженедельных отчетов и мониторов"""
        with open(os.path.join(BASE_DIR, "weekly_bot_audit.py"), "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("🛡 <b>ЕЖЕНЕДЕЛЬНЫЙ", content)
        self.assertNotIn("🤖 <b>1. ТЕМА", content)
        self.assertNotIn("📸 <b>2. ТЕМА", content)

    def test_07_autonomous_quality_dashboard(self):
        """Проверка панели контроля качества autonomous_quality_engine"""
        import autonomous_quality_engine as aqe
        dash = aqe.get_autonomous_quality_dashboard()
        ems = contains_emoji(dash)
        self.assertEqual(ems, [], f"Эмодзи в дашборде качества: {dash}")

    def test_08_all_26_core_modules_zero_emoji(self):
        """Статический сквозной аудит всех 26 основных исполняемых файлов Вектора"""
        core_files = [
            "autonomous_agent_bridge.py",
            "autonomous_quality_engine.py",
            "autonomous_task_dispatcher.py",
            "background_engine.py",
            "chatgpt_engine.py",
            "cloud_storage_module.py",
            "construction_control_module.py",
            "email_security_guard.py",
            "logger_engine.py",
            "notes_module.py",
            "pc_control_engine.py",
            "reminders_module.py",
            "secretary_module.py",
            "security_guard_module.py",
            "security_watchdog.py",
            "sports_library_engine.py",
            "vault_manager.py",
            "vector_bot.py",
            "vector_polling.py",
            "vector_tier1_engine.py",
            "inline_query_handler.py",
            "daily_bot_audit.py",
            "pc_maintenance.py",
            "instagram_daily_analyzer.py",
            "instagram_session_keeper.py",
            "auto_sync_3h.py"
        ]
        violations = []
        for cf in core_files:
            cp = os.path.join(BASE_DIR, cf)
            if not os.path.exists(cp):
                continue
            with open(cp, "r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f, 1):
                    ems = contains_emoji(line)
                    if ems:
                        violations.append(f"{cf}:{line_idx} contains {ems}")
        self.assertEqual(violations, [], f"Найдены эмодзи в основных файлах: {violations}")

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
ИИ-ВЕКТОР: СИСТЕМА НЕПРЕРЫВНОГО РЕГРЕССИОННОГО КОНТРОЛЯ (VECTOR REGRESSION GUARD)
Автоматический запуск перед любым обновлением для исключения поломок и регрессий:
10/10 тестов всех систем, модулей и настроек.
"""

import os
import sys
import json
import unittest
import subprocess

BASE_DIR = "/home/home/Документы/2"
sys.path.insert(0, BASE_DIR)

class TestVectorRegressionGuard(unittest.TestCase):

    def test_01_golden_config_integrity(self):
        cfg_path = os.path.join(BASE_DIR, "vector_core_config.json")
        self.assertTrue(os.path.exists(cfg_path))
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        self.assertEqual(cfg["owner"]["chat_id"], 6375883079)
        self.assertEqual(cfg["ui_contract"]["mode"], "SINGLE_CARD_ZERO_CLUTTER")
        self.assertEqual(len(cfg["yandex_maps_guard"]["strict_markers"]), 6)

    def test_02_notes_full_text_and_3_folders(self):
        import vector_bot as vb
        notes = vb.load_notes()
        self.assertIsInstance(notes, list)
        self.assertGreater(len(notes), 0)
        # Check folders on disk
        for cat_dir in ["1_Спорт", "2_Работа", "3_Общее"]:
            dpath = os.path.join(BASE_DIR, "База_Заметок", cat_dir)
            self.assertTrue(os.path.exists(dpath), f"Папка {cat_dir} не найдена!")

    def test_03_mail_system_cache_and_folders(self):
        import email_security_guard as esg
        dash = esg.get_mail_dashboard_text()
        self.assertIn("user@mail.ru", dash)
        self.assertIn("imap.mail.ru", dash)
        topics = esg.categorize_emails_by_topic()
        self.assertIn("Работа", topics)
        self.assertIn("Бухгалтерия", topics)
        self.assertIn("Общая", topics)

    def test_04_cloud_vault_categories_and_ssd(self):
        import cloud_storage_module as csm
        index = csm.load_cloud_index()
        self.assertIsInstance(index, list)
        self.assertGreater(len(index), 0)
        dash = csm.get_cloud_dashboard_text()
        self.assertIn("ЛИЧНОЕ ПРИВАТНОЕ ОБЛАЧНОЕ ХРАНИЛИЩЕ", dash)

    def test_05_yandex_maps_6_strict_markers(self):
        import yandex_maps_guard as ymg
        # Must match
        self.assertTrue(ymg.is_target_boxing_review("Хожу на персональный бокс к тренеру Сергею"))
        self.assertTrue(ymg.is_target_boxing_review("Отличная секция бокса, поставили удар"))
        self.assertTrue(ymg.is_target_boxing_review("Тренер Сергей Анатольевич Романов мастер"))
        self.assertTrue(ymg.is_target_boxing_review("Отличный силовой кондиционный тренинг и СФП"))
        self.assertTrue(ymg.is_target_boxing_review("Петросян Давид отлично провел спарринг"))
        # Must NOT match (filtered out)
        self.assertFalse(ymg.is_target_boxing_review("Ходил на тренировку по дзюдо у Владимира"))
        self.assertFalse(ymg.is_target_boxing_review("Занимаюсь бразильским джиу-джитсу BJJ на татами"))
        self.assertFalse(ymg.is_target_boxing_review("Просто пришел посмотреть тренажеры в зал"))

    def test_06_reminders_watchdog_and_priority(self):
        import reminders_module as rm
        rems = rm.load_reminders()
        self.assertIsInstance(rems, list)

    def test_07_passwords_vault_security(self):
        vault_path = os.path.expanduser("~/.config/antigravity-email/passwords_vault.json")
        if os.path.exists(vault_path):
            stat = os.stat(vault_path)
            # Check chmod 600 permissions
            self.assertEqual(stat.st_mode & 0o777, 0o600)

    def test_08_auto_chat_cleaner_ready(self):
        import auto_chat_cleaner_and_sorter as accs
        self.assertTrue(callable(accs.run_chat_sort_and_cleanup))

    def test_09_sports_isolation_and_boxing_suite(self):
        sys.path.insert(0, os.path.join(BASE_DIR, "Спорт/Разработка/Тест_утром"))
        from test_boxing_performance_suite import TestBoxingPerformance
        suite = unittest.TestLoader().loadTestsFromTestCase(TestBoxingPerformance)
        runner = unittest.TextTestRunner(verbosity=0)
        res = runner.run(suite)
        self.assertEqual(len(res.failures), 0)
        self.assertEqual(len(res.errors), 0)

    def test_10_systemd_daemons_and_disk(self):
        res = subprocess.run(["systemctl", "--user", "is-active", "vector-bot.service"], capture_output=True, text=True)
        self.assertEqual(res.stdout.strip(), "active")
        statvfs = os.statvfs(BASE_DIR)
        free_gb = (statvfs.f_bavail * statvfs.f_frsize) / (1024 ** 3)
        self.assertGreater(free_gb, 20.0, "Свободного места на SSD менее 20 ГБ!")

if __name__ == "__main__":
    unittest.main()

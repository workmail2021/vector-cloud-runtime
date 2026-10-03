#!/usr/bin/env python3
"""
ИИ-Вектор: Модуль автоматического обслуживания ПК, Wi-Fi, VPN и АВТО-УВЕДОМЛЕНИЙ О ПЕРЕЗАГРУЗКЕ/ВЫКЛЮЧЕНИИ.
"""

import os
import sys
import shutil
import subprocess
import json
import urllib.request
import time

def check_reboot_recommendation():
    reasons = []
    # 1. Проверка флага необходимости перезагрузки после обновлений Linux
    if os.path.exists("/var/run/reboot-required"):
        reasons.append("Установлены важные обновления ядра Linux — требуется перезагрузка.")

    # 2. Проверка Uptime (время работы без перезагрузки)
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
            days = uptime_seconds / (24 * 3600)
            if days > 14:
                reasons.append(f"Компьютер работает без перезагрузки уже {int(days)} дней — рекомендуется перезагрузить для очистки кэша ядра.")
    except Exception:
        pass

    # 3. Проверка батареи
    bat_path = "/sys/class/power_supply/BAT0"
    if not os.path.exists(bat_path):
        bat_path = "/sys/class/power_supply/BAT1"
    
    if os.path.exists(bat_path):
        try:
            with open(os.path.join(bat_path, "capacity"), "r") as f:
                cap = int(f.read().strip())
            with open(os.path.join(bat_path, "status"), "r") as f:
                status = f.read().strip()
            
            if status.lower() == "discharging" and cap < 15:
                reasons.append(f"<b>Критически низкий заряд батареи ({cap}%)!</b> Подключите зарядное устройство или выключите ПК.")
        except Exception:
            pass

    return reasons

def get_system_health():
    total, used, free = shutil.disk_usage("/")
    total_gb = total / (1024 ** 3)
    used_gb = used / (1024 ** 3)
    free_gb = free / (1024 ** 3)
    used_percent = (used / total) * 100

    ram_total_mb = 0
    ram_used_percent = 0
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
            mem_dict = {}
            for line in lines:
                parts = line.split(":")
                if len(parts) == 2:
                    k = parts[0].strip()
                    v = parts[1].strip().split()[0]
                    mem_dict[k] = int(v)
            
            ram_total_mb = mem_dict.get("MemTotal", 0) // 1024
            ram_avail_mb = mem_dict.get("MemAvailable", 0) // 1024
            ram_used_percent = ((ram_total_mb - ram_avail_mb) / ram_total_mb) * 100 if ram_total_mb else 0
    except Exception:
        pass

    uptime_str = "неизвестно"
    try:
        res = subprocess.run(["uptime", "-p"], capture_output=True, text=True)
        uptime_str = res.stdout.strip()
    except Exception:
        pass

    wifi_ssid = "неизвестно"
    wifi_status = "отключен"
    local_ip = "127.0.0.1"
    try:
        res = subprocess.run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "dev"], capture_output=True, text=True)
        for line in res.stdout.splitlines():
            parts = line.split(":")
            if len(parts) >= 4 and parts[1] == "wifi" and parts[2] == "connected":
                wifi_status = "подключен"
                wifi_ssid = parts[3]
                break
        
        ip_res = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
        local_ip = ip_res.stdout.strip().split()[0] if ip_res.stdout.strip() else local_ip
    except Exception:
        pass

    vpn_status = "неактивен"
    vpn_name = "нет"
    public_ip = "неизвестно"
    country_location = "неизвестно"
    try:
        res = subprocess.run(["ip", "a"], capture_output=True, text=True)
        if "tun" in res.stdout or "wg" in res.stdout or "Meta" in res.stdout:
            vpn_status = "активен (зашифрован)"
            if "Meta" in res.stdout:
                vpn_name = "Meta (TUN)"
            elif "tun0" in res.stdout:
                vpn_name = "OpenVPN/TUN"
            elif "wg" in res.stdout:
                vpn_name = "WireGuard"
        
        # Надежное определение внешнего IP и страны через ipwho.is и ipify
        for api_url in ["https://ipwho.is/", "https://api.ipify.org?format=json"]:
            try:
                req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    public_ip = data.get("ip", public_ip)
                    city = data.get("city", "")
                    country = data.get("country", "")
                    if country or city:
                        country_location = f"{country} ({city})".strip() if city else country.strip()
                    if public_ip != "неизвестно":
                        break
            except Exception:
                continue
    except Exception:
        pass

    reboot_reasons = check_reboot_recommendation()

    return {
        "disk_total_gb": round(total_gb, 1),
        "disk_used_gb": round(used_gb, 1),
        "disk_free_gb": round(free_gb, 1),
        "disk_used_percent": round(used_percent, 1),
        "ram_total_mb": ram_total_mb,
        "ram_used_percent": round(ram_used_percent, 1),
        "uptime": uptime_str,
        "wifi_status": wifi_status,
        "wifi_ssid": wifi_ssid,
        "local_ip": local_ip,
        "vpn_status": vpn_status,
        "vpn_name": vpn_name,
        "public_ip": public_ip,
        "country_location": country_location,
        "reboot_reasons": reboot_reasons
    }

def clean_system_junk():
    cleaned_items = 0
    tmp_dir = "/tmp"
    if os.path.exists(tmp_dir):
        for f in os.listdir(tmp_dir):
            if f.startswith("tmp") or f.endswith(".tmp") or f.endswith(".log"):
                fp = os.path.join(tmp_dir, f)
                try:
                    if os.path.isfile(fp):
                        os.remove(fp)
                        cleaned_items += 1
                except Exception:
                    pass
    return cleaned_items

def format_pc_health_html():
    health = get_system_health()
    lines = ["<b>ОБСЛУЖИВАНИЕ ПК, WI-FI, VPN И СТАТУС ПИТАНИЯ:</b>\n"]
    lines.append(f"• Диск: <b>{health['disk_free_gb']} ГБ свободно</b> (Занято: {health['disk_used_percent']}%)")
    lines.append(f"• ОЗУ: <b>{health['ram_used_percent']}%</b> ({health['ram_total_mb']} МБ)")
    lines.append(f"• Время работы: <b>{health['uptime']}</b>")
    lines.append(f"• Wi-Fi Сеть: <b>{health['wifi_status']}</b> (Сеть: <code>{health['wifi_ssid']}</code>, IP: <code>{health['local_ip']}</code>)")
    lines.append(f"• VPN Шифрование: <b>{health['vpn_status']}</b> (Туннель: {health['vpn_name']})")
    lines.append(f"• Публичный IP: <code>{health['public_ip']}</code> — Локация: <b>{health['country_location']}</b>")
    
    if health['reboot_reasons']:
        lines.append("\n<b>РЕКОМЕНДАЦИЯ ПО ПЕРЕЗАГРУЗКЕ / ВЫКЛЮЧЕНИЮ:</b>")
        for r in health['reboot_reasons']:
            lines.append(f"  • {r}")
    else:
        lines.append("\n[✓] <b>Перезагрузка не требуется. ПК работает штатно!</b>")
        
    return "\n".join(lines)

# Стандартный псевдоним для совместимости
get_pc_health_data = get_system_health

if __name__ == "__main__":
    print(format_pc_health_html())

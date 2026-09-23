#!/usr/bin/env python3
import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import sys
import argparse

CONFIG_PATH = os.path.expanduser("~/.config/antigravity-email/config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения конфигурации: {e}")
        return None

def decode_mime_words(s):
    if not s:
        return ""
    decoded_fragments = decode_header(s)
    result = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            enc = encoding or 'utf-8'
            try:
                result.append(fragment.decode(enc, errors='ignore'))
            except Exception:
                result.append(fragment.decode('utf-8', errors='ignore'))
        else:
            result.append(str(fragment))
    return "".join(result)

def connect_imap(account):
    server = account.get("imap_server", "imap.mail.ru")
    port = account.get("imap_port", 993)
    user = account.get("email")
    password = account.get("app_password")

    try:
        mail = imaplib.IMAP4_SSL(server, port)
        mail.login(user, password)
        return mail
    except Exception as e:
        print(f"Ошибка подключения IMAP для {user}: {e}")
        return None

def categorize_email(subject, sender, body=""):
    text = f"{subject} {sender} {body}".lower()
    
    # 1. 🏗️ Подряд, Объектное строительство & ФКР
    if any(k in text for k in ['фкр', 'гнб', 'псд', 'терра-строй', 'мбу южное', 'набережная', 'котово', 'мир 149', 'лаврова', 'нефтяников', 'чапаева', 'школьная', 'штименко', 'водооткачка', 'дефектовка', 'проектирование', 'подряд']):
        return "1. 🏗️ Проекты, Строительство и ФКР"
    
    # 2. 🚚 Закупки Материалов и Снабжение
    elif any(k in text for k in ['эльф', 'труба', 'материалы', 'заказ покупателя', 'закупка', 'оборудование', 'поставка']):
        return "2. 🚚 Закупки и Снабжение (Трубы/Сантехника)"
    
    # 3. 📄 Бухгалтерия, Счета и Накладные
    elif any(k in text for k in ['удумян', 'осв', 'накладная', 'счет-фактура', 'счет №', 'аванс', 'парадигма', 'товарная накладная', 'оплата']):
        return "3. 📄 Бухгалтерия (Счета/Накладные/ОСВ)"
    
    # 4. ⚖️ Юридические вопросы, Договоры и Экспертиза
    elif any(k in text for k in ['иск', 'задолженность', 'договор подряда', 'теплоснабжения', 'акт сверки', 'экспертиза', 'юртаева']):
        return "4. ⚖️ Юрист, Договоры и Акты Сверки"
    
    # 5. 🏢 Управляющая Компания (УК Котово)
    elif any(k in text for k in ['uk-kotovo', 'управляющая компания']):
        return "5. 🏢 Управляющая Компания (УК Котово)"
    
    # 6. 🏦 Банк и Кадры (ПСБ, 2-НДФЛ)
    elif any(k in text for k in ['псб', 'psb', '2ндфл', '2-ндфл', 'работодатель', 'зарплата', 'работники']):
        return "6. 🏦 Банк и Кадровые документы"
    
    return "7. 📋 Прочие рабочие обращения"

def main():
    parser = argparse.ArgumentParser(description="Mail.ru AI Email Assistant Helper")
    parser.add_argument("--categorize-all", action="store_true", help="Categorize recent inbox emails")
    parser.add_argument("--account-name", type=str, default="work", help="Account key name")
    
    args = parser.parse_args()
    config = load_config() or {"accounts": {}}
    acc = config.get("accounts", {}).get(args.account_name)

    if not acc:
        print(f"Учетная запись '{args.account_name}' не найдена.")
        return

    mail = connect_imap(acc)
    if not mail:
        return
    
    mail.select("INBOX")
    status, messages = mail.search(None, 'ALL')
    msg_ids = messages[0].split()
    start_idx = max(1, len(msg_ids) - 49)
    fetch_ids = f"{start_idx}:{len(msg_ids)}"
    res, data = mail.fetch(fetch_ids, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')

    categories = {}
    for item in data:
        if isinstance(item, tuple):
            msg = email.message_from_bytes(item[1])
            subj = decode_mime_words(msg.get('Subject'))
            sender = decode_mime_words(msg.get('From'))
            cat = categorize_email(subj, sender)
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({"sender": sender, "subject": subj})

    mail.logout()
    print(json.dumps(categories, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

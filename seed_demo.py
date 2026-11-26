# -*- coding: utf-8 -*-
"""Demo kartlarini database.py semasina uygun sekilde ekler."""
import sqlite3, json
from datetime import datetime
from database import init_db, insert_card
from routes_generator import generate_routes

init_db()
now = datetime.now().isoformat()

demo = [
    ('DEMO-IBAN',    '04:AA:01:00:00:01', 'Çoklu IBAN Kartı', 'G-DEMO',
     {'title': 'Banka Hesaplarım', 'accounts': [
        {'bank_name': 'Akbank',       'bank_color': '#E30613', 'account_title': 'Maaş',    'recipient': 'İsmail Yılmaz', 'iban': 'TR12 0004 6000 1234 5678 9012 34'},
        {'bank_name': 'Garanti BBVA', 'bank_color': '#009B4E', 'account_title': 'Ticari',  'recipient': 'İsmail Yılmaz', 'iban': 'TR34 0006 2000 5678 9012 3456 78'},
        {'bank_name': 'Enpara',       'bank_color': '#00A0E3', 'account_title': 'Birikim', 'recipient': 'İsmail Yılmaz', 'iban': 'TR90 0011 1000 0000 0123 4567 89'},
     ]}, 0),
    ('DEMO-MENU',    '04:AA:01:00:00:02', 'Dijital Menü',     'G-DEMO',
     {'title': 'Kahve Dükkanı Menü', 'url': 'https://example.com/menu'}, 0),
    ('DEMO-GOOGLE',  '04:AA:01:00:00:03', 'Google Yorum',     'G-DEMO',
     {'title': 'Kahve Dükkanı', 'url': 'https://g.page/r/example/review'}, 0),
    ('DEMO-INSTA',   '04:AA:01:00:00:04', 'Instagram',        'G-DEMO',
     {'username': 'kahvedukkani', 'url': 'https://instagram.com/kahvedukkani'}, 0),
    ('DEMO-WA',      '04:AA:01:00:00:05', 'WhatsApp',         'G-DEMO',
     {'title': 'Sipariş Hattı', 'phone': '905551234567', 'url': 'https://wa.me/905551234567'}, 0),
    ('DEMO-SAHIB',   '04:AA:01:00:00:06', 'Sahibinden Mağaza','G-DEMO',
     {'title': 'Mağaza', 'url': 'https://sahibinden.com/example'}, 0),
]

conn = sqlite3.connect('data/nfc_system.db')
for card_id, uid, ct, gid, data, locked in demo:
    try:
        insert_card(card_id, uid, ct, gid, data, locked)
        print('Eklendi:', card_id, '-', ct)
    except sqlite3.IntegrityError:
        print('Zaten var:', card_id)
conn.close()

path = generate_routes('routes.json')
print('routes.json yazildi:', path)

# -*- coding: utf-8 -*-
import sqlite3, json
from datetime import datetime
from database import init_db
from routes_generator import generate_routes

init_db()
now = datetime.now().isoformat()

demo = [
    ('DEMO-IBAN',    '04:AA:01:00:00:01', 'Çoklu IBAN Kartı', 'G-DEMO',
     {'title': 'Banka Hesaplarım', 'owner': 'İsmail Hazar', 'accounts': [
        {'bank_name': 'Akbank',       'bank_color': '#E30613', 'account_title': 'Maaş',    'recipient': 'İsmail Hazar', 'iban': 'TR12 0004 6000 1234 5678 9012 34'},
        {'bank_name': 'Garanti BBVA', 'bank_color': '#009B4E', 'account_title': 'Ticari',  'recipient': 'İsmail Hazar', 'iban': 'TR34 0006 2000 5678 9012 3456 78'},
        {'bank_name': 'Ziraat Bankası','bank_color': '#E30613','account_title': 'Kredi',   'recipient': 'İsmail Hazar', 'iban': 'TR12 0001 0000 1234 5678 9012 34'},
        {'bank_name': 'Enpara',       'bank_color': '#00A0E3', 'account_title': 'Birikim', 'recipient': 'İsmail Hazar', 'iban': 'TR90 0011 1000 0000 0123 4567 89'},
        {'bank_name': 'İş Bankası',   'bank_color': '#004B93', 'account_title': 'Fatura',  'recipient': 'İsmail Hazar', 'iban': 'TR12 0006 4000 1234 5678 9012 34'},
        {'bank_name': 'Kuveyt Türk',  'bank_color': '#00A651', 'account_title': 'Altın',   'recipient': 'İsmail Hazar', 'iban': 'TR12 0020 5000 1234 5678 9012 34'},
     ]}, 0),
    ('DEMO-MENU',    '04:AA:01:00:00:02', 'Dijital Menü',     'G-DEMO',
     {'title': 'Kahve Dükkanı Menü', 'url': 'https://example.com/menu'}, 0),
    ('DEMO-GOOGLE',  '04:AA:01:00:00:03', 'Google Yorum',     'G-DEMO',
     {'title': 'Kahve Dükkanı', 'url': 'https://g.page/r/SENIN_GERCEK_GOOGLE_LINKIN/review'}, 0),
    ('DEMO-INSTA',   '04:AA:01:00:00:04', 'Instagram',        'G-DEMO',
     {'username': 'kahvedukkani', 'url': 'https://instagram.com/kahvedukkani'}, 0),
    ('DEMO-WA',      '04:AA:01:00:00:05', 'WhatsApp',         'G-DEMO',
     {'title': 'Sipariş Hattı', 'phone': '905551234567', 'url': 'https://wa.me/905551234567'}, 0),
]

# Tek bir güvenli bağlantı açıyoruz ve hata olsa bile kapanmasını (with) sağlıyoruz
with sqlite3.connect('data/nfc_system.db') as conn:
    cur = conn.cursor()
    for card_id, uid, ct, gid, data, locked in demo:
        # INSERT OR REPLACE: Varsa silip yeniden yazar (günceller), yoksa ekler
        cur.execute('''
            INSERT OR REPLACE INTO cards (card_id, uid, card_type, group_id, data, locked, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (card_id, uid, ct, gid, json.dumps(data, ensure_ascii=False), locked, now))
        print('Hazir:', card_id, '-', ct)

# routes.json dosyasını güncelle
path = generate_routes('routes.json')
print('routes.json basariyla yazildi:', path)

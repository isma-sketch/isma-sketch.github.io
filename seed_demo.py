import sqlite3, json
from database import init_db
from routes_generator import generate_routes
init_db()
with sqlite3.connect('data/nfc_system.db') as c:
    c.execute('DELETE FROM cards')
    c.execute('INSERT INTO cards (card_id, uid, card_type, group_id, data, locked, created_at) VALUES (?,?,?,?,?,?,?)',
              ('DEMO-IBAN', '04AABBCC', 'Çoklu IBAN Kartı', 'G1', json.dumps({'title':'Hesaplar','owner':'İsmail','accounts':[{'bank_name':'Akbank','bank_color':'#E30613','recipient':'İsmail','iban':'TR12 0000'}]}), 0, '2026-01-01'))
    c.execute('INSERT INTO cards (card_id, uid, card_type, group_id, data, locked, created_at) VALUES (?,?,?,?,?,?,?)',
              ('DEMO-MENU', '04DDEEFF', 'Dijital Menü', 'G1', json.dumps({'title':'Menü','url':'https://example.com'}), 0, '2026-01-01'))
generate_routes('routes.json')
print('Test verileri eklendi.')

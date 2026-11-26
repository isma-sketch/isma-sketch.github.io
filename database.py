import sqlite3, os, json
from datetime import datetime

DB_DIR = 'data'
DB_PATH = os.path.join(DB_DIR, 'nfc_system.db')

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS cards (id INTEGER PRIMARY KEY AUTOINCREMENT, card_id TEXT UNIQUE NOT NULL, uid TEXT, card_type TEXT NOT NULL, group_id TEXT, data TEXT NOT NULL, locked INTEGER DEFAULT 0, created_at TEXT NOT NULL)')
        cur.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')

def get_setting(key, default=None):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT value FROM settings WHERE key=?', (key,))
        row = cur.fetchone()
        return row[0] if row else default

def set_setting(key, value):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))

def find_by_uid(uid):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT card_id, uid, card_type, group_id, data FROM cards WHERE uid=?', (uid,))
        return cur.fetchone()

def insert_card(card_id, uid, card_type, group_id, data, locked):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO cards (card_id, uid, card_type, group_id, data, locked, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                    (card_id, uid, card_type, group_id, json.dumps(data, ensure_ascii=False), 1 if locked else 0, datetime.now().isoformat()))

def get_next_card_id(group_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM cards WHERE group_id=?', (group_id,))
        count = cur.fetchone()[0]
        return group_id + '-' + str(count + 1).zfill(3)

def get_all_cards():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('SELECT card_id, card_type, group_id, data, locked, created_at, uid FROM cards ORDER BY created_at DESC')
        return cur.fetchall()

def update_card_data(card_id, new_data):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('UPDATE cards SET data=? WHERE card_id=?', (json.dumps(new_data, ensure_ascii=False), card_id))

def update_group_data(group_id, new_data):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('UPDATE cards SET data=? WHERE group_id=?', (json.dumps(new_data, ensure_ascii=False), group_id))
        return cur.rowcount

def delete_card(card_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM cards WHERE card_id=?', (card_id,))

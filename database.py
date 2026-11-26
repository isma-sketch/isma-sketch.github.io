import sqlite3, os, json
from datetime import datetime

DB_DIR = 'data'
DB_PATH = os.path.join(DB_DIR, 'nfc_system.db')

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS cards (id INTEGER PRIMARY KEY AUTOINCREMENT, card_id TEXT UNIQUE NOT NULL, uid TEXT, card_type TEXT NOT NULL, group_id TEXT, data TEXT NOT NULL, locked INTEGER DEFAULT 0, created_at TEXT NOT NULL)')
    cur.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT value FROM settings WHERE key=?', (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def find_by_uid(uid):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT card_id, uid, card_type, group_id, data FROM cards WHERE uid=?', (uid,))
    row = cur.fetchone()
    conn.close()
    return row

def insert_card(card_id, uid, card_type, group_id, data, locked):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO cards (card_id, uid, card_type, group_id, data, locked, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)', (card_id, uid, card_type, group_id, json.dumps(data, ensure_ascii=False), 1 if locked else 0, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_next_card_id(group_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM cards WHERE group_id=?', (group_id,))
    count = cur.fetchone()[0]
    conn.close()
    return group_id + '-' + str(count + 1).zfill(3)

def get_all_cards():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT card_id, card_type, group_id, data, locked, created_at FROM cards')
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_card(card_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('DELETE FROM cards WHERE card_id=?', (card_id,))
    conn.commit()
    conn.close()

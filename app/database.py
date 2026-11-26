# -*- coding: utf-8 -*-
"""Veritabanı işlemleri: SQLite okuma/yazma ve routes.json güncelleme"""
import sqlite3
import json
import os
from app.config import DB_YOLU, ROTA_YOLU, GATE_URL


def baglan():
    conn = sqlite3.connect(DB_YOLU)
    conn.row_factory = sqlite3.Row
    return conn


def tablolari_olustur():
    """Veritabanı yoksa tabloları oluştur."""
    conn = baglan()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS cards (
        id TEXT PRIMARY KEY,
        uid TEXT UNIQUE,
        group_id TEXT,
        type TEXT NOT NULL,
        title TEXT,
        customer_name TEXT,
        target TEXT,
        created_date TEXT DEFAULT (date('now'))
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ibans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_id TEXT NOT NULL,
        bank TEXT,
        label TEXT,
        account_name TEXT,
        iban TEXT,
        FOREIGN KEY (card_id) REFERENCES cards(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS groups (
        id TEXT PRIMARY KEY,
        name TEXT,
        card_ids TEXT DEFAULT '[]'
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS banks (
        name TEXT PRIMARY KEY,
        color TEXT,
        short TEXT
    )""")
    conn.commit()
    conn.close()


def uid_var_mi(uid):
    """UID daha önce kayıtlı mı?"""
    conn = baglan()
    c = conn.cursor()
    c.execute("SELECT id, customer_name FROM cards WHERE uid = ?", (uid,))
    satir = c.fetchone()
    conn.close()
    return satir


def kart_sayisi():
    conn = baglan()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM cards")
    sayi = c.fetchone()[0]
    conn.close()
    return sayi


def yeni_kart_id():
    """Otomatik artan kart kimliği üret: kart-0001, kart-0002 ..."""
    conn = baglan()
    c = conn.cursor()
    c.execute("SELECT id FROM cards WHERE id LIKE 'kart-%'")
    satirlar = c.fetchall()
    conn.close()
    en_buyuk = 0
    for s in satirlar:
        try:
            sayi = int(s[0].split("-")[1])
            if sayi > en_buyuk:
                en_buyuk = sayi
        except (IndexError, ValueError):
            pass
    return f"kart-{en_buyuk + 1:04d}"


def grup_kart_sayisi(group_id):
    """Bir gruba bağlı kayıtlı kart sayısı (X / Toplam sayacı için)."""
    conn = baglan()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM cards WHERE group_id = ?", (group_id,))
    sayi = c.fetchone()[0]
    conn.close()
    return sayi


def kart_kaydet(kart_id, uid, group_id, tur, baslik, musteri_adi, hedef, ibanlar):
    """Kartı SQLite'a kaydeder."""
    conn = baglan()
    c = conn.cursor()
    c.execute("""INSERT INTO cards (id, uid, group_id, type, title, customer_name, target)
                 VALUES (?, ?, ?, ?, ?, ?, ?)
                 ON CONFLICT(id) DO UPDATE SET
                 uid=excluded.uid, group_id=excluded.group_id, type=excluded.type,
                 title=excluded.title, customer_name=excluded.customer_name, target=excluded.target""",
              (kart_id, uid, group_id, tur, baslik, musteri_adi, hedef))
    # IBANları yenile
    c.execute("DELETE FROM ibans WHERE card_id = ?", (kart_id,))
    for ib in ibanlar:
        c.execute("INSERT INTO ibans (card_id, bank, label, account_name, iban) VALUES (?, ?, ?, ?, ?)",
                  (kart_id, ib["bank"], ib.get("label", ""), ib["account_name"], ib["iban"]))
    # Grup kaydı
    if group_id:
        c.execute("SELECT card_ids FROM groups WHERE id = ?", (group_id,))
        satir = c.fetchone()
        if satir:
            ids = json.loads(satir[0] or "[]")
            if kart_id not in ids:
                ids.append(kart_id)
            c.execute("UPDATE groups SET card_ids = ? WHERE id = ?",
                      (json.dumps(ids, ensure_ascii=False), group_id))
        else:
            c.execute("INSERT INTO groups (id, name, card_ids) VALUES (?, ?, ?)",
                      (group_id, group_id, json.dumps([kart_id], ensure_ascii=False)))
    conn.commit()
    conn.close()


def routes_guncelle():
    """SQLite'taki tüm veriyi okuyup routes.json dosyasını yeniden yazar.
    Tek kayıt veya grup değiştiğinde bu fonksiyon çağrılır."""
    conn = baglan()
    c = conn.cursor()
    rotalar = {
        "version": "1.0",
        "updated": __import__("datetime").date.today().isoformat(),
        "gate_url": GATE_URL,
        "cards": {},
        "groups": {},
        "banks": {}
    }
    c.execute("SELECT * FROM banks")
    for satir in c.fetchall():
        rotalar["banks"][satir["name"]] = {"color": satir["color"], "short": satir["short"]}
    c.execute("SELECT * FROM cards")
    kartlar = c.fetchall()
    for kart in kartlar:
        kart_dict = {
            "id": kart["id"],
            "group_id": kart["group_id"],
            "type": kart["type"],
            "title": kart["title"],
            "customer_name": kart["customer_name"],
            "target": kart["target"]
        }
        if kart["type"] == "multi-iban":
            c.execute("SELECT * FROM ibans WHERE card_id = ?", (kart["id"],))
            kart_dict["ibans"] = [
                {"bank": i["bank"], "label": i["label"],
                 "account_name": i["account_name"], "iban": i["iban"]}
                for i in c.fetchall()
            ]
        rotalar["cards"][kart["id"]] = kart_dict
    c.execute("SELECT * FROM groups")
    for g in c.fetchall():
        rotalar["groups"][g["id"]] = {
            "name": g["name"],
            "cards": json.loads(g["card_ids"] or "[]")
        }
    conn.close()
    with open(ROTA_YOLU, "w", encoding="utf-8") as f:
        json.dump(rotalar, f, ensure_ascii=False, indent=2)
    return len(rotalar["cards"])
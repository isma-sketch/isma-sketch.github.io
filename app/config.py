# -*- coding: utf-8 -*-
"""Ayarlar ve sabitler"""
import os

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_YOLU = os.path.join(KOK, "data", "nfc_system.db")
ROTA_YOLU = os.path.join(KOK, "data", "routes.json")

# Sabit kapı adresi (kartlara bu yazılır)
GATE_URL = "https://isma-sketch.github.io/g/?id="

BANKALAR = [
    "Akbank", "Garanti BBVA", "Ziraat Bankası", "İş Bankası",
    "Yapı Kredi", "QNB", "VakıfBank", "Halkbank", "Enpara",
    "Kuveyt Türk", "Diğer"
]

BANKA_RENKLERI = {
    "Akbank": "#E30A17", "Garanti BBVA": "#00A758", "Ziraat Bankası": "#004A9C",
    "İş Bankası": "#0072C6", "Yapı Kredi": "#FF6B35", "QNB": "#00A8E1",
    "VakıfBank": "#FFB200", "Halkbank": "#0068A8", "Enpara": "#6C5CFF",
    "Kuveyt Türk": "#00693E", "Diğer": "#6B7280"
}

CIP_TIPLERI = [
    "Otomatik Algıla (Önerilen)",
    "NTAG213 (144 Bayt)",
    "NTAG215 (504 Bayt)",
    "NTAG216 (888 Bayt)",
    "NTAG210 / NTAG212",
    "MIFARE Ultralight / Ultralight C / EV1",
    "MIFARE Classic 1K / 4K (Telefon uyumluluk notu: Bazı telefonlar yazamaz)"
]

KART_TURLERI = [
    "Çoklu IBAN Kartı",
    "Dijital Menü",
    "Google Yorum",
    "Instagram",
    "WhatsApp",
    "Sahibinden Mağaza",
    "Özel Bağlantı"
]

# Kart türü -> routes.json type eşlemesi
TUR_ESLEME = {
    "Çoklu IBAN Kartı": "multi-iban",
    "Dijital Menü": "digital-menu",
    "Google Yorum": "google-review",
    "Instagram": "instagram",
    "WhatsApp": "whatsapp",
    "Sahibinden Mağaza": "sahibinden",
    "Özel Bağlantı": "custom-link"
}
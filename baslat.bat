@echo off
chcp 65001 > nul
title NFC Kart Sabit Kapi - Yonetim
echo NFC Kart Sabit Kapi ve Yonlendirme Yonetim Sistemi baslatiliyor...
echo.
python --version > nul 2>&1
if errorlevel 1 (
  echo HATA: Python bulunamadi. Lutfen Python 3.10+ kurun.
  pause
  exit /b 1
)
python app.py
if errorlevel 1 (
  echo.
  echo HATA: Uygulama coktu. Yukaridaki hata mesajini kontrol edin.
)
pause

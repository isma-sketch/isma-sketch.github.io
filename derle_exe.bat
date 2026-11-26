@echo off
chcp 65001 > nul
title NFC Kart Sabit Kapi - EXE Derleme
echo Bagimliliklar kuruluyor...
pip install -r requirements.txt
echo.
echo PyInstaller ile EXE derleniyor...
pyinstaller --onefile --windowed --name NFCYonetim app.py
echo.
echo Derleme tamamlandi. Cikti: dist\NFCYonetim.exe
echo NOT: routes.json, g klasoru ve onizleme.html dosyalarini exe ile ayni klasore kopyalayin.
pause

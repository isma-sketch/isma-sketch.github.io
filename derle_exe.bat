@echo off
chcp 65001 > nul
title NFC Kart Sabit Kapi - EXE Derleme
echo Bagimliliklar kontrol ediliyor...
pip install -r requirements.txt
echo.
echo PyInstaller ile derleme basliyor (Musteri paneli ve HTML dosyalari dahil)...
pyinstaller --noconfirm --onefile --windowed --name NFCYonetim ^
    --add-data "musteri.html;." ^
    --add-data "onizleme.html;." ^
    --add-data "routes.json;." ^
    --add-data "g;g" ^
    app.py
echo.
echo Derleme tamamlandi! Cikti: dist\NFCYonetim.exe
echo NOT: Olusan exe'yi data ve g klasorleriyle ayni dizinde calistirabilirsiniz.
pause

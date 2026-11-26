@echo off
chcp 65001 >nul
pip install -r requirements.txt
pyinstaller --onefile --windowed --name NFCYonetim --add-data "data;data" --add-data "routes.json;." --add-data "g;g" --add-data "musteri.html;." --add-data "onizleme.html;." app.py
pause
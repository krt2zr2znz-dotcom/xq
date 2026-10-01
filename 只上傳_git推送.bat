@echo off
chcp 950 >nul
title 只上傳網頁
cd /d "%~dp0"
echo 上傳到 GitHub...
python "%~dp0..\..\07_自動化腳本\網站推送.py" "manual upload" auto
if errorlevel 1 (echo. & echo X 推送失敗,原因看上面 [推送] 那幾行,也記在 _publish_log.txt) else (echo. & echo V 完成,開網頁按 Ctrl+F5)
pause

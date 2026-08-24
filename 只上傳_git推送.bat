@echo off
chcp 950 >nul
title 只上傳網頁
cd /d "%~dp0"
del /f /s /q ".git\*.lock" >nul 2>&1
echo 上傳到 GitHub...
git add -A
git commit -m "manual upload"
git push -f -u origin main
if errorlevel 1 (echo. ^& echo X 失敗! 若跳GitHub授權就授權後再跑一次) else (echo. ^& echo V 成功! 開網頁按 Ctrl+F5)
pause

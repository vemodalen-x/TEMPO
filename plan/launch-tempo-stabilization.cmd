@echo off
title TEMPO Stabilization Authorization
cd /d "C:\Users\User\Documents\TEMPO-pr-20260718"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\User\Documents\TEMPO-pr-20260718\plan\authorize-tempo-stabilization.ps1"
echo.
echo Keep this window open and report the final result to Codex.
pause

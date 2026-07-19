@echo off
title TEMPO Stabilization Authorization
setlocal
set "TEMPO_ROOT=%~dp0.."
cd /d "%TEMPO_ROOT%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0authorize-tempo-stabilization.ps1" -TempoRoot "%TEMPO_ROOT%"
echo.
echo Keep this window open and report the final result to Codex.
pause

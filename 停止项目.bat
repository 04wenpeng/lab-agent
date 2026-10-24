@echo off
rem stop lab-agent (mysql 3307 / backend 8001 / frontend 5173 / ollama 11434)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":11434" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
rem stop MySQL gracefully-ish (only the instance on 3307)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3307" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
echo lab-agent stopped (close the cmd windows if they are still open)
timeout /t 2 /nobreak >nul

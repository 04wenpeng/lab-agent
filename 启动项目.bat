@echo off
rem ===== lab-agent one-click start =====
rem 1) MySQL first (backend needs it)
start "lab-agent mysql 3307" cmd /k E:\lab-agent\start-mysql.bat
echo waiting for MySQL...
timeout /t 10 /nobreak >nul
rem 2) ollama / backend / frontend
start "lab-agent ollama 11434" cmd /k E:\lab-agent\start-ollama.bat
start "lab-agent backend 8001" cmd /k E:\lab-agent\start-backend.bat
start "lab-agent frontend 5173" cmd /k E:\lab-agent\start-frontend.bat
echo waiting for servers...
timeout /t 12 /nobreak >nul
start http://127.0.0.1:5173
exit

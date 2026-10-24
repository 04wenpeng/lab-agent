@echo off
rem local Ollama (used by the AI assistant), OpenAI-compatible at 127.0.0.1:11434/v1
netstat -ano | findstr ":11434" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
  echo Ollama already running on 11434
  timeout /t 2 /nobreak >nul
  exit /b
)
set "OLLAMA_MODELS=E:\RAG-KnowledgeBase\ollama\models"
set "OLLAMA_HOST=127.0.0.1:11434"
"E:\RAG-KnowledgeBase\ollama\app\ollama.exe" serve
pause

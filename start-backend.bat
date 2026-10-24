@echo off
rem lab-agent backend (FastAPI) on 127.0.0.1:8001
set "PYTHONPATH=E:\lab-agent\backend\.pylibs"
set "TMP=E:\lab-agent\.tmp"
set "TEMP=E:\lab-agent\.tmp"
set "PYTHONIOENCODING=utf-8"
set "HF_ENDPOINT=https://hf-mirror.com"
cd /d E:\lab-agent\backend
"C:\Users\Rayna\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001
pause

@echo off
rem lab-agent frontend (Vite) on 0.0.0.0:5173  (LAN accessible)
cd /d E:\lab-agent\frontend
npm run dev -- --port 5173
pause

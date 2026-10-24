@echo off
rem start project MySQL instance (port 3307, data in E:\lab-agent\mysql-data)
netstat -ano | findstr ":3307" | findstr "LISTENING" >nul
if not errorlevel 1 (
  echo [mysql] already running on 3307
  exit /b 0
)
echo [mysql] starting on 127.0.0.1:3307 ...
start "lab-agent mysql 3307" /min "D:\MySQL\MySQL Server 8.0\bin\mysqld.exe" --no-defaults --basedir="D:\MySQL\MySQL Server 8.0" --datadir="E:\lab-agent\mysql-data" --port=3307 --bind-address=127.0.0.1 --mysqlx=0 --log-error="E:\lab-agent\mysql-data\error.log"
timeout /t 8 /nobreak >nul
netstat -ano | findstr ":3307" | findstr "LISTENING" >nul
if errorlevel 1 (
  echo [mysql] start failed, check E:\lab-agent\mysql-data\error.log
) else (
  echo [mysql] ready
)

@echo off
echo Stopping any instance already on port 8081...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8081" ^| findstr "LISTENING"') do taskkill /f /pid %%p >nul 2>&1
timeout /t 1 >nul

echo Starting UF Alumni Legal Finder...
start "UF Alumni Legal Finder" powershell -NoExit -Command "cd '%~dp0'; python -m uvicorn app:app --reload --host 127.0.0.1 --port 8081"

echo Opening browser in 3 seconds...
timeout /t 3 >nul
start "" "http://127.0.0.1:8081"

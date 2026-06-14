@echo off
echo ==========================================================
echo Starting AI Writing Assistant Backend
echo ==========================================================
cd /d %~dp0

echo [Step 1] Installing python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b %errorlevel%
)

echo [Step 2] Launching server on http://localhost:8765
echo Open http://localhost:8765 in your browser once started.
python main.py
pause

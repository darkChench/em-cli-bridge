@echo off
REM ============================================================
REM  em-cli-bridge one-click setup (Windows)
REM  Does: 1) check Python  2) create venv  3) install deps
REM  Usage: double-click setup.bat  OR  run in cmd: setup.bat
REM ============================================================

echo.
echo ============================================================
echo   em-cli-bridge setup
echo ============================================================
echo.

REM --- 1. Check Python ---
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found. Please install Python 3.8+ first:
    echo    https://www.python.org/downloads/
    echo    Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do set PYVER=%%v
echo    OK - %PYVER%

REM --- 2. Create venv ---
echo.
echo [2/4] Creating virtual environment .venv ...
if exist .venv (
    echo    .venv already exists, skipped. Delete .venv folder to recreate.
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo    OK - venv created
)

REM --- 3. Activate and upgrade pip ---
echo.
echo [3/4] Activating venv and upgrading pip ...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
echo    OK - activated

REM --- 4. Install deps ---
echo.
echo [4/4] Installing dependencies (requirements.txt) ...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Dependency install failed. Check network or run manually:
    echo    pip install -r requirements.txt
    pause
    exit /b 1
)

REM --- Done ---
echo.
echo ============================================================
echo   Setup complete!
echo ============================================================
echo.
echo  Next steps:
echo   1. Activate venv in each new cmd window before running:
echo        .venv\Scripts\activate
echo      Then test:
echo        python device_cli.py cmd qSensor
echo.
echo   2. For MCP server, install optional deps:
echo        pip install -r requirements-mcp.txt
echo.
echo   3. Find serial port: Device Manager -^> Ports (COM ^& LPT)
echo.
pause

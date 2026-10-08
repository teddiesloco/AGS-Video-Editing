@echo off
chcp 65001 >nul
echo ==================================================
echo 🎬 Cai dat AGS-Video-Editing cho Windows
echo ==================================================

:: 1. Kiem tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Chua cai Python. Vui long cai Python 3.10+ tu python.org va tich vao 'Add Python to PATH'
    pause
    exit /b 1
)

:: 2. Kiem tra FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Dang cai dat FFmpeg qua winget...
    winget install Gyan.FFmpeg
    if %errorlevel% neq 0 (
        echo [!] Khong the tu dong cai FFmpeg. Vui long tai FFmpeg tu gyan.dev/ffmpeg va them vao PATH.
    )
)

:: 3. Tao virtualenv
cd /d "%~dp0"
if not exist "venv" (
    echo [*] Dang tao moi truong ao venv...
    python -m venv venv
)

echo [*] Dang cai dat thu vien Python...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo ==================================================
echo 🎉 Cai dat thanh cong!
echo ==================================================
pause

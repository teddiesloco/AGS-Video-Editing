@echo off
chcp 65001 >nul
echo ==================================================
echo 🎬 Cai dat AGS Video Editing (AGS - Agent Space) cho Windows
echo ==================================================

:: 1. Kiem tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Chua cai Python. Vui long cai Python 3.10+ tu python.org va tich vao 'Add Python to PATH'
    pause
    exit /b 1
)

:: 2. Kiem tra FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [*] Dang cai dat FFmpeg qua winget...
    winget install Gyan.FFmpeg
    if errorlevel 1 (
        echo [!] Khong the tu dong cai FFmpeg. Vui long tai FFmpeg tu gyan.dev/ffmpeg va them vao PATH.
    ) else (
        echo [*] Da cai FFmpeg. Mo cua so cmd moi de PATH cap nhat.
    )
)

:: 3. Tao virtualenv trong thu muc repo
cd /d "%~dp0"
if not exist "venv" (
    echo [*] Dang tao moi truong ao venv...
    python -m venv venv
)

echo [*] Dang cai dat thu vien Python...
venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r requirements.txt

:: 4. (Tuy chon) MCP server cho Claude Code / Claude Desktop / Codex / Antigravity / Cursor
set "WITH_MCP="
set /p WITH_MCP=Cai them MCP server (tuy chon)? [y/N]: 
if /I "%WITH_MCP%"=="y" (
    venv\Scripts\python -m pip install -r requirements-mcp.txt
    echo [*] Da cai MCP. Cau hinh client: xem HUONG-DAN-SU-DUNG.md, Phan 3.
) else (
    echo [i] Bo qua MCP. Cai sau bang: venv\Scripts\python -m pip install -r requirements-mcp.txt
)

echo ==================================================
echo 🎉 Cai dat thanh cong!
echo Chay script: venv\Scripts\python scripts\ags_cut_silence.py ^<video^>
echo Kiem dinh:   venv\Scripts\python harness\ags_anti_slop_guard.py ^<video^>
echo ==================================================
pause

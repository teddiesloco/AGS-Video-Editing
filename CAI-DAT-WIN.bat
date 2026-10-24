@echo off
setlocal EnableExtensions
chcp 65001 >nul
rem AGS Video Editing - cai moi truong cho Windows (chua duoc chay thu tren Windows that).
rem   CAI-DAT-WIN.bat           cai day du: loi + MCP + ca hai giong doc cuc bo (VieNeu, ZeroTTS) + SFX
rem   CAI-DAT-WIN.bat --core    khong cai thu vien TTS
rem   CAI-DAT-WIN.bat --yes     duoc phep tu cai Python 3.11 / FFmpeg con thieu bang winget
rem Moi tuy chon khac chuyen thang cho scripts\ags_setup.py (--check, --warmup-tts, --print-mcp, ...).
rem Chay duoc tu moi thu muc, ke ca duong dan co dau cach. Dat AGS_PYTHON de chi dinh Python 3.11/3.12.
set "ROOT=%~dp0"
set "ASSUME_YES=0"
for %%A in (%*) do (
    if /I "%%~A"=="--yes" set "ASSUME_YES=1"
    if /I "%%~A"=="-y" set "ASSUME_YES=1"
)
set "AGS_LINKS=%LOCALAPPDATA%\Microsoft\WinGet\Links"
if exist "%AGS_LINKS%" set "PATH=%PATH%;%AGS_LINKS%"

call :find_python
if not defined PY_EXE if "%ASSUME_YES%"=="1" call :install_python
if not defined PY_EXE (
    echo Chua co Python 3.11/3.12. Cai: winget install -e --id Python.Python.3.11
    echo roi chay lai, hoac them --yes de installer tu cai, hoac dat AGS_PYTHON.
    exit /b 3
)

where ffmpeg >nul 2>&1 && where ffprobe >nul 2>&1
if errorlevel 1 if "%ASSUME_YES%"=="1" call :install_ffmpeg

"%PY_EXE%" %PY_ARGS% "%ROOT%scripts\ags_setup.py" %*
exit /b %errorlevel%

:find_python
set "PY_EXE="
set "PY_ARGS="
if defined AGS_PYTHON set "PY_EXE=%AGS_PYTHON%"
if defined PY_EXE exit /b 0
py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set "PY_EXE=py"
    set "PY_ARGS=-3.11"
    exit /b 0
)
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set "PY_EXE=py"
    set "PY_ARGS=-3.12"
)
exit /b 0

:install_python
echo Cai Python 3.11 bang winget...
winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
call :find_python
exit /b 0

:install_ffmpeg
echo Cai FFmpeg bang winget...
winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
if exist "%AGS_LINKS%" set "PATH=%PATH%;%AGS_LINKS%"
exit /b 0

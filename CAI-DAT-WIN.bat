@echo off
setlocal EnableExtensions
chcp 65001 >nul
rem AGS Video Editing - cai moi truong cho Windows (chua duoc chay thu tren Windows that).
rem   CAI-DAT-WIN.bat           cai day du: loi + MCP + ca hai giong doc cuc bo (VieNeu, ZeroTTS) + SFX, roi dang ky
rem                             3 MCP + skill vao Antigravity/Gemini, Claude Code, Codex, Cursor (--install-all-clients)
rem   CAI-DAT-WIN.bat --core    khong cai thu vien TTS
rem   CAI-DAT-WIN.bat --yes     duoc phep tu cai Python 3.11 / FFmpeg con thieu bang winget
rem   CAI-DAT-WIN.bat --activate TOKEN   cai nhu tren + kich hoat ban quyen (--targets/--home cung chuyen cho buoc client)
rem   CAI-DAT-WIN.bat --no-configs       cai moi truong, khong ghi cau hinh MCP nao
rem Lenh don (--check, --warmup-tts, --print-mcp, --install-all-clients, ...) chuyen nguyen cho scripts\ags_setup.py.
rem Chay duoc tu moi thu muc, ke ca duong dan co dau cach. Dat AGS_PYTHON de chi dinh Python 3.11/3.12.
set "ROOT=%~dp0"
set "ASSUME_YES=0"
for %%A in (%*) do (
    if /I "%%~A"=="--yes" set "ASSUME_YES=1"
    if /I "%%~A"=="-y" set "ASSUME_YES=1"
)
set "ACTION=0"
set "SKIP_CLIENTS=0"
set "INSTALL_ARGS="
set "CLIENT_ARGS=--install-all-clients"
:parse
if "%~1"=="" goto parsed
set "ARG=%~1"
if /I "%ARG%"=="--activate" goto take_value
if /I "%ARG%"=="--targets" goto take_value
if /I "%ARG%"=="--home" goto take_value
if /I "%ARG%"=="--no-configs" set "SKIP_CLIENTS=1"
for %%F in (--check --warmup-tts --print-mcp --register-claude-code --machine-id --license-status --install-all-clients -h --help) do if /I "%ARG%"=="%%F" set "ACTION=1"
set INSTALL_ARGS=%INSTALL_ARGS% %1
shift
goto parse
:take_value
set CLIENT_ARGS=%CLIENT_ARGS% %1 %2
shift
shift
goto parse
:parsed
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

if "%ACTION%"=="1" goto run_action
"%PY_EXE%" %PY_ARGS% "%ROOT%scripts\ags_setup.py" %INSTALL_ARGS%
if errorlevel 1 exit /b %errorlevel%
if "%SKIP_CLIENTS%"=="1" exit /b 0
"%ROOT%venv\Scripts\python.exe" "%ROOT%scripts\ags_setup.py" %CLIENT_ARGS%
exit /b %errorlevel%

:run_action
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

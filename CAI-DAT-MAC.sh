#!/usr/bin/env bash
# AGS Video Editing — cài môi trường cho macOS / Linux.
#   ./CAI-DAT-MAC.sh            cài đầy đủ: lõi + MCP + cả hai giọng đọc cục bộ (VieNeu, ZeroTTS) + SFX, rồi đăng ký
#                               3 MCP + skill vào Antigravity/Gemini, Claude Code, Codex, Cursor (--install-all-clients)
#   ./CAI-DAT-MAC.sh --core     không cài thư viện TTS
#   ./CAI-DAT-MAC.sh --yes      được phép tự cài Python 3.11 / FFmpeg còn thiếu (Homebrew hoặc uv)
#   ./CAI-DAT-MAC.sh --activate <TOKEN>   cài như trên + kích hoạt bản quyền (--targets/--home cũng chuyển cho bước client)
#   ./CAI-DAT-MAC.sh --no-configs         cài môi trường, không ghi cấu hình MCP nào
# Lệnh đơn (--check, --warmup-tts, --print-mcp, --install-all-clients, …) chuyển nguyên cho scripts/ags_setup.py.
# Chạy được từ bất kỳ thư mục nào, kể cả đường dẫn có dấu cách. Đặt AGS_PYTHON để chỉ định Python 3.11/3.12.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSUME_YES=0
ACTION=0
SKIP_CLIENTS=0
INSTALL_ARGS=()
CLIENT_ARGS=(--install-all-clients)
ARGS=("$@")
i=0
while [[ $i -lt ${#ARGS[@]} ]]; do
    arg="${ARGS[$i]}"
    case "$arg" in
        --activate|--targets|--home) CLIENT_ARGS+=("$arg" "${ARGS[$((i + 1))]:-}"); i=$((i + 2)); continue ;;
        --yes|-y) ASSUME_YES=1 ;;
        --no-configs) SKIP_CLIENTS=1 ;;
        --check|--warmup-tts|--print-mcp|--register-claude-code|--machine-id|--license-status|--install-all-clients|-h|--help)
            ACTION=1 ;;
    esac
    INSTALL_ARGS+=("$arg"); i=$((i + 1))
done

supported() {
    "$1" -c 'import sys; sys.exit(0 if sys.version_info[:2] in ((3, 11), (3, 12)) else 1)' >/dev/null 2>&1
}

find_python() {
    local candidate path
    if [[ -n "${AGS_PYTHON:-}" ]]; then echo "$AGS_PYTHON"; return 0; fi
    for candidate in python3.11 python3.12 python3; do
        path="$(command -v "$candidate" 2>/dev/null || true)"
        if [[ -n "$path" ]] && supported "$path"; then echo "$path"; return 0; fi
    done
    if command -v uv >/dev/null 2>&1; then
        for candidate in 3.11 3.12; do
            path="$(uv python find "$candidate" 2>/dev/null || true)"
            if [[ -n "$path" ]] && supported "$path"; then echo "$path"; return 0; fi
        done
    fi
    if command -v brew >/dev/null 2>&1; then
        path="$(brew --prefix python@3.11 2>/dev/null || true)/bin/python3.11"
        if [[ -x "$path" ]] && supported "$path"; then echo "$path"; return 0; fi
    fi
    return 1
}

PYTHON="$(find_python || true)"
if [[ -z "$PYTHON" && $ASSUME_YES -eq 1 ]]; then
    if command -v brew >/dev/null 2>&1; then
        echo "Cài Python 3.11 bằng Homebrew…"; brew install python@3.11
    elif command -v uv >/dev/null 2>&1; then
        echo "Cài Python 3.11 bằng uv…"; uv python install 3.11
    fi
    PYTHON="$(find_python || true)"
fi
if [[ -z "$PYTHON" ]]; then
    echo "Chưa có Python 3.11/3.12. Cài bằng một trong các lệnh:" >&2
    echo "  macOS:  brew install python@3.11     (hoặc: uv python install 3.11)" >&2
    echo "  Linux:  sudo apt install python3.11 python3.11-venv   (hoặc: uv python install 3.11)" >&2
    echo "rồi chạy lại, hoặc thêm --yes để installer tự cài bằng Homebrew/uv; hoặc đặt AGS_PYTHON." >&2
    exit 3
fi

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
    if [[ $ASSUME_YES -eq 1 ]] && command -v brew >/dev/null 2>&1; then
        echo "Cài FFmpeg bằng Homebrew…"; brew install ffmpeg
    fi
fi

if [[ $ACTION -eq 1 ]]; then
    exec "$PYTHON" "$ROOT/scripts/ags_setup.py" "$@"
fi
"$PYTHON" "$ROOT/scripts/ags_setup.py" ${INSTALL_ARGS[@]+"${INSTALL_ARGS[@]}"}
if [[ $SKIP_CLIENTS -eq 1 ]]; then exit 0; fi
exec "$ROOT/venv/bin/python" "$ROOT/scripts/ags_setup.py" "${CLIENT_ARGS[@]}"

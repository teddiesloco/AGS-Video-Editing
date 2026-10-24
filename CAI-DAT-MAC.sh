#!/usr/bin/env bash
# AGS Video Editing — cài môi trường cho macOS / Linux.
#   ./CAI-DAT-MAC.sh            cài đầy đủ: lõi + MCP + cả hai giọng đọc cục bộ (VieNeu, ZeroTTS) + SFX
#   ./CAI-DAT-MAC.sh --core     không cài thư viện TTS
#   ./CAI-DAT-MAC.sh --yes      được phép tự cài Python 3.11 / FFmpeg còn thiếu (Homebrew hoặc uv)
# Mọi tuỳ chọn khác chuyển thẳng cho scripts/ags_setup.py (--check, --warmup-tts, --print-mcp, …).
# Chạy được từ bất kỳ thư mục nào, kể cả đường dẫn có dấu cách. Đặt AGS_PYTHON để chỉ định Python 3.11/3.12.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSUME_YES=0
for arg in "$@"; do
    if [[ "$arg" == "--yes" || "$arg" == "-y" ]]; then ASSUME_YES=1; fi
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

exec "$PYTHON" "$ROOT/scripts/ags_setup.py" "$@"

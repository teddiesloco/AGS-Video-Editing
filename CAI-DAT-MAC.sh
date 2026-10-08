#!/usr/bin/env bash
# ==============================================================================
# AGS Video Editing (AGS — Agent Space) — Installer cho macOS (Apple Silicon / Intel)
# ==============================================================================
set -e

echo "=================================================="
echo "🎬 Cài đặt AGS Video Editing (AGS — Agent Space) cho macOS"
echo "=================================================="

# 1. Homebrew
if ! command -v brew &>/dev/null; then
    echo "⚠️ Chưa có Homebrew. Đang cài đặt Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 2. FFmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "📦 Đang cài đặt FFmpeg..."
    brew install ffmpeg
else
    echo "✅ FFmpeg đã sẵn sàng."
fi

# 3. Python 3
if ! command -v python3 &>/dev/null; then
    echo "📦 Đang cài đặt Python 3..."
    brew install python
else
    echo "✅ Python 3 đã sẵn sàng: $(python3 --version)"
fi

# 4. Môi trường ảo venv trong thư mục repo
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "⚙️ Đang tạo virtualenv (venv)..."
    python3 -m venv venv
fi

echo "📦 Đang cài đặt các thư viện Python..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 5. (Tuỳ chọn) MCP server cho Claude Code / Claude Desktop / Codex / Antigravity / Cursor
read -r -p "Cài thêm MCP server (tuỳ chọn)? [y/N] " WITH_MCP || true
if [[ "$WITH_MCP" =~ ^[Yy]$ ]]; then
    ./venv/bin/pip install -r requirements-mcp.txt
    echo "✅ Đã cài MCP. Cấu hình client: xem HUONG-DAN-SU-DUNG.md, Phần 3."
else
    echo "ℹ️ Bỏ qua MCP. Cài sau bằng: ./venv/bin/pip install -r requirements-mcp.txt"
fi

echo ""
echo "=================================================="
echo "🎉 Cài đặt hoàn tất!"
echo "Cách dùng:"
echo "1. Chạy script: ./venv/bin/python scripts/ags_cut_silence.py <video>"
echo "2. Trong Claude Code / Codex / Antigravity / Cursor: mở thư mục này và chat theo HUONG-DAN-SU-DUNG.md"
echo "3. Kiểm định video: ./venv/bin/python harness/ags_anti_slop_guard.py <video>"
echo "=================================================="

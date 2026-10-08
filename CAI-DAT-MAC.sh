#!/usr/bin/env bash
# ==============================================================================
# AGS-Video-Editing — 1-Click Installer cho macOS (Apple Silicon / Intel)
# ==============================================================================
set -e

echo "=================================================="
echo "🎬 Cài đặt AGS-Video-Editing cho macOS"
echo "=================================================="

# 1. Kiểm tra Homebrew
if ! command -v brew &>/dev/null; then
    echo "⚠️ Chưa có Homebrew. Đang cài đặt Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 2. Cài đặt FFmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "📦 Đang cài đặt FFmpeg..."
    brew install ffmpeg
else
    echo "✅ FFmpeg đã sẵn sàng."
fi

# 3. Kiểm tra Python 3
if ! command -v python3 &>/dev/null; then
    echo "📦 Đang cài đặt Python 3..."
    brew install python
else
    echo "✅ Python 3 đã sẵn sàng: $(python3 --version)"
fi

# 4. Tạo môi trường ảo venv
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "⚙️ Đang tạo virtualenv (venv)..."
    python3 -m venv venv
fi

echo "📦 Đang cài đặt các thư viện Python..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo ""
echo "=================================================="
echo "🎉 Cài đặt hoàn tất 100%!"
echo "Cách dùng:"
echo "1. Mở Claude Code / Terminal: gõ lệnh các skill (/ags-edit-az, /ags-edit-hook...)"
echo "2. Hoặc chạy script trực tiếp: ./venv/bin/python scripts/cut_silence.py <video>"
echo "=================================================="

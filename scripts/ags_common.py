#!/usr/bin/env python3
"""
AGS (Agent Space) — tiện ích dùng chung cho các script AGS Video Editing.

- run_cmd / media_duration / display_size: gọi FFmpeg/ffprobe, báo lỗi kèm stderr.
- load_font / wrap_text / fit_text: font có đủ dấu tiếng Việt trên macOS, Windows, Linux.
- transcribe_words / group_words / clean_subtitle_text: bóc băng Whisper theo từng từ.
- timeline_frames / encode_frames: dựng khung hình theo đúng mốc thời gian audio rồi xuất MP4.
"""

import functools
import json
import math
import re
import subprocess

from PIL import ImageFont

# Chuẩn âm lượng phát sóng mạng xã hội; -ar 48000 vì loudnorm xuất 192 kHz.
LOUDNORM = "loudnorm=I=-14:LRA=11:TP=-1.5"

# Font có đủ dấu tiếng Việt, theo thứ tự ưu tiên (tên file trên macOS, Windows, Linux).
# Pillow tự tìm tên file trong thư mục font hệ thống của từng hệ điều hành.
FONT_FILES = {
    "bold": ["Montserrat-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf",
             "DejaVuSans-Bold.ttf", "NotoSans-Bold.ttf", "LiberationSans-Bold.ttf"],
    "regular": ["Montserrat-SemiBold.ttf", "Arial.ttf", "arial.ttf",
                "DejaVuSans.ttf", "NotoSans-Regular.ttf", "LiberationSans-Regular.ttf"],
    "serif": ["Georgia.ttf", "georgia.ttf",
              "DejaVuSerif.ttf", "NotoSerif-Regular.ttf", "LiberationSerif-Regular.ttf"],
}

FILLER_PUNCT = re.compile(r"[^\w]+")


def run_cmd(cmd):
    result = subprocess.run([str(c) for c in cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"Lệnh thất bại: {' '.join(str(c) for c in cmd)}\nLỗi: {result.stderr[-3000:]}")
    return result


def media_duration(path):
    out = run_cmd(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                   "-of", "default=noprint_wrappers=1:nokey=1", path]).stdout
    return float(out.strip())


def display_size(video_path):
    """Kích thước hiển thị (đã tính metadata xoay của video quay điện thoại)."""
    info = json.loads(run_cmd([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height:stream_tags=rotate:stream_side_data=rotation",
        "-of", "json", video_path,
    ]).stdout)["streams"][0]
    rotation = int(float(info.get("tags", {}).get("rotate", 0) or 0))
    for side_data in info.get("side_data_list", []):
        if "rotation" in side_data:
            rotation = int(float(side_data["rotation"]))
    width, height = info["width"], info["height"]
    return (height, width) if abs(rotation) % 180 == 90 else (width, height)


@functools.lru_cache(maxsize=None)
def font_path(style):
    for name in FONT_FILES[style]:
        try:
            return ImageFont.truetype(name, 12).path
        except OSError:
            continue
    raise RuntimeError(
        f"Không tìm thấy font hỗ trợ tiếng Việt ({', '.join(FONT_FILES[style])}). "
        "Hãy cài DejaVu Sans hoặc Noto Sans rồi chạy lại."
    )


def load_font(style, size):
    return ImageFont.truetype(font_path(style), int(size))


def wrap_text(draw, text, font, max_width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and draw.textlength(trial, font=font) > max_width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def fit_text(draw, text, style, max_width, max_lines, size, min_size):
    """Giảm cỡ chữ tới khi text vừa max_width trong tối đa max_lines dòng."""
    while True:
        font = load_font(style, size)
        lines = wrap_text(draw, text, font, max_width)
        fits = len(lines) <= max_lines and all(draw.textlength(l, font=font) <= max_width for l in lines)
        if fits or size <= min_size:
            return font, lines
        size = max(min_size, int(size * 0.9))


def clean_subtitle_text(text):
    """Lọc rác Whisper: nhãn âm thanh ảo giác và từ lặp >= 3 lần liên tiếp."""
    cleaned = re.sub(r"\[(nhạc|tiếng cười|vỗ tay|music|applause)\]", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(\w+)(?:\s+\1\b){2,}", r"\1", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_word(word):
    return FILLER_PUNCT.sub("", word.lower())


def load_audio_16k(media_path):
    """Giải mã audio bằng FFmpeg thành mảng float32 mono 16 kHz (không phụ thuộc API của PyAV)."""
    import numpy as np

    pcm = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(media_path),
                          "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if pcm.returncode != 0 or not pcm.stdout:
        raise RuntimeError(f"Không đọc được audio từ {media_path}: {pcm.stderr.decode('utf-8', 'replace')[-2000:]}")
    return np.frombuffer(pcm.stdout, np.int16).astype(np.float32) / 32768.0


def transcribe_words(media_path, model_size="base"):
    """Bóc băng bằng faster-whisper; trả về [(start, end, word)] theo thời gian."""
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, _ = model.transcribe(load_audio_16k(media_path), beam_size=5, word_timestamps=True, vad_filter=True)
    return [(w.start, w.end, w.word.strip()) for seg in segments for w in (seg.words or []) if w.word.strip()]


def group_words(words, max_chars=32, max_seconds=3.0):
    """Gom từ thành cụm phụ đề ngắn [(start, end, text)], ngắt ở dấu câu."""
    chunks, current = [], []

    def flush():
        if current:
            text = clean_subtitle_text(" ".join(w[2] for w in current))
            if text:
                chunks.append((current[0][0], current[-1][1], text))
            current.clear()

    for word in words:
        if current:
            length = len(" ".join(w[2] for w in current)) + 1 + len(word[2])
            if length > max_chars or word[1] - current[0][0] > max_seconds:
                flush()
        current.append(word)
        if word[2][-1] in ".!?…":
            flush()
    flush()
    return chunks


def timeline_frames(chunks, total_seconds, fps, render):
    """Sinh đủ khung hình cho toàn bộ audio; mỗi khung gọi render(chunk_index, frame_in_chunk).

    chunk_index = -1 trước câu đầu tiên; sau mỗi câu, câu đó được giữ tới khi câu sau bắt đầu.
    """
    starts = [round(c[0] * fps) for c in chunks]
    index = -1
    for n in range(max(1, math.ceil(total_seconds * fps))):
        while index + 1 < len(chunks) and starts[index + 1] <= n:
            index += 1
        yield render(index, n - starts[index] if index >= 0 else n)


def encode_frames(frames, size, fps, audio_path, output_path):
    """Ghi chuỗi khung hình RGB (bytes) + audio thành MP4 H.264/AAC 48 kHz chuẩn -14 LUFS."""
    width, height = size
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
        "-i", str(audio_path),
        "-map", "0:v:0", "-map", "1:a:0",
        "-af", LOUDNORM, "-ar", "48000",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
        str(output_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for frame in frames:
            proc.stdin.write(frame)
    except BrokenPipeError:
        pass
    finally:
        try:
            proc.stdin.close()
        except BrokenPipeError:
            pass
    error = proc.stderr.read().decode("utf-8", "replace")
    if proc.wait() != 0:
        raise RuntimeError(f"FFmpeg lỗi khi xuất video: {error[-3000:]}")

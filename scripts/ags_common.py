#!/usr/bin/env python3
"""
AGS (Agent Space) — tiện ích dùng chung cho các script AGS Video Editing.

- run_cmd / media_duration / video_info / display_size / filter_path: gọi FFmpeg/ffprobe, báo lỗi kèm stderr.
- nfc / load_font / wrap_text / fit_text: chữ Unicode NFC, font có đủ dấu tiếng Việt trên macOS, Windows, Linux.
- SAFE_ZONE_9X16 / safe_box: vùng an toàn để đặt chữ (định nghĩa DUY NHẤT tại đây, mọi script dùng chung).
- load_audio / transcribe_words / group_word_lists / group_words: bóc băng Whisper theo từng từ.
- timeline_frames / encode_frames: dựng khung hình theo đúng mốc thời gian audio rồi xuất MP4.
"""

import functools
import json
import math
import re
import subprocess
import unicodedata
from fractions import Fraction
from pathlib import Path

from PIL import ImageFont

# Chuẩn âm lượng phát sóng mạng xã hội: -14 LUFS; -ar 48000 vì loudnorm xuất 192 kHz.
# TP=-2.0: mã hoá AAC đẩy true peak lên tới ~0.8 dB (đo thực tế), vẫn giữ dưới trần -1 dBTP của harness.
LOUDNORM = "loudnorm=I=-14:LRA=11:TP=-2.0"

# Vùng an toàn cho chữ trên video dọc 9:16, tính theo tỉ lệ khung (không phụ thuộc độ phân giải).
# Lấy lề lớn nhất mỗi cạnh từ 3 tài liệu chính thức về quảng cáo dọc (chặt hơn giao diện video thường), để chữ
# không bị nút, avatar, caption hay nút CTA che trên cả TikTok, Instagram Reels và YouTube Shorts:
#   - Meta, Instagram Reels ads: chừa 14% trên, 35% dưới, 6% mỗi bên.
#     https://www.facebook.com/business/ads-guide/update/video/instagram-reels/outcome-engagement
#   - Google Ads, YouTube vertical video ads 1080x1920: 288 px trên, 672 px dưới, 48 px trái, 192 px phải.
#     https://support.google.com/google-ads/answer/13547298 (mục "Universal safe zones for video ads on YouTube")
#   - TikTok TopView, giai đoạn in-feed, mẫu 720x1280: 160 px trên, 440 px dưới, 80 px mỗi bên có thể bị cắt,
#     cột nút bên phải thêm 120 px (cao 720 px tính từ đáy).
#     https://ads.tiktok.com/help/article/tiktok-reservation-topview (file "TopView safe zones .zip")
# => trên 288/1920 = 15%, dưới 35%, trái 80/720 = 11.1%, phải (80 + 120)/720 = 27.8%.
SAFE_ZONE_9X16 = {"left": 0.111, "top": 0.15, "right": 0.278, "bottom": 0.35}
# Video không dọc 9:16 (ngang, vuông): chừa lề đều mỗi cạnh.
SAFE_MARGIN_OTHER = 0.08

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
STANDARD_FPS = [Fraction(24000, 1001), Fraction(24), Fraction(25), Fraction(30000, 1001), Fraction(30),
                Fraction(50), Fraction(60000, 1001), Fraction(60)]


def nfc(text):
    """Chuẩn hoá Unicode NFC (dấu tiếng Việt dựng sẵn) trước khi vẽ hoặc ghi chữ."""
    return unicodedata.normalize("NFC", str(text))


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


def _nominal_fps(avg, real):
    """FPS danh định: avg_frame_rate (gần chuẩn thì làm tròn về chuẩn, hợp với video điện thoại VFR)."""
    for text in (avg, real):
        try:
            fps = Fraction(text)
        except (ValueError, ZeroDivisionError, TypeError):
            continue
        if 1 <= fps <= 240:
            std = min(STANDARD_FPS, key=lambda s: abs(fps - s))
            return std if abs(fps - std) <= std * Fraction(5, 1000) else fps.limit_denominator(1001)
    return Fraction(30)


def video_info(path):
    """Thông số video: size (rộng, cao hiển thị — đã tính metadata xoay), fps (Fraction), duration (giây),
    audio_channels (0 nếu không có tiếng)."""
    data = json.loads(run_cmd([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,width,height,avg_frame_rate,r_frame_rate,duration,channels"
        ":stream_tags=rotate:stream_side_data=rotation",
        "-of", "json", path,
    ]).stdout)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise RuntimeError(f"{path}: không có luồng hình")
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    rotation = int(float(video.get("tags", {}).get("rotate", 0) or 0))
    for side_data in video.get("side_data_list", []):
        if "rotation" in side_data:
            rotation = int(float(side_data["rotation"]))
    width, height = video["width"], video["height"]
    if abs(rotation) % 180 == 90:
        width, height = height, width
    duration = 0.0
    for value in (video.get("duration"), data.get("format", {}).get("duration")):
        try:
            duration = float(value)
            break
        except (TypeError, ValueError):
            continue
    return {
        "size": (width, height),
        "fps": _nominal_fps(video.get("avg_frame_rate"), video.get("r_frame_rate")),
        "duration": duration,
        "audio_channels": int(audio.get("channels") or 0) if audio else 0,
    }


def display_size(video_path):
    """Kích thước hiển thị (đã tính metadata xoay của video quay điện thoại)."""
    return video_info(video_path)["size"]


def filter_path(path):
    """Đường dẫn làm tham số bộ lọc FFmpeg (subtitles, sendcmd...): dấu '/', escape ':' của ổ đĩa Windows."""
    return Path(path).resolve().as_posix().replace(":", "\\:")


def safe_box(width, height):
    """(x0, y0, x1, y1) pixel của vùng an toàn để đặt chữ: SAFE_ZONE_9X16 với video dọc, lề đều với video khác."""
    if height >= 1.6 * width:
        z = SAFE_ZONE_9X16
        return (round(width * z["left"]), round(height * z["top"]),
                round(width * (1 - z["right"])), round(height * (1 - z["bottom"])))
    m = SAFE_MARGIN_OTHER
    return round(width * m), round(height * m), round(width * (1 - m)), round(height * (1 - m))


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


def font_family(style):
    """Tên họ font (dùng cho phụ đề .ASS) của file font mà font_path(style) tìm được."""
    return ImageFont.truetype(font_path(style), 12).getname()[0]


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
    """Giảm cỡ chữ tới khi text (chuẩn hoá NFC) vừa max_width trong tối đa max_lines dòng."""
    text = nfc(text)
    while True:
        font = load_font(style, size)
        lines = wrap_text(draw, text, font, max_width)
        fits = len(lines) <= max_lines and all(draw.textlength(l, font=font) <= max_width for l in lines)
        if fits or size <= min_size:
            return font, lines
        size = max(min_size, int(size * 0.9))


def clean_subtitle_text(text):
    """Lọc rác Whisper: nhãn âm thanh ảo giác và từ lặp >= 3 lần liên tiếp."""
    cleaned = re.sub(r"\[(nhạc|tiếng cười|vỗ tay|music|applause)\]", "", nfc(text), flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(\w+)(?:\s+\1\b){2,}", r"\1", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_word(word):
    return FILLER_PUNCT.sub("", nfc(word).lower())


def load_audio(media_path, sample_rate=16000, channels=1):
    """Giải mã audio bằng FFmpeg thành float32: mảng (n,) khi mono, (n, channels) khi nhiều kênh."""
    import numpy as np

    pcm = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(media_path),
                          "-vn", "-ac", str(channels), "-ar", str(sample_rate), "-f", "f32le", "-"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if pcm.returncode != 0 or not pcm.stdout:
        raise RuntimeError(f"Không đọc được audio từ {media_path}: {pcm.stderr.decode('utf-8', 'replace')[-2000:]}")
    data = np.frombuffer(pcm.stdout, "<f4")
    return data if channels == 1 else data.reshape(-1, channels)


def transcribe_words(media_path, model_size="base"):
    """Bóc băng bằng faster-whisper; trả về [(start, end, word)] (chữ NFC) theo thời gian.
    model_size: tên model faster-whisper (tiny, base, small, medium, large-v3, large-v3-turbo...) hoặc thư mục model."""
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, _ = model.transcribe(load_audio(media_path), beam_size=5, word_timestamps=True, vad_filter=True)
    return [(w.start, w.end, nfc(w.word.strip())) for seg in segments for w in (seg.words or []) if w.word.strip()]


def _drop_whisper_junk(words):
    """Bỏ nhãn âm thanh ảo giác; chuỗi >= 3 từ giống hệt nhau liên tiếp chỉ giữ từ đầu."""
    kept = []
    for start, end, word in words:
        text = clean_subtitle_text(word)
        if text:
            kept.append((start, end, text))
    result, i = [], 0
    while i < len(kept):
        j = i
        while j + 1 < len(kept) and normalize_word(kept[j + 1][2]) == normalize_word(kept[i][2]):
            j += 1
        result.extend(kept[i:j + 1] if j - i < 2 else kept[i:i + 1])
        i = j + 1
    return result


def group_word_lists(words, max_chars=32, max_seconds=3.0):
    """Gom từ [(start, end, word)] thành các cụm ngắn (mỗi cụm là list từ), ngắt ở dấu câu."""
    groups, current = [], []
    for word in _drop_whisper_junk(words):
        if current:
            length = len(" ".join(w[2] for w in current)) + 1 + len(word[2])
            if length > max_chars or word[1] - current[0][0] > max_seconds:
                groups.append(current)
                current = []
        current.append(word)
        if word[2][-1] in ".!?…":
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def group_words(words, max_chars=32, max_seconds=3.0):
    """Gom từ thành cụm phụ đề ngắn [(start, end, text)], ngắt ở dấu câu."""
    return [(g[0][0], g[-1][1], " ".join(w[2] for w in g)) for g in group_word_lists(words, max_chars, max_seconds)]


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

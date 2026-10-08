#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: Cắt khoảng lặng & từ đệm
1. Đo độ to audio (RMS 30 ms, bước 10 ms). Chỗ nhỏ hơn mức giọng nói (phân vị 95% độ to của file) quá
   --threshold-db dB và kéo dài >= --min-silence giây là khoảng lặng → cắt, chừa 0.10 s trước và 0.15 s sau lời nói.
2. Whisper bóc băng theo từng từ; từ đệm ('ờ, à, ừm...') bị cắt, mép cắt dời về chỗ nhỏ tiếng nhất gần đó.
3. Mốc cắt làm tròn theo khung hình: hình cắt chính xác từng khung (encode lại H.264), tiếng nối bằng crossfade
   equal-power 25 ms ở mỗi mối nối (không lách cách), chuẩn hoá -14 LUFS. Giữ nguyên khung hình gốc.
"""

import argparse
import sys
import tempfile
from pathlib import Path

import numpy as np

from ags_common import LOUDNORM, load_audio, normalize_word, run_cmd, transcribe_words, video_info

FILLERS = {"ờ", "à", "ừm", "ừ", "hả", "um", "uh", "er"}
HOP = 0.01            # bước đo độ to (giây)
WINDOW_HOPS = 3       # cửa sổ RMS = 3 bước = 30 ms
PRE_ROLL = 0.10       # chừa trước khi lời nói bắt đầu
POST_ROLL = 0.15      # chừa sau khi lời nói kết thúc
MIN_SPEECH = 0.08     # tiếng ngắn hơn mức này (tiếng tách, chạm mic) vẫn tính là lặng
MIN_KEEP = 0.12       # mảnh giữ lại ngắn hơn mức này bị bỏ
SNAP = 0.12           # tìm chỗ nhỏ tiếng nhất trong khoảng này quanh mép từ đệm
CROSSFADE = 0.025     # crossfade audio ở mỗi mối nối (giây)
SAMPLE_RATE = 48000


def loudness_db(mono, sample_rate):
    """Độ to (dBFS) mỗi bước HOP, cửa sổ RMS dài WINDOW_HOPS bước."""
    hop = int(round(HOP * sample_rate))
    count = len(mono) // hop
    if count == 0:
        return np.zeros(0)
    power = (mono[:count * hop].astype(np.float64).reshape(count, hop) ** 2).mean(axis=1)
    power = np.convolve(power, np.ones(WINDOW_HOPS) / WINDOW_HOPS, mode="same")
    return 10 * np.log10(power + 1e-12)


def true_runs(mask):
    """[(đầu, cuối)) chỉ số của các đoạn True liên tiếp."""
    edges = np.flatnonzero(np.diff(np.concatenate([[0], mask.astype(np.int8), [0]])))
    return list(zip(edges[::2], edges[1::2]))


def find_silences(db, threshold_db, min_silence):
    """Khoảng lặng [(start, end)] giây: nhỏ hơn mức giọng nói + threshold_db, dài >= min_silence."""
    if len(db) == 0:
        return []
    loud = db > np.percentile(db, 95) + threshold_db
    for a, b in true_runs(loud):
        if (b - a) * HOP < MIN_SPEECH:
            loud[a:b] = False
    return [(a * HOP, b * HOP) for a, b in true_runs(~loud) if (b - a) * HOP >= min_silence]


def quietest(db, t, before, after):
    """Thời điểm nhỏ tiếng nhất trong [t - before, t + after]."""
    lo, hi = max(0, int((t - before) / HOP)), min(len(db), int((t + after) / HOP) + 1)
    if hi <= lo:
        return t
    return (lo + int(np.argmin(db[lo:hi])) + 0.5) * HOP


def plan_keep_ranges(total, silences, fillers, db):
    """Đoạn giữ [(start, end)] giây = cả file trừ khoảng lặng (đã chừa đệm) và từ đệm."""
    cuts = []
    for start, end in silences:
        a = start + POST_ROLL if start > 0 else 0.0
        b = end - PRE_ROLL if end < total - 2 * HOP else total
        if b > a:
            cuts.append((a, b))
    for start, end in fillers:
        a, b = quietest(db, start, SNAP, 0.05), quietest(db, end, 0.05, SNAP)
        if b > a:
            cuts.append((a, b))
    keep, cursor = [], 0.0
    for a, b in sorted(cuts):
        if a > cursor:
            keep.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < total:
        keep.append((cursor, total))
    return [(a, b) for a, b in keep if b - a >= MIN_KEEP]


def to_frames(ranges, fps, frame_count):
    """Làm tròn đoạn giữ theo khung hình [(khung đầu, khung cuối)), gộp đoạn chạm nhau."""
    frames = []
    for a, b in ranges:
        first, last = int(round(a * fps)), min(frame_count, int(round(b * fps)))
        if last - first < 2:
            continue
        if frames and first <= frames[-1][1]:
            frames[-1] = (frames[-1][0], max(frames[-1][1], last))
        else:
            frames.append((first, last))
    return frames


def join_audio(audio, frame_ranges, fps, sample_rate, crossfade=CROSSFADE):
    """Nối các đoạn audio (theo mốc khung hình) bằng crossfade equal-power; độ dài = đúng tổng độ dài hình."""
    channels = audio.shape[1]
    bounds = [(int(round(a / fps * sample_rate)), int(round(b / fps * sample_rate))) for a, b in frame_ranges]
    out = np.zeros((sum(b - a for a, b in bounds), channels), np.float32)
    half = int(crossfade * sample_rate / 2)
    ramp = (np.arange(2 * half) + 0.5) / max(1, 2 * half) * (np.pi / 2)
    fade_in, fade_out = np.sin(ramp)[:, None], np.cos(ramp)[:, None]

    def take(a, b):
        piece = np.zeros((b - a, channels), np.float32)
        lo, hi = max(a, 0), min(b, len(audio))
        if hi > lo:
            piece[lo - a:hi - a] = audio[lo:hi]
        return piece

    pos = 0
    for k, (a, b) in enumerate(bounds):
        if k == 0 or half == 0:
            out[pos:pos + b - a] = take(a, b)
        else:
            prev_end = bounds[k - 1][1]
            out[pos - half:pos + half] = (take(prev_end - half, prev_end + half) * fade_out
                                          + take(a - half, a + half) * fade_in)
            out[pos + half:pos + b - a] = take(a + half, b)
        pos += b - a
    return out


def render(video_path, output_path, frame_ranges, fps, audio_raw, channels):
    """Hình: chuẩn hoá CFR rồi chọn đúng các khung cần giữ; tiếng: audio đã nối, chuẩn hoá -14 LUFS."""
    expr = "+".join(f"between(n,{a},{b - 1})" for a, b in frame_ranges)
    graph = (f"[0:v]fps={fps},select='{expr}',setpts=N/(({fps})*TB)[v];"
             f"[1:a]{LOUDNORM},aresample=48000[a]")
    if sys.platform == "win32" and len(graph) > 30000:
        raise RuntimeError("Quá nhiều đoạn cắt cho một lệnh FFmpeg trên Windows — hãy chia video thành nhiều phần.")
    run_cmd([
        "ffmpeg", "-y", "-i", video_path,
        "-f", "f32le", "-ar", str(SAMPLE_RATE), "-ac", str(channels), "-i", audio_raw,
        "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output_path,
    ])


def cut_silence(video_path, output_path, model_size="base", min_silence=0.4, threshold_db=-30.0):
    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()
    info = video_info(video_path)
    if not info["audio_channels"]:
        sys.exit("❌ Video không có tiếng — không có gì để đo khoảng lặng.")
    channels = min(2, info["audio_channels"])
    fps, total = info["fps"], info["duration"]

    print("[*] Đo độ to audio để tìm khoảng lặng...")
    audio = load_audio(video_path, SAMPLE_RATE, channels).reshape(-1, channels)
    db = loudness_db(audio.mean(axis=1), SAMPLE_RATE)
    silences = find_silences(db, threshold_db, min_silence)

    print(f"[*] Nhận diện từ đệm bằng Faster-Whisper ({model_size})...")
    fillers = [(s, e) for s, e, w in transcribe_words(video_path, model_size) if normalize_word(w) in FILLERS]

    keep = to_frames(plan_keep_ranges(total, silences, fillers, db), fps, int(total * fps))
    if not keep:
        sys.exit("❌ Không còn đoạn có tiếng nói để giữ (thử --threshold-db thấp hơn, ví dụ -40).")
    kept = sum(b - a for a, b in keep) / fps
    print(f"[+] {len(silences)} khoảng lặng, {len(fillers)} từ đệm; giữ {len(keep)} đoạn = {kept:.2f}s / {total:.2f}s.")

    with tempfile.TemporaryDirectory(prefix="ags_cut_") as tmp:
        audio_raw = Path(tmp) / "audio.f32"
        join_audio(audio, keep, fps, SAMPLE_RATE).astype("<f4").tofile(audio_raw)
        print("[*] Cắt chính xác từng khung hình, nối tiếng bằng crossfade và chuẩn hoá -14 LUFS...")
        render(video_path, output_path, keep, fps, audio_raw, channels)
    print(f"🎉 Hoàn thành video sạch: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — cắt khoảng lặng & từ đệm tự động")
    parser.add_argument("input", help="Đường dẫn video đầu vào")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra (mặc định <tên>_clean.mp4)")
    parser.add_argument("--model", default="base",
                        help="Model faster-whisper: tiny, base, small, medium, large-v3, large-v3-turbo... (mặc định base)")
    parser.add_argument("--min-silence", type=float, default=0.4, help="Khoảng lặng dài hơn mức này (giây) sẽ bị cắt")
    parser.add_argument("--threshold-db", type=float, default=-30.0,
                        help="Ngưỡng lặng, tính bằng dB so với mức giọng nói của file (mặc định -30; -20 cắt mạnh hơn)")
    args = parser.parse_args()

    inp = Path(args.input)
    out = args.out or inp.with_name(f"{inp.stem}_clean.mp4")
    cut_silence(inp, out, model_size=args.model, min_silence=args.min_silence, threshold_db=args.threshold_db)

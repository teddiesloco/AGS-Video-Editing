#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: Tự reframe video ngang (16:9, 4:3, 1:1) → dọc 9:16 bám theo khuôn mặt chính
1. Lấy mẫu 5 khung/giây (thu nhỏ bề ngang 640 px), dò mặt bằng OpenCV FaceDetectorYN với model YuNet
   (MIT, ~230 KB, lần đầu tự tải về ~/.cache/ags-video-editing/ và kiểm SHA-256).
2. Chọn mặt chính: mặt to nhất; nếu có mặt gần vị trí trước đó và đủ to thì giữ mặt đó (không nhảy qua lại 2 người).
3. Làm mượt: vùng chết 6% bề ngang khung cắt (người nhúc nhích thì khung đứng yên), lọc trung vị rồi trung bình
   trượt ~1 s để khung lia mượt khi người di chuyển thật.
4. Cắt khung 9:16 theo đường đã làm mượt (sendcmd + crop của FFmpeg), xuất 1080x1920, -14 LUFS.
Không thấy mặt nào hoặc không tải được model → cắt chính giữa và báo rõ. Video đã dọc → chỉ đổi cỡ về 1080x1920.
"""

import argparse
import hashlib
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import numpy as np

from ags_common import LOUDNORM, filter_path, run_cmd, video_info

OUT_W, OUT_H = 1080, 1920
SAMPLE_FPS = 5
SAMPLE_W = 640
DEAD_ZONE = 0.06      # tỉ lệ bề ngang khung cắt
SMOOTH_SECONDS = 1.0
MODEL_NAME = "face_detection_yunet_2023mar.onnx"
MODEL_URL = ("https://github.com/opencv/opencv_zoo/raw/f12e12798e8314f7c074a6656816c048dcc95b7a/"
             "models/face_detection_yunet/" + MODEL_NAME)
MODEL_SHA256 = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"
CACHE_DIR = Path.home() / ".cache" / "ags-video-editing"


def face_model():
    """Đường dẫn model YuNet (tải lần đầu, kiểm SHA-256)."""
    path = CACHE_DIR / MODEL_NAME
    if not path.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        print("[*] Tải model nhận diện khuôn mặt YuNet (~230 KB, chỉ lần đầu)...")
        data = urllib.request.urlopen(MODEL_URL, timeout=60).read()
        if hashlib.sha256(data).hexdigest() != MODEL_SHA256:
            raise RuntimeError("Model YuNet tải về sai mã SHA-256 — bỏ qua để an toàn.")
        path.write_bytes(data)
    return path


def sample_frames(video_path, start, duration, source_size):
    """Sinh (giây, khung BGR thu nhỏ) với SAMPLE_FPS khung/giây trong [start, start + duration)."""
    width = SAMPLE_W
    height = int(round(source_size[1] * width / source_size[0] / 2) * 2)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", str(video_path),
                             "-t", f"{duration:.3f}", "-an", "-vf", f"fps={SAMPLE_FPS},scale={width}:{height}",
                             "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    frame_bytes = width * height * 3
    k = 0
    while True:
        buf = proc.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        yield k / SAMPLE_FPS, np.frombuffer(buf, np.uint8).reshape(height, width, 3)
        k += 1
    proc.stdout.close()
    proc.wait()


def pick_face(faces, previous, frame_w):
    """Tâm ngang (tỉ lệ bề ngang) của mặt chính, hoặc None."""
    if faces is None or len(faces) == 0:
        return None
    centers = faces[:, 0] + faces[:, 2] / 2
    areas = faces[:, 2] * faces[:, 3]
    best = int(np.argmax(areas))
    if previous is not None:
        near = np.flatnonzero((np.abs(centers - previous * frame_w) < 0.1 * frame_w) & (areas >= 0.6 * areas[best]))
        if len(near):
            best = int(near[np.argmax(areas[near])])
    return float(centers[best] / frame_w)


def face_detector(frame_size):
    """FaceDetectorYN cho khung cỡ frame_size, hoặc None (thiếu mạng lần đầu, OpenCV quá cũ)."""
    try:
        import cv2

        return cv2.FaceDetectorYN.create(str(face_model()), "", frame_size, 0.7, 0.3, 50)
    except (ImportError, AttributeError, OSError, RuntimeError) as exc:
        print(f"⚠️ Không dùng được bộ dò khuôn mặt ({exc}).")
        return None


def face_track(video_path, start, duration, source_size):
    """[(giây, tâm mặt theo tỉ lệ bề ngang | None)], hoặc None nếu không dùng được bộ dò mặt."""
    track, previous, detector = [], None, None
    for t, frame in sample_frames(video_path, start, duration, source_size):
        if detector is None:
            detector = face_detector((frame.shape[1], frame.shape[0]))
            if detector is None:
                return None
        _, faces = detector.detect(frame)
        center = pick_face(faces, previous, frame.shape[1])
        previous = center if center is not None else previous
        track.append((t, center))
    return track


def smooth_path(track, crop_frac):
    """Đường tâm khung cắt [(giây, tâm theo tỉ lệ)] đã điền chỗ trống, chặn vùng chết và làm mượt."""
    times = np.array([t for t, _ in track])
    seen = [(i, c) for i, (_, c) in enumerate(track) if c is not None]
    if not seen:
        return None
    raw = np.empty(len(track))
    last = seen[0][1]
    for i, (_, c) in enumerate(track):  # mất mặt thì giữ vị trí cũ
        last = c if c is not None else last
        raw[i] = last
    pad = 2
    padded = np.pad(raw, pad, mode="edge")
    median = np.array([np.median(padded[i:i + 2 * pad + 1]) for i in range(len(raw))])
    cam, held = median[0], np.empty(len(raw))
    for i, x in enumerate(median):
        if abs(x - cam) > DEAD_ZONE * crop_frac:
            cam = x
        held[i] = cam
    width = max(1, int(SMOOTH_SECONDS * SAMPLE_FPS))
    smooth = np.convolve(np.pad(held, width, mode="edge"), np.ones(2 * width + 1) / (2 * width + 1), mode="same")
    smooth = np.clip(smooth[width:-width], crop_frac / 2, 1 - crop_frac / 2)
    return list(zip(times, smooth))


def reframe_filter(video_path, start, duration, workdir):
    """Chuỗi bộ lọc FFmpeg đưa đoạn [start, start + duration) về 1080x1920 (bám mặt nếu video ngang)."""
    info = video_info(video_path)
    width, height = info["size"]
    if width * 16 <= height * 9 + 1:
        print("[*] Video đã là dạng dọc — chỉ đổi cỡ về 1080x1920.")
        return (f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=decrease,"
                f"pad={OUT_W}:{OUT_H}:(ow-iw)/2:(oh-ih)/2,setsar=1")
    crop_w = int(round(height * 9 / 16 / 2) * 2)
    crop_frac = crop_w / width
    track = face_track(video_path, start, duration, (width, height))
    path = smooth_path(track, crop_frac) if track else None
    if path is None:
        if track is not None:
            print("⚠️ Không thấy khuôn mặt nào — dùng crop chính giữa.")
        x = (width - crop_w) // 2
        return f"crop={crop_w}:{height}:{x}:0,scale={OUT_W}:{OUT_H}:flags=lanczos,setsar=1"
    found = sum(1 for _, c in track if c is not None)
    print(f"[+] Thấy mặt ở {found}/{len(track)} khung mẫu; khung cắt {crop_w}x{height} bám theo mặt.")
    times = np.array([t for t, _ in path])
    centers = np.array([c for _, c in path])
    fps = float(info["fps"])
    frame_times = np.arange(int(np.ceil(duration * fps)) + 1) / fps
    xs = np.round(np.interp(frame_times, times, centers) * width - crop_w / 2).astype(int)
    xs = np.clip(xs - xs % 2, 0, width - crop_w)
    lines = [f"{t:.4f} crop@ags x {x};" for i, (t, x) in enumerate(zip(frame_times, xs)) if i == 0 or x != xs[i - 1]]
    commands = Path(workdir) / "reframe_cmds.txt"
    commands.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return (f"sendcmd=f='{filter_path(commands)}',crop@ags=w={crop_w}:h={height}:x={xs[0]}:y=0,"
            f"scale={OUT_W}:{OUT_H}:flags=lanczos,setsar=1")


def reframe(video_path, output_path):
    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()
    info = video_info(video_path)
    with tempfile.TemporaryDirectory(prefix="ags_reframe_") as tmp:
        print("[*] Dò khuôn mặt và tính đường lia khung...")
        vf = reframe_filter(video_path, 0.0, info["duration"], tmp)
        audio = ["-af", LOUDNORM, "-ar", "48000", "-c:a", "aac", "-b:a", "192k"] if info["audio_channels"] else ["-an"]
        print("[*] Xuất video dọc 1080x1920...")
        run_cmd(["ffmpeg", "-y", "-i", video_path, "-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                 "-pix_fmt", "yuv420p", *audio, "-movflags", "+faststart", output_path])
    print(f"🎉 Hoàn thành video dọc 9:16: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — reframe 16:9 → 9:16 bám khuôn mặt")
    parser.add_argument("input", help="Đường dẫn video ngang")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra (mặc định <tên>_9x16.mp4)")
    args = parser.parse_args()
    inp = Path(args.input)
    try:
        reframe(inp, args.out or inp.with_name(f"{inp.stem}_9x16.mp4"))
    except (RuntimeError, OSError) as exc:
        sys.exit(f"❌ {exc}")

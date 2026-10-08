#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: Chữ chìm sau người (Text Behind Person)
Tách lớp người bằng rembg (u2net_human_seg) rồi ghép sandwich 3 lớp trong FFmpeg:
video gốc -> chữ hook -> lớp người đè lên trên.
"""

import argparse
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from ags_common import display_size, fit_text, run_cmd


def create_text_banner(text, width, height, output_image_path, color="yellow"):
    """Ảnh PNG trong suốt chứa câu hook; tự co chữ để vừa 90% bề ngang, tối đa 2 dòng."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font, lines = fit_text(draw, text, "bold", max_width=width * 0.9, max_lines=2,
                           size=int(width * 0.10), min_size=int(width * 0.05))
    text_color = (255, 215, 0, 255) if color == "yellow" else (255, 255, 255, 255)
    stroke = max(3, font.size // 18)
    line_height = int(font.size * 1.15)
    y = int(height * 0.28)  # 28% từ đỉnh: ngang đầu/ngực người nói
    for line in lines:
        x = (width - draw.textlength(line, font=font)) / 2
        draw.text((x, y), line, font=font, fill=text_color, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        y += line_height
    img.save(output_image_path)


def process_text_behind_person(video_path, hook_text, output_path, duration_hook=5.0):
    import cv2
    from rembg import new_session, remove

    video_path = Path(video_path).resolve()
    output_path = Path(output_path).resolve()
    width, height = display_size(video_path)

    with tempfile.TemporaryDirectory(prefix="ags_hook_") as tmp:
        tmp = Path(tmp)
        text_png = tmp / "hook_text.png"
        create_text_banner(hook_text, width, height, text_png)

        print(f"[*] Đang tách lớp người bằng rembg cho {duration_hook}s đầu...")
        hook_clip = tmp / "hook_clip.mp4"
        run_cmd(["ffmpeg", "-y", "-i", video_path, "-t", str(duration_hook), "-an",
                 "-c:v", "libx264", "-preset", "fast", "-crf", "18", hook_clip])

        session = new_session("u2net_human_seg")
        cap = cv2.VideoCapture(str(hook_clip))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        mask_mp4 = tmp / "person_alpha.mp4"
        writer = cv2.VideoWriter(str(mask_mp4), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if (frame.shape[1], frame.shape[0]) != (width, height):
                frame = cv2.resize(frame, (width, height))
            mask = remove(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), session=session, only_mask=True)
            writer.write(cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR))
        cap.release()
        writer.release()

        print("[*] Đang ghép hiệu ứng 3 lớp trong FFmpeg...")
        # [0:v] video gốc, [1:v] ảnh chữ, [2:v] mask alpha của người
        filter_complex = (
            f"[0:v][1:v]overlay=0:0:enable='between(t,0,{duration_hook})'[bg_with_text];"
            f"[2:v]format=gray[mask];"
            f"[0:v][mask]alphamerge[person_layer];"
            f"[bg_with_text][person_layer]overlay=0:0:enable='between(t,0,{duration_hook})'[final_v]"
        )
        run_cmd([
            "ffmpeg", "-y", "-i", video_path, "-i", text_png, "-i", mask_mp4,
            "-filter_complex", filter_complex,
            "-map", "[final_v]", "-map", "0:a?",
            "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "copy", "-movflags", "+faststart", output_path,
        ])
    print(f"🎉 Hoàn thành video chữ chìm sau người: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — chữ chìm sau người (Text-Behind-Person)")
    parser.add_argument("input", help="Đường dẫn video")
    parser.add_argument("--text", "-t", required=True, help="Câu hook đặt sau lưng người nói")
    parser.add_argument("--out", "-o", default=None, help="Đường dẫn video đầu ra (mặc định <tên>_hook.mp4)")
    parser.add_argument("--duration", "-d", type=float, default=5.0, help="Thời lượng hiển thị chữ (giây)")
    args = parser.parse_args()

    inp = Path(args.input)
    out = args.out or inp.with_name(f"{inp.stem}_hook.mp4")
    process_text_behind_person(inp, args.text, out, args.duration)

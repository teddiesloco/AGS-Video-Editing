"""
AGS (Agent Space) — render trực tiếp bằng FFmpeg (không cần CapCut)
Slideshow 9:16 (mặc định 1080x1920): mỗi ảnh zoom chậm Ken Burns (+0.08%/khung, tối đa 1.15x), cắt cứng giữa các ảnh
(đặt thời lượng theo beat nhạc để cắt đúng nhịp). Có nhạc thì chuẩn hoá -14 LUFS, AAC 48 kHz.
"""

import tempfile
from pathlib import Path
from typing import List, Optional

from ags_common import LOUDNORM, run_cmd


class AgsDirectRenderer:
    def __init__(self, width: int = 1080, height: int = 1920, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps

    def render_image_slideshow(
        self,
        image_paths: List[str],
        durations: List[float],
        output_mp4: str,
        audio_path: Optional[str] = None,
    ) -> str:
        if not image_paths or len(image_paths) != len(durations):
            raise ValueError("Cần ít nhất 1 ảnh và số thời lượng phải bằng số ảnh")
        out = Path(output_mp4).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        w2, h2 = self.width * 2, self.height * 2  # phóng to trước khi zoompan để chuyển động mượt

        with tempfile.TemporaryDirectory(prefix="ags_bds_") as tmp:
            lines = []
            for idx, (img_path, dur) in enumerate(zip(image_paths, durations)):
                clip = Path(tmp) / f"slide_{idx:03d}.mp4"
                frames = max(1, round(dur * self.fps))
                vf = (
                    f"scale={w2}:{h2}:force_original_aspect_ratio=increase,crop={w2}:{h2},"
                    f"zoompan=z='min(zoom+0.0008,1.15)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                    f":s={self.width}x{self.height}:fps={self.fps},format=yuv420p"
                )
                run_cmd([
                    "ffmpeg", "-y", "-loop", "1", "-i", Path(img_path).resolve(), "-vf", vf,
                    "-frames:v", str(frames), "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                    "-pix_fmt", "yuv420p", clip,
                ])
                lines.append(f"file '{clip.as_posix()}'")
            concat_list = Path(tmp) / "concat.txt"
            concat_list.write_text("\n".join(lines) + "\n", encoding="utf-8")

            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list]
            if audio_path:
                # apad + -shortest: nhạc ngắn hơn thì đệm im lặng, dài hơn thì cắt theo hình
                cmd += ["-i", Path(audio_path).resolve(), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                        "-af", f"{LOUDNORM},apad", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest"]
            else:
                cmd += ["-c:v", "copy"]
            run_cmd(cmd + ["-movflags", "+faststart", out])
        return str(out)

"""
AGS (Agent Space) — render trực tiếp bằng FFmpeg (không cần CapCut)
Slideshow 9:16 (mặc định 1080x1920): mỗi ảnh zoom chậm Ken Burns (+0.08%/khung, tối đa 1.15x).
- Chuyển cảnh: cắt cứng (mặc định) hoặc wipe quét trái → phải (xfade) cho ảnh trước/sau; mốc chuyển vẫn đúng beat.
- Âm thanh: nhạc nền và/hoặc giọng đọc. Có cả hai thì nhạc tự nhỏ xuống khi có giọng (sidechaincompress), chuẩn hoá
  -14 LUFS, AAC 48 kHz; tiếng ngắn hơn hình được đệm im lặng, dài hơn bị cắt theo hình.
"""

import tempfile
from pathlib import Path
from typing import List, Optional

from ags_common import LOUDNORM, run_cmd

TRANSITIONS = {"cut": None, "wipe": "wiperight"}
MUSIC_BED = "loudnorm=I=-20:LRA=11:TP=-2"   # nhạc nền nằm dưới giọng ~4 LU trước khi duck
VOICE_LEVEL = "loudnorm=I=-16:LRA=11:TP=-2"
# Duck nhạc khi có giọng: tác động nhanh 150 ms, nhả chậm 450 ms để nhạc không "bơm" theo từng chữ.
DUCKING = "sidechaincompress=threshold=0.02:ratio=12:attack=150:release=450"


class AgsDirectRenderer:
    def __init__(self, width: int = 1080, height: int = 1920, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps

    def _slide(self, image: Path, seconds: float, out: Path) -> None:
        frames = max(1, round(seconds * self.fps))
        w2, h2 = self.width * 2, self.height * 2  # phóng to trước khi zoompan để chuyển động mượt
        vf = (
            f"scale={w2}:{h2}:force_original_aspect_ratio=increase,crop={w2}:{h2},"
            f"zoompan=z='min(zoom+0.0008,1.15)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":s={self.width}x{self.height}:fps={self.fps},format=yuv420p"
        )
        run_cmd(["ffmpeg", "-y", "-loop", "1", "-i", image, "-vf", vf, "-frames:v", str(frames),
                 "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", out])

    def render_image_slideshow(
        self,
        image_paths: List[str],
        durations: List[float],
        output_mp4: str,
        audio_path: Optional[str] = None,
        voice_path: Optional[str] = None,
        transition: str = "cut",
        transition_seconds: float = 0.5,
    ) -> str:
        if not image_paths or len(image_paths) != len(durations):
            raise ValueError("Cần ít nhất 1 ảnh và số thời lượng phải bằng số ảnh")
        if transition not in TRANSITIONS:
            raise ValueError(f"transition phải là một trong: {', '.join(TRANSITIONS)}")
        wipe = TRANSITIONS[transition] if len(image_paths) > 1 else None
        if wipe and transition_seconds >= min(durations):
            raise ValueError("Thời lượng wipe phải ngắn hơn cảnh ngắn nhất")
        out = Path(output_mp4).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="ags_bds_") as tmp:
            clips = []
            for idx, (img_path, dur) in enumerate(zip(image_paths, durations)):
                clip = Path(tmp) / f"slide_{idx:03d}.mp4"
                # Wipe: cảnh (trừ cảnh cuối) dài thêm đúng thời gian chuyển để tổng độ dài và mốc beat không đổi
                extra = transition_seconds if wipe and idx < len(image_paths) - 1 else 0.0
                self._slide(Path(img_path).resolve(), dur + extra, clip)
                clips.append(clip)

            if wipe:
                cmd = ["ffmpeg", "-y"]
                for clip in clips:
                    cmd += ["-i", clip]
                chain, prev, offset = [], "[0:v]", 0.0
                for k in range(1, len(clips)):
                    offset += durations[k - 1]
                    label = "[v]" if k == len(clips) - 1 else f"[x{k}]"
                    chain.append(f"{prev}[{k}:v]xfade=transition={wipe}:duration={transition_seconds}"
                                 f":offset={offset:.4f}{label}")
                    prev = label
                video = Path(tmp) / "video.mp4"
                run_cmd(cmd + ["-filter_complex", ";".join(chain), "-map", "[v]", "-c:v", "libx264",
                               "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", video])
                cmd = ["ffmpeg", "-y", "-i", video]
            else:
                concat_list = Path(tmp) / "concat.txt"
                concat_list.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
                cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list]

            sources = [Path(p).resolve() for p in (audio_path, voice_path) if p]
            for source in sources:
                cmd += ["-i", source]
            if audio_path and voice_path:
                graph = (f"[1:a]aresample=48000,aformat=channel_layouts=stereo,{MUSIC_BED}[music];"
                         f"[2:a]aresample=48000,aformat=channel_layouts=stereo,{VOICE_LEVEL},asplit=2[voice][key];"
                         f"[music][key]{DUCKING}[ducked];"
                         f"[ducked][voice]amix=inputs=2:duration=longest:normalize=0,{LOUDNORM},apad[a]")
                cmd += ["-filter_complex", graph, "-map", "0:v:0", "-map", "[a]"]
            elif sources:
                # apad + -shortest: tiếng ngắn hơn thì đệm im lặng, dài hơn thì cắt theo hình
                cmd += ["-map", "0:v:0", "-map", "1:a:0", "-af", f"{LOUDNORM},apad"]
            cmd += ["-c:v", "copy"]
            if sources:
                cmd += ["-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest"]
            run_cmd(cmd + ["-movflags", "+faststart", out])
        return str(out)

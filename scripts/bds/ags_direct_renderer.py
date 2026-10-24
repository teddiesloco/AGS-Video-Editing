"""
AGS (Agent Space) — render trực tiếp bằng FFmpeg (không cần CapCut)
Dựng 9:16 (mặc định 1080x1920) từ ảnh VÀ/HOẶC video thật: clip video giữ nguyên chuyển động (không trích khung tĩnh).
- Mỗi clip phủ kín khung (scale + crop). Video lấy `seconds` giây ĐẦU của file nguồn, bỏ tiếng gốc; nguồn ngắn hơn
  thời lượng cần thì báo lỗi (không lặp, không đứng hình). Ảnh/video nhận theo đuôi file: ảnh = IMAGE_SUFFIXES.
- Zoom: auto = ảnh Ken Burns (+0.08%/khung, tối đa 1.15x), video giữ nguyên; none = không zoom; subtle = đẩy vào nhẹ
  1.06x suốt clip (cả ảnh lẫn video).
- Chuyển cảnh: cut (cắt cứng, mặc định), wipe (quét trái → phải), dissolve (hoà mờ); mốc chuyển vẫn đúng beat.
- Màu: grade none (mặc định, giữ nguyên) | natural (tương phản/bão hoà +5%) | warm (natural + ấm nhẹ); áp cùng một công
  thức cho MỌI clip để nhiều nguồn khác nhau nhìn đồng nhất, không đẩy bão hoà.
- Âm thanh: nhạc nền và/hoặc giọng đọc. Có cả hai thì nhạc tự nhỏ xuống khi có giọng (sidechaincompress), chuẩn hoá
  -14 LUFS, AAC 48 kHz. Giọng ngắn hơn hình được đệm im lặng; giọng dài hơn hình thì BÁO LỖI (không cắt giọng);
  nhạc dài hơn hình bị cắt theo hình.
"""

import json
import math
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from ags_common import LOUDNORM, run_cmd, video_info

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
TRANSITIONS = {"cut": None, "wipe": "wiperight", "dissolve": "fade"}
ZOOMS = ("auto", "none", "subtle")
# Chỉnh màu nhẹ, cùng một công thức cho mọi clip để các nguồn khác nhau nhìn đồng nhất (không đẩy bão hoà).
# natural: tương phản +5%, bão hoà +5%; warm: thêm chút ấm ở trung tính/vùng sáng (cát, nắng) mà không ngả vàng.
GRADES = {
    "none": None,
    "natural": "eq=contrast=1.05:saturation=1.05",
    "warm": "eq=contrast=1.05:saturation=1.05,colorbalance=rm=0.02:bm=-0.02:rh=0.015:bh=-0.015",
}
KEN_BURNS = "min(zoom+0.0008,1.15)"
SUBTLE_ZOOM = 0.06          # độ phóng tối đa của zoom subtle (1.06x) ở khung cuối clip
SOURCE_SLACK = 0.05         # nguồn video được phép ngắn hơn thời lượng cần tối đa 50 ms (làm tròn khung)
VOICE_SLACK = 0.05          # giọng được phép dài hơn hình tối đa 50 ms (làm tròn khung)
MUSIC_BED = "loudnorm=I=-20:LRA=11:TP=-2"   # nhạc nền nằm dưới giọng ~4 LU trước khi duck
VOICE_LEVEL = "loudnorm=I=-16:LRA=11:TP=-2"
# Duck nhạc khi có giọng: tác động nhanh 150 ms, nhả chậm 450 ms để nhạc không "bơm" theo từng chữ.
DUCKING = "sidechaincompress=threshold=0.02:ratio=12:attack=150:release=450"


def is_image(path) -> bool:
    return Path(path).suffix.lower() in IMAGE_SUFFIXES


def _positive(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} phải là số hữu hạn > 0 (nhận {value!r})")
    return float(value)


class AgsDirectRenderer:
    def __init__(self, width: int = 1080, height: int = 1920, fps: int = 30):
        for name, value in (("width", width), ("height", height), ("fps", fps)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} phải là số nguyên dương (nhận {value!r})")
        if width % 2 or height % 2:
            raise ValueError("width và height phải là số chẵn (yuv420p)")
        if fps > 240:
            raise ValueError("fps tối đa 240")
        self.width = width
        self.height = height
        self.fps = fps

    def _source(self, path, needed: float) -> Path:
        """File ảnh/video hợp lệ; video phải có luồng hình và dài ít nhất `needed` giây."""
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise ValueError(f"Không thấy file: {path}")
        if is_image(source):
            return source
        seconds = video_info(source)["duration"]
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError(f"Video không có thời lượng hữu hạn > 0: {source.name}")
        if seconds + SOURCE_SLACK < needed:
            raise ValueError(f"Video {source.name} chỉ dài {seconds:.2f}s nhưng cần {needed:.2f}s — "
                             "giảm thời lượng clip này hoặc dùng clip dài hơn (không lặp/đứng hình)")
        return source

    @staticmethod
    def _audio_seconds(path, label: str) -> Tuple[Path, float]:
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise ValueError(f"Không thấy file {label}: {path}")
        data = json.loads(run_cmd(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                                   "-of", "json", source]).stdout)
        if not any(s.get("codec_type") == "audio" for s in data.get("streams", [])):
            raise ValueError(f"File {label} không có luồng âm thanh: {source.name}")
        try:
            seconds = float(data["format"]["duration"])
        except (KeyError, TypeError, ValueError):
            seconds = math.nan
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError(f"File {label} không có thời lượng hữu hạn > 0: {source.name}")
        return source, seconds

    def _segment(self, source: Path, seconds: float, zoom: str, out: Path, grade: str = "none") -> None:
        """Một clip đã chuẩn khung/fps, không tiếng. Video: giữ chuyển động thật, lấy từ giây 0."""
        video = not is_image(source)
        frames = max(1, round(seconds * self.fps))
        w, h = self.width, self.height
        if zoom == "none" or (zoom == "auto" and video):
            vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        else:
            expr = KEN_BURNS if zoom == "auto" else f"1+{SUBTLE_ZOOM}*on/{frames}"
            w2, h2 = w * 2, h * 2  # phóng to trước khi zoompan để chuyển động mượt
            # Ảnh: một khung vào, `frames` khung ra (d=frames). Video: mỗi khung vào ra đúng một khung (d=1).
            vf = (f"scale={w2}:{h2}:force_original_aspect_ratio=increase,crop={w2}:{h2},"
                  f"zoompan=z='{expr}':d={1 if video else frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                  f":s={w}x{h}:fps={self.fps}")
        vf = (f"fps={self.fps}," if video else "") + vf + (f",{GRADES[grade]}" if GRADES[grade] else "")
        vf += ",setsar=1,format=yuv420p"
        src = ["-i", source] if video else ["-loop", "1", "-framerate", str(self.fps), "-i", source]
        run_cmd(["ffmpeg", "-y", *src, "-an", "-vf", vf, "-frames:v", str(frames),
                 "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", out])

    def render_slideshow(
        self,
        media_paths: List[str],
        durations: List[float],
        output_mp4: str,
        audio_path: Optional[str] = None,
        voice_path: Optional[str] = None,
        transition: str = "cut",
        transition_seconds: float = 0.5,
        zoom: str = "auto",
        grade: str = "none",
    ) -> str:
        if not media_paths or len(media_paths) != len(durations):
            raise ValueError("Cần ít nhất 1 clip/ảnh và số thời lượng phải bằng số clip/ảnh")
        if transition not in TRANSITIONS:
            raise ValueError(f"transition phải là một trong: {', '.join(TRANSITIONS)}")
        if zoom not in ZOOMS:
            raise ValueError(f"zoom phải là một trong: {', '.join(ZOOMS)}")
        if grade not in GRADES:
            raise ValueError(f"grade phải là một trong: {', '.join(GRADES)}")
        durations = [_positive(d, f"Thời lượng clip {i}") for i, d in enumerate(durations, 1)]
        count = len(media_paths)
        blend = TRANSITIONS[transition] if count > 1 else None
        if blend:
            transition_seconds = _positive(transition_seconds, "transition_seconds")
            if transition_seconds >= min(durations):
                raise ValueError(f"Thời lượng {transition} ({transition_seconds}s) phải ngắn hơn cảnh ngắn nhất "
                                 f"({min(durations)}s)")
        out = Path(output_mp4).expanduser().resolve()

        # Kiểm hết đầu vào trước khi encode bất cứ thứ gì.
        # Chuyển cảnh: cảnh (trừ cảnh cuối) dài thêm đúng thời gian chuyển để tổng độ dài và mốc beat không đổi.
        extras = [transition_seconds if blend and i < count - 1 else 0.0 for i in range(count)]
        sources = [self._source(p, d + e) for p, d, e in zip(media_paths, durations, extras)]
        audio = self._audio_seconds(audio_path, "nhạc")[0] if audio_path else None
        voice, voice_seconds = self._audio_seconds(voice_path, "giọng đọc") if voice_path else (None, 0.0)
        if out in [*sources, audio, voice]:
            raise ValueError("File đầu ra trùng với một file đầu vào")
        video_seconds = sum(max(1, round(d * self.fps)) for d in durations) / self.fps
        if voice and voice_seconds > video_seconds + VOICE_SLACK:
            raise ValueError(f"Giọng đọc dài {voice_seconds:.2f}s nhưng phần hình chỉ {video_seconds:.2f}s — giọng sẽ "
                             f"bị cắt cụt. Kéo tổng thời lượng clip lên ≥ {voice_seconds:.2f}s "
                             f"(ví dụ --seconds ≥ {voice_seconds / count:.2f} cho {count} clip) hoặc thêm clip.")
        out.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="ags_bds_") as tmp:
            clips = []
            for idx, (source, dur, extra) in enumerate(zip(sources, durations, extras)):
                clip = Path(tmp) / f"slide_{idx:03d}.mp4"
                self._segment(source, dur + extra, zoom, clip, grade)
                clips.append(clip)

            if blend:
                cmd = ["ffmpeg", "-y"]
                for clip in clips:
                    cmd += ["-i", clip]
                chain, prev, offset = [], "[0:v]", 0.0
                for k in range(1, len(clips)):
                    offset += durations[k - 1]
                    label = "[v]" if k == len(clips) - 1 else f"[x{k}]"
                    chain.append(f"{prev}[{k}:v]xfade=transition={blend}:duration={transition_seconds}"
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

            tracks = [p for p in (audio, voice) if p]
            for track in tracks:
                cmd += ["-i", track]
            if audio and voice:
                graph = (f"[1:a]aresample=48000,aformat=channel_layouts=stereo,{MUSIC_BED}[music];"
                         f"[2:a]aresample=48000,aformat=channel_layouts=stereo,{VOICE_LEVEL},asplit=2[voice][key];"
                         f"[music][key]{DUCKING}[ducked];"
                         f"[ducked][voice]amix=inputs=2:duration=longest:normalize=0,{LOUDNORM},apad[a]")
                cmd += ["-filter_complex", graph, "-map", "0:v:0", "-map", "[a]"]
            elif tracks:
                # apad + -shortest: tiếng ngắn hơn thì đệm im lặng, nhạc dài hơn thì cắt theo hình
                cmd += ["-map", "0:v:0", "-map", "1:a:0", "-af", f"{LOUDNORM},apad"]
            cmd += ["-c:v", "copy"]
            if tracks:
                # -t = đúng độ dài hình (vd 30.000 s): AAC không kéo dài thêm vài chục ms so với hình
                cmd += ["-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest", "-t", f"{video_seconds:.3f}"]
            run_cmd(cmd + ["-movflags", "+faststart", out])
        return str(out)

#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing — MCP server (stdio).

Mỗi tool gọi đúng script trong repo bằng chính Python đang chạy server và trả về:
  output (đường dẫn kết quả), exit_code, stderr_tail, stdout_tail.
Chạy: python mcp/ags_mcp_server.py   (cần: pip install -r requirements.txt -r requirements-mcp.txt)
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
HARNESS = ROOT / "harness"
TAIL = 2000

mcp = FastMCP("ags-video-editing")


def _run(args: List[str], output: str) -> dict:
    proc = subprocess.run([sys.executable, *[str(a) for a in args]], cwd=str(ROOT), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    return {"output": output, "exit_code": proc.returncode,
            "stderr_tail": proc.stderr[-TAIL:], "stdout_tail": proc.stdout[-TAIL:]}


def _default_out(input_path: str, suffix: str) -> str:
    src = Path(input_path).expanduser().resolve()
    return str(src.with_name(f"{src.stem}_{suffix}.mp4"))


@mcp.tool()
def cut_silence(input_path: str, output_path: str = "", model: str = "base", min_silence: float = 0.4) -> dict:
    """Cắt khoảng lặng dài hơn min_silence giây và từ đệm ('ờ, à, ừm') khỏi video nói chuyện."""
    out = output_path or _default_out(input_path, "clean")
    return _run([SCRIPTS / "ags_cut_silence.py", input_path, "--out", out, "--model", model,
                 "--min-silence", min_silence], out)


@mcp.tool()
def text_behind_person(input_path: str, text: str, output_path: str = "", duration: float = 5.0) -> dict:
    """Đặt câu hook chìm sau lưng người nói trong `duration` giây đầu (tách người bằng rembg)."""
    out = output_path or _default_out(input_path, "hook")
    return _run([SCRIPTS / "ags_text_behind_person.py", input_path, "--text", text, "--out", out,
                 "--duration", duration], out)


@mcp.tool()
def editorial_sub(input_path: str, output_path: str = "", model: str = "base") -> dict:
    """Đốt phụ đề nét Serif phong cách tạp chí và chuẩn hoá âm lượng -14 LUFS."""
    out = output_path or _default_out(input_path, "editorial")
    return _run([SCRIPTS / "ags_editorial_sub.py", input_path, "--out", out, "--model", model], out)


@mcp.tool()
def voice_to_kinetic(audio_path: str, output_path: str = "", model: str = "base") -> dict:
    """Biến file ghi âm thành video 1080x1920 chữ 2D bật nảy theo từng cụm lời nói."""
    out = output_path or _default_out(audio_path, "kinetic")
    return _run([SCRIPTS / "ags_voice_to_kinetic.py", audio_path, "--out", out, "--model", model], out)


@mcp.tool()
def voice_to_doodle(audio_path: str, output_path: str = "", model: str = "base") -> dict:
    """Biến file ghi âm thành video 1080x1920 người que nét chì trên giấy kraft kèm phụ đề."""
    out = output_path or _default_out(audio_path, "doodle")
    return _run([SCRIPTS / "ags_voice_to_doodle.py", audio_path, "--out", out, "--model", model], out)


@mcp.tool()
def bds_draft(name: str, clips: List[str], output_dir: str = "", capcut: bool = False, seconds: float = 0.0,
              bpm: float = 0.0, beat_step: int = 4, title: str = "", music: str = "") -> dict:
    """Sinh draft CapCut (thử nghiệm) cho video BĐS. Ghi vào <output_dir>/<name>, hoặc thẳng vào thư mục
    draft của CapCut desktop khi capcut=True. Không ghi đè thư mục đã có."""
    if not capcut and not output_dir:
        return {"output": "", "exit_code": 2, "stderr_tail": "Cần output_dir hoặc capcut=True", "stdout_tail": ""}
    args = [SCRIPTS / "ags_bds_cli.py", "draft", "--name", name, "--clips", *clips]
    args += ["--capcut"] if capcut else ["--out", output_dir]
    if seconds:
        args += ["--seconds", seconds]
    if bpm:
        args += ["--bpm", bpm, "--beat-step", beat_step]
    if title:
        args += ["--title", title]
    if music:
        args += ["--music", music]
    result = _run(args, "")
    if result["exit_code"] == 0:
        result["output"] = json.loads(result["stdout_tail"].strip().splitlines()[-1])["draft_dir"]
    return result


@mcp.tool()
def bds_render(images: List[str], output_path: str, seconds: float = 2.0, bpm: float = 0.0,
               beat_step: int = 4, music: str = "") -> dict:
    """Render slideshow MP4 9:16 (Ken Burns) từ ảnh BĐS bằng FFmpeg; có nhạc thì chuẩn hoá -14 LUFS."""
    args = [SCRIPTS / "ags_bds_cli.py", "render", "--images", *images, "--out", output_path, "--seconds", seconds]
    if bpm:
        args += ["--bpm", bpm, "--beat-step", beat_step]
    if music:
        args += ["--music", music]
    return _run(args, output_path)


@mcp.tool()
def anti_slop_guard(video_path: str) -> dict:
    """Kiểm định video trước khi bàn giao. exit_code 0 = đạt, 2 = có cảnh báo, 1 = lỗi nghiêm trọng."""
    return _run([HARNESS / "ags_anti_slop_guard.py", video_path], video_path)


if __name__ == "__main__":
    mcp.run()

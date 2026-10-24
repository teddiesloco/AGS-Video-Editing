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
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
HARNESS = ROOT / "harness"
TAIL = 2000
sys.path.insert(0, str(SCRIPTS))

from ags_client_license import assert_client_licensed  # noqa: E402

mcp = FastMCP("ags-video-editing")


def _run(args: List[object], output: str) -> dict:
    assert_client_licensed()
    proc = subprocess.run([sys.executable, *[str(a) for a in args]], cwd=str(ROOT), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    return {"output": output, "exit_code": proc.returncode,
            "stderr_tail": proc.stderr[-TAIL:], "stdout_tail": proc.stdout[-TAIL:]}


def _last_json(result: dict) -> dict:
    return json.loads(result["stdout_tail"].strip().splitlines()[-1])


def _default_out(input_path: str, suffix: str, ext: str = ".mp4") -> str:
    src = Path(input_path).expanduser().resolve()
    return str(src.with_name(f"{src.stem}_{suffix}{ext}"))


@mcp.tool()
def cut_silence(input_path: str, output_path: str = "", model: str = "base", min_silence: float = 0.4,
                threshold_db: float = -30.0) -> dict:
    """Cắt khoảng lặng (đo độ to, dài hơn min_silence giây, nhỏ hơn mức giọng nói threshold_db dB) và từ đệm
    ('ờ, à, ừm') khỏi video nói chuyện; cắt chính xác từng khung, crossfade tiếng, -14 LUFS.
    model: tên model faster-whisper (base, small, large-v3-turbo...)."""
    out = output_path or _default_out(input_path, "clean")
    return _run([SCRIPTS / "ags_cut_silence.py", input_path, "--out", out, "--model", model,
                  "--min-silence", min_silence, "--threshold-db", threshold_db], out)


@mcp.tool()
def text_behind_person(input_path: str, text: str, output_path: str = "", duration: float = 5.0) -> dict:
    """Đặt câu hook chìm sau lưng người nói trong `duration` giây đầu (tách người bằng rembg); hook hiện ngay khung 0."""
    out = output_path or _default_out(input_path, "hook")
    return _run([SCRIPTS / "ags_text_behind_person.py", input_path, "--text", text, "--out", out,
                 "--duration", duration], out)


@mcp.tool()
def editorial_sub(input_path: str, output_path: str = "", model: str = "base", style: str = "clean",
                  highlight_color: str = "", keywords: str = "", script_path: str = "") -> dict:
    """Đốt phụ đề và chuẩn hoá -14 LUFS. style: 'clean' (Sans đậm trắng, bóng mềm, từ khoá vàng cát; mặc định),
    'editorial' (Serif tạp chí) hoặc 'karaoke' (từ đang nói đổi màu).
    keywords: từ/cụm từ khoá cách nhau bằng dấu phẩy, tô highlight_color (#RRGGBB; để trống = màu mặc định của kiểu).
    script_path: file UTF-8 chứa đúng
    lời đọc — chữ hiện theo script (không theo Whisper nghe sai), Whisper chỉ cho mốc thời gian. Chữ tối đa 2 dòng, đúng cỡ."""
    out = output_path or _default_out(input_path, style)
    args = [SCRIPTS / "ags_editorial_sub.py", input_path, "--out", out, "--model", model, "--style", style,
            "--keywords", keywords]
    if highlight_color:
        args += ["--highlight-color", highlight_color]
    if script_path:
        args += ["--script", script_path]
    return _run(args, out)


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
def reframe(input_path: str, output_path: str = "") -> dict:
    """Chuyển video ngang (16:9...) thành dọc 1080x1920, khung cắt bám theo khuôn mặt chính (không thấy mặt: cắt giữa)."""
    out = output_path or _default_out(input_path, "9x16")
    return _run([SCRIPTS / "ags_reframe.py", input_path, "--out", out], out)


@mcp.tool()
def clip_shorts_transcript(input_path: str, output_path: str = "", model: str = "base") -> dict:
    """Bước 1 làm short: bóc băng video dài ra JSON (câu + từng từ có mốc giây). Đọc JSON rồi chọn đoạn theo
    skills/ags-clip-shorts/SKILL.md, sau đó gọi clip_shorts_cut."""
    out = output_path or _default_out(input_path, "transcript", ".json")
    return _run([SCRIPTS / "ags_clip_shorts.py", "transcript", input_path, "--out", out, "--model", model], out)


@mcp.tool()
def clip_shorts_cut(input_path: str, transcript_path: str, ranges: List[Dict[str, object]], output_dir: str = "",
                    style: str = "karaoke", highlight_color: str = "", keywords: str = "",
                    reframe: bool = True) -> dict:
    """Bước 2 làm short: ranges = [{"start": giây, "end": giây, "hook": "chữ hook (tuỳ chọn)", "name": "tên file"}].
    Mỗi đoạn (1–180 s) thành 1 short 1080x1920: bám mặt, phụ đề (style karaoke | clean | editorial | none), hook hiện ngay
    khung 0, -14 LUFS. output trả về thư mục; stdout_tail có JSON danh sách file."""
    out_dir = output_dir or str(Path(input_path).expanduser().resolve().with_name(f"{Path(input_path).stem}_shorts"))
    with tempfile.TemporaryDirectory(prefix="ags_mcp_") as tmp:
        ranges_file = Path(tmp) / "ranges.json"
        ranges_file.write_text(json.dumps(ranges, ensure_ascii=False), encoding="utf-8")
        args = [SCRIPTS / "ags_clip_shorts.py", "cut", input_path, "--transcript", transcript_path,
                "--ranges", ranges_file, "--out-dir", out_dir, "--style", style, "--keywords", keywords]
        if highlight_color:
            args += ["--highlight-color", highlight_color]
        return _run(args + ([] if reframe else ["--no-reframe"]), out_dir)


@mcp.tool()
def bds_draft(name: str, clips: List[str], output_dir: str = "", capcut: bool = False, seconds: float = 0.0,
              bpm: float = 0.0, beat_step: int = 4, auto_beat: bool = False, title: str = "", music: str = "") -> dict:
    """Sinh draft CapCut (thử nghiệm) cho video BĐS. Ghi vào <output_dir>/<name>, hoặc thẳng vào thư mục
    draft của CapCut desktop khi capcut=True. Không ghi đè thư mục đã có. auto_beat=True: dò beat từ music."""
    if not capcut and not output_dir:
        return {"output": "", "exit_code": 2, "stderr_tail": "Cần output_dir hoặc capcut=True", "stdout_tail": ""}
    args = [SCRIPTS / "ags_bds_cli.py", "draft", "--name", name, "--clips", *clips]
    args += ["--capcut"] if capcut else ["--out", output_dir]
    if seconds:
        args += ["--seconds", seconds]
    if bpm:
        args += ["--bpm", bpm]
    if auto_beat:
        args += ["--auto-beat"]
    args += ["--beat-step", beat_step]
    if title:
        args += ["--title", title]
    if music:
        args += ["--music", music]
    result = _run(args, "")
    if result["exit_code"] == 0:
        result["output"] = _last_json(result)["draft_dir"]
    return result


@mcp.tool()
def bds_render(output_path: str, clips: Optional[List[str]] = None, images: Optional[List[str]] = None,
               seconds: float = 2.0, bpm: float = 0.0, beat_step: int = 4, auto_beat: bool = False,
               music: str = "", voice: str = "", transition: str = "cut", transition_seconds: float = 0.5,
               zoom: str = "auto", grade: str = "none") -> dict:
    """Render MP4 9:16 từ video thật và/hoặc ảnh (đưa đúng một trong `clips` / `images`, nhận cả hai loại file; video giữ
    chuyển động thật, lấy `seconds` giây đầu mỗi file, bỏ tiếng gốc, file ngắn hơn thì báo lỗi). auto_beat=True: dò
    BPM/beat từ music và cắt đúng beat. voice: giọng đọc (có cả music thì nhạc tự nhỏ khi có giọng; giọng dài hơn hình →
    báo lỗi, không cắt giọng). transition: 'cut', 'wipe' (quét trái → phải) hoặc 'dissolve' (hoà mờ). zoom: 'auto'
    (ảnh Ken Burns, video giữ nguyên), 'none', 'subtle' (đẩy vào nhẹ 1.06x). grade: 'none', 'natural' hoặc 'warm' (chỉnh
    màu nhẹ, cùng công thức cho mọi clip). stdout cuối là JSON có `cut_times` để đặt SFX."""
    if bool(clips) == bool(images):
        return {"output": "", "exit_code": 2, "stdout_tail": "",
                "stderr_tail": "Truyền đúng một trong `clips` hoặc `images` (danh sách không rỗng)"}
    args = [SCRIPTS / "ags_bds_cli.py", "render", "--clips", *(clips or images), "--out", output_path,
            "--seconds", seconds, "--beat-step", beat_step, "--transition", transition,
            "--transition-seconds", transition_seconds, "--zoom", zoom, "--grade", grade]
    if bpm:
        args += ["--bpm", bpm]
    if auto_beat:
        args += ["--auto-beat"]
    if music:
        args += ["--music", music]
    if voice:
        args += ["--voice", voice]
    return _run(args, output_path)


@mcp.tool()
def anti_slop_guard(video_path: str, contact_sheet: str = "", frames: int = 12) -> dict:
    """Kiểm định video trước khi bàn giao. exit_code 0 = đạt, 2 = có cảnh báo, 1 = lỗi nghiêm trọng.
    contact_sheet: đường dẫn ảnh .jpg để xuất lưới `frames` khung (khung 0 + rải đều) — mở ảnh ra soát bằng mắt."""
    args = [HARNESS / "ags_anti_slop_guard.py", video_path, "--frames", frames]
    if contact_sheet:
        args += ["--contact-sheet", contact_sheet]
    return _run(args, contact_sheet or video_path)


@mcp.tool()
def tts_voices(engine: str) -> dict:
    """List bundled voices for vieneu, gemini, synth, or zerotts. First use downloads local model weights."""
    return _run([SCRIPTS / "ags_tts.py", "voices", "--engine", engine], "")


@mcp.tool()
def tts_synthesize(engine: str, text_path: str, output_path: str, voice: str = "") -> dict:
    """UTF-8 Vietnamese text (auto-normalizes 99k, 1,9tr, 40%, 24/7) to a new WAV. ZeroTTS voices: evaluation/demo only."""
    assert_client_licensed()
    args = [SCRIPTS / "ags_tts.py", "synthesize", "--engine", engine,
            "--text-file", text_path, "--out", output_path]
    if voice:
        args += ["--voice", voice]
    return _run(args, output_path)


@mcp.tool()
def sfx_list() -> dict:
    """List bundled Kenney CC0 sound effects."""
    return _run([SCRIPTS / "ags_sfx.py", "list"], "")


@mcp.tool()
def sfx_mix(input_path: str, events: List[dict], output_path: str) -> dict:
    """Mix effects [{file, time, gain}] into video. file: bundled filename (see sfx_list) or absolute path; gain 0–1."""
    for event in events:
        name = event.get("file") if isinstance(event, dict) else None
        # A relative path would resolve against the server's repo cwd, not the caller's: refuse the ambiguity.
        if isinstance(name, str) and not Path(name).expanduser().is_absolute() and Path(name).name != name:
            return {"output": "", "exit_code": 2, "stdout_tail": "",
                    "stderr_tail": f"Custom effect must be an absolute path or a bundled filename: {name}"}
    with tempfile.TemporaryDirectory(prefix="ags_sfx_") as tmp:
        manifest = Path(tmp) / "events.json"
        manifest.write_text(json.dumps(events, ensure_ascii=False), encoding="utf-8")
        return _run([SCRIPTS / "ags_sfx.py", "mix", input_path, "--events", manifest,
                     "--out", output_path], output_path)


if __name__ == "__main__":
    mcp.run()

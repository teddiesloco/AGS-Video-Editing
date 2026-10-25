#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing — MCP server (stdio).

Mỗi tool gọi đúng script trong repo bằng chính Python đang chạy server và trả về:
  output (đường dẫn kết quả), exit_code, stderr_tail, stdout_tail.
Tool AGS Video Studio `ags_studio_*` bọc `ags_studio.py` / `ags_vi_script.py --json` và trả exit_code, result (JSON của
lệnh), stderr_tail, stdout_tail.
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


def _exec(args: List[object]) -> subprocess.CompletedProcess:
    assert_client_licensed()
    return subprocess.run([sys.executable, *[str(a) for a in args]], cwd=str(ROOT), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def _run(args: List[object], output: str) -> dict:
    proc = _exec(args)
    return {"output": output, "exit_code": proc.returncode,
            "stderr_tail": proc.stderr[-TAIL:], "stdout_tail": proc.stdout[-TAIL:]}


def _studio(script: str, *args: object) -> dict:
    """AGS Video Studio: chạy `scripts/<script> ... --json`; `result` = JSON lệnh in ra (None nếu stdout không phải JSON).
    ags_studio.py: exit 0 đạt · 2 lỗi nghiệp vụ (result.error.code/message) · 1 lỗi giấy phép/hệ thống.
    ags_vi_script.py: exit 0 đạt · 1 chưa đạt (result.errors[]) · 2 sai tham số."""
    proc = _exec([SCRIPTS / script, *args, "--json"])
    try:
        result = json.loads(proc.stdout)
    except ValueError:
        result = None
    return {"exit_code": proc.returncode, "result": result,
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
def blender_3d_render(output_path: str, scene_preset: str = "auto", seconds: float = 6.0, title: str = "",
                      mode: str = "auto") -> dict:
    """Dựng cảnh 3D 1080x1920 30fps bằng Blender chạy ngầm. scene_preset: 'blender_3d_bds' (lô đất nhô cao + cột mốc
    phát sáng + camera bay quỹ đạo), 'blender_3d_isometric' (01 INTAKE -> 02 AI CORE -> 03 OUTCOME), 'blender_3d_product'
    (bục xoay 360°) hoặc 'auto' (chọn theo title). mode='auto': máy chưa có Blender thì tự dựng bằng Canvas 30fps
    (render.engine='canvas', kèm fallback_reason); mode='blender': báo lỗi nếu thiếu Blender."""
    script = SCRIPTS / "ags_blender_3d.py"
    if not script.is_file():
        return {"output": output_path, "exit_code": 1, "stdout_tail": "",
                "stderr_tail": "BLENDER_ADDON_MISSING — add-on Blender 3D là tuỳ chọn, chưa cài: giải nén "
                               "ags-blender-3d-addon.zip vào thư mục skill (có sẵn scripts/) rồi gọi lại."}
    result = _run([script, "--preset", scene_preset, "--out", output_path,
                   "--seconds", seconds, "--title", title, "--mode", mode], output_path)
    if result["exit_code"] == 0:
        result["render"] = _last_json(result)
    return result


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


@mcp.tool()
def ags_studio_menu() -> dict:
    """AGS Video Studio — bảng chọn món (ngành/ý tưởng → câu mẫu → mẫu video) của bản cài, nhãn lời thường từ config/menu.json."""
    return _studio("ags_studio.py", "menu")


@mcp.tool()
def ags_studio_intake(request: str = "", job_dir: str = "", topic: str = "", preset: str = "", voice: str = "",
                      images: str = "") -> dict:
    """AGS Video Studio bước 1 — hỏi ngược đúng 3 câu (ngành/chủ đề → mẫu → giọng), bỏ câu khách đã nói. Lần đầu:
    request = câu nguyên văn của khách (job_dir trống → tạo việc mới, result.job_dir). Các lần sau: job_dir + câu trả lời
    vừa hỏi (topic | preset: business-thinking-60s/jetlag-vi/bds/editorial/isometric-3d | voice: synth/vieneu/gemini).
    images: 'ai' (ảnh AI, có phí) | 'free' — chỉ khi khách tự nhắc. result.next_question {key,text,choices}; null = đủ."""
    args: List[object] = ["intake"]
    for flag, value in (("--request", request), ("--job-dir", job_dir), ("--topic", topic), ("--preset", preset),
                        ("--voice", voice), ("--images", images)):
        if value:
            args += [flag, value]
    return _studio("ags_studio.py", *args)


@mcp.tool()
def ags_studio_quote(job_dir: str, script_path: str = "", hook_text: str = "",
                     claims: Optional[List[Dict[str, str]]] = None, source_url: str = "", source_text: str = "",
                     image_prompts: Optional[List[str]] = None) -> dict:
    """AGS Video Studio bước 3 — chi phí bằng VND (result.quote.total_vnd), đọc cho khách rồi CHỜ khách nói 'chạy'.
    script_path = kịch bản agent viết (câu đầu = câu mở đọc), hook_text = chữ mở trên hình ≤ 8 từ, claims =
    [{"text", "claim_source": "khach-nhap"|"tai-lieu:<tên>"|"vi-du"}], source_url/source_text = nguồn tham khảo để chặn chép
    quá 8 từ, image_prompts = 1 chủ thể ảnh AI (tiếng Anh) cho mỗi câu, đúng thứ tự câu. Kịch bản chưa đạt →
    E-ags-video-studio-10x-004/005/012/013. Không có script_path → báo giá ước tính."""
    with tempfile.TemporaryDirectory(prefix="ags_studio_") as tmp:
        args: List[object] = ["quote", "--job-dir", job_dir]
        for flag, value in (("--script-file", script_path), ("--hook-text", hook_text), ("--source-url", source_url)):
            if value:
                args += [flag, value]
        files = (("--claims-file", "claims.json", json.dumps(claims, ensure_ascii=False) if claims else ""),
                 ("--source-file", "source.txt", source_text),
                 ("--image-prompts-file", "image-prompts.json",
                  json.dumps(image_prompts, ensure_ascii=False) if image_prompts else ""))
        for flag, name, content in files:
            if content:
                (Path(tmp) / name).write_text(content, encoding="utf-8")
                args += [flag, Path(tmp) / name]
        return _studio("ags_studio.py", *args)


@mcp.tool()
def ags_studio_run(job_dir: str, confirmed: bool = False) -> dict:
    """AGS Video Studio bước 4 — dựng mp4 9:16 + contact-sheet.jpg. confirmed=true CHỈ khi khách đã nói 'chạy' sau khi xem
    chi phí; confirmed=false → E-ags-video-studio-10x-003, không dựng, không gọi dịch vụ ngoài."""
    return _studio("ags_studio.py", "run", "--job-dir", job_dir, *(["--confirmed"] if confirmed else []))


@mcp.tool()
def ags_studio_revise(job_dir: str, say: str, confirmed: bool = False) -> dict:
    """AGS Video Studio bước 6 — sửa bằng lời thường: say = câu nguyên văn của khách ('đổi sub sang vàng'). Câu không rõ →
    E-ags-video-studio-10x-010 kèm gợi ý. Sửa phát sinh phí → báo chi phí, khách nói 'chạy' rồi gọi lại với confirmed=true."""
    return _studio("ags_studio.py", "revise", "--job-dir", job_dir, "--say", say, *(["--confirmed"] if confirmed else []))


@mcp.tool()
def ags_studio_variants(job_dir: str, hooks: List[str], count: int = 3, confirmed: bool = False) -> dict:
    """AGS Video Studio — 'làm 3 bản thử': hooks = 3 câu mở thuộc 3 loại khác nhau; các mp4 chỉ khác 3 giây đầu. Báo chi
    phí trước; confirmed=true chỉ sau khi khách nói 'chạy'."""
    return _studio("ags_studio.py", "variants", "--job-dir", job_dir, "--count", count,
                   *[part for hook in hooks for part in ("--hook", hook)], *(["--confirmed"] if confirmed else []))


@mcp.tool()
def ags_studio_proof(spec_path: str, out_dir: str, confirmed: bool = False) -> dict:
    """AGS Video Studio — bằng chứng render của người bán (mp4 + contact sheet + proof-manifest.json). Không chạy cho khách;
    confirmed=true khi người bán đã đồng ý chi phí dịch vụ ngoài."""
    return _studio("ags_studio.py", "proof", "--spec", spec_path, "--out-dir", out_dir,
                   *(["--confirmed"] if confirmed else []))


@mcp.tool()
def ags_studio_validate_script(script: str, duration_sec: float, source_text: str = "") -> dict:
    """Kiểm kịch bản Việt hoá (tất định, không mạng): câu ≤ 16 từ, nhịp 2,4 từ/giây ±10%, không dịch máy, không chép
    nguồn quá 8 từ (source_text = văn bản tham khảo nếu có). result.ok=false → viết lại đúng các câu trong result.errors[]."""
    with tempfile.TemporaryDirectory(prefix="ags_studio_") as tmp:
        args: List[object] = ["validate", "--script", script, "--duration", duration_sec]
        if source_text:
            source = Path(tmp) / "source.txt"
            source.write_text(source_text, encoding="utf-8")
            args += ["--source-file", source]
        return _studio("ags_vi_script.py", *args)


@mcp.tool()
def ags_studio_hook(spoken: str = "", on_screen: str = "") -> dict:
    """Chấm câu mở đầu: lời nói ≤ 14 từ, chữ trên hình ≤ 8 từ, có số/câu hỏi/nghịch lý/cảnh báo/trước–sau/POV, không mở
    bằng lời chào. Chưa đạt → E-ags-video-studio-10x-012. spoken trống → trả thư viện 8 loại câu mở để agent viết."""
    args: List[object] = ["hook"] + (["--spoken", spoken] if spoken else []) + (["--on-screen", on_screen] if on_screen else [])
    return _studio("ags_vi_script.py", *args)


@mcp.tool()
def ags_studio_claims(script: str, claims: List[Dict[str, str]]) -> dict:
    """Không bịa kết quả của khách: claims = [{"text": "50 triệu", "claim_source": "khach-nhap" | "tai-lieu:<tên>" | "vi-du"}].
    Số kết quả cá nhân không có nguồn → E-ags-video-studio-10x-013; 'vi-du' → nhãn "ví dụ" trên video."""
    with tempfile.TemporaryDirectory(prefix="ags_studio_") as tmp:
        claims_file = Path(tmp) / "claims.json"
        claims_file.write_text(json.dumps(claims, ensure_ascii=False), encoding="utf-8")
        return _studio("ags_vi_script.py", "claims", "--script", script, "--claims-file", claims_file)


@mcp.tool()
def ags_studio_profile(samples: List[str]) -> dict:
    """Hiệu chỉnh theo 1–5 mẫu thật của khách (link http(s) công khai hoặc đoạn văn): chỉ đo số từ/giây, độ dài câu, loại câu
    mở, số ý — không tải hay dùng lại hình/tiếng gốc."""
    return _studio("ags_vi_script.py", "profile", *[part for sample in samples for part in ("--sample", sample)])


@mcp.tool()
def marketing_editor_inspect(source: str, transcript_path: str, model: str = "base") -> dict:
    """Đọc media cục bộ và bóc băng từng từ để agent chọn ý marketing từ nguồn thật.
    Không upload hay gọi API trả phí; model Whisper cần có trên máy để chạy offline."""
    assert_client_licensed()
    from ags_marketing_editor import inspect_source

    return inspect_source(source, transcript_path, model)


@mcp.tool()
def marketing_editor_validate(plan_path: str) -> dict:
    """Kiểm plan JSON do agent viết: nguồn, mốc từ, persona, provenance và hash; không cấp duyệt.
    Kết quả kỹ thuật không chứng minh ý nghĩa, chất lượng hình hay tương thích host."""
    assert_client_licensed()
    from ags_marketing_editor import validate_plan

    return validate_plan(plan_path)


@mcp.tool()
def marketing_editor_approve(plan_path: str, stage: str, reason: str) -> dict:
    """Ghi sự đồng ý RÕ RÀNG của chủ cho plan hoặc draft, reason chép lời duyệt và ngữ cảnh.
    Chỉ gọi sau khi chủ xem đúng plan/draft hiện tại; draft phải được xem/nghe trước khi duyệt xuất final.
    Bản ghi cục bộ không xác thực danh tính người duyệt. Thay nội dung cần duyệt lại."""
    assert_client_licensed()
    from ags_marketing_editor import approve_plan

    return approve_plan(plan_path, stage, reason)


@mcp.tool()
def marketing_editor_render(plan_path: str = "", output_dir: str = "", stage: str = "draft",
                            plan_paths: Optional[List[str]] = None) -> dict:
    """Dựng draft/final cục bộ sau duyệt. Chọn plan_path cho một job HOẶC plan_paths cho batch.
    Batch dùng cùng engine, duyệt riêng từng plan, lỗi một job không chặn job sau.
    output_dir bắt buộc; không ghi đè output cũ hay nguồn; không upload/xuất bản lên mạng."""
    assert_client_licensed()
    from ags_marketing_editor import render_batch, render_plan

    if not output_dir.strip():
        raise ValueError("output_dir is required; choose a new local output directory")
    if plan_paths is not None:
        if plan_path or not plan_paths:
            raise ValueError("Provide either plan_path or a nonempty plan_paths batch, not both")
        return render_batch(plan_paths, output_dir, stage)
    if not plan_path.strip():
        raise ValueError("Provide plan_path or a nonempty plan_paths batch")
    return render_plan(plan_path, output_dir, stage)


if __name__ == "__main__":
    mcp.run()

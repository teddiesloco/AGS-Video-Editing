#!/usr/bin/env python3
"""
AGS Video Studio — lõi cho khách không biết kỹ thuật (FR-ags-video-studio-10x-004/005/014/015/016/023).
Trạng thái mỗi video nằm trong <thư mục job>/studio-job.json (khoá cấp 1 theo docs/ags-video-studio-10x/api/api-map.md).

  intake   hỏi ngược đúng 3 câu (chủ đề, kiểu video, giọng đọc); câu đã nói trong yêu cầu đầu thì bỏ qua
  quote    báo chi phí (config/pricing.json) — nhận kịch bản do agent viết và kiểm bằng ags_vi_script
  run      dựng video thật; bắt buộc --confirmed sau khi khách nói "chạy"
  revise   sửa bằng lời thường, chỉ các tham số trong whitelist BR-007
  variants 3 bản thử chỉ khác chữ hook ở 3 giây đầu (dùng lại hình, giọng, phụ đề)
  proof    dựng bộ bằng chứng ≥ 4 mẫu + proof-manifest.json
  menu     bảng chọn món (config/menu.json)
Mọi lệnh có --json. Lỗi: exit 2 + {"ok": false, "error": {"code": "E-ags-video-studio-10x-NNN", "message": ...}}.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
CONFIG_DIR = ROOT / "config"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ags_client_license import assert_client_licensed  # noqa: E402

JOB_FILE = "studio-job.json"
CONTACT_SHEET = "contact-sheet.jpg"
QUESTION_ORDER = ("topic", "preset", "voice")
VOICES = {
    "synth": "Giọng máy miễn phí (có sẵn trên máy)",
    "vieneu": "Giọng Việt miễn phí VieNeu (lần đầu tải mô hình)",
    "gemini": "Giọng Google AI – Gemini (cần khoá Google AI, có phí)",
}
VOICE_ALIASES = {
    "gemini": ("gemini", "google"),
    "vieneu": ("vieneu",),
    "synth": ("giọng miễn phí", "giọng máy", "miễn phí", "synth"),
}
REVISE_SUGGESTIONS = ["đổi màu sub sang vàng", "đọc nhanh hơn", "đổi cảnh 2"]
COLOR_WORDS = {"vàng": "#FFD166", "xanh lá": "#A8FF3E", "xanh": "#A8FF3E", "đỏ": "#FF5A5F", "trắng": "#FFFFFF"}
RETENTION_GUIDE = [
    {"giu_chan_3s": "< 40%", "y_nghia": "cần sửa lớn"},
    {"giu_chan_3s": "40–55%", "y_nghia": "trung bình"},
    {"giu_chan_3s": "55–70%", "y_nghia": "tốt"},
    {"giu_chan_3s": "≥ 70%", "y_nghia": "rất tốt"},
]
RETENTION_NOTE = "Mốc tham khảo từ blog bên thứ ba, không phải cam kết. Đăng cả 3 bản, xem tỉ lệ giữ chân 3 giây đầu rồi chọn."
MESSAGES = {
    2: "Em chưa hiểu câu trả lời. Chọn 1 trong các lựa chọn bên dưới.",
    3: "Anh/chị chưa bấm đồng ý chi phí nên em chưa chạy.",
    4: "Nguồn không đọc được / kịch bản trùng nguồn quá 8 từ — em viết lại bằng lời của mình.",
    5: "Kịch bản còn câu nghe như dịch máy hoặc sai nhịp (xem lý do từng câu).",
    6: "Có cảnh tạo ảnh AI chưa được, em dùng hình dự phòng.",
    7: "Chưa có khoá Google AI — chọn giọng miễn phí hoặc dán khoá.",
    8: "Chữ phụ đề lấn vùng giao diện — em đã thu nhỏ/đổi dòng.",
    9: "Chưa tạo được ảnh lưới xem trước.",
    10: "Em chưa chắc ý anh/chị: đổi màu chữ, đổi giọng hay đổi cảnh nào?",
    11: "Video chưa đạt chuẩn.",
    12: "Câu mở đầu chưa đủ lực.",
    13: "Câu này nói về kết quả thật của anh/chị nhưng em chưa có số liệu — anh/chị đưa số hoặc em đổi thành ví dụ minh hoạ.",
    14: "Giọng Google AI mô hình cũ/không chạy — em thử mô hình mới hoặc đề nghị giọng miễn phí.",
}
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
JOB_ID = re.compile(r"[a-z0-9][a-z0-9-]{5,63}")


class StudioError(Exception):
    def __init__(self, number, detail="", **extra):
        self.code = f"E-ags-video-studio-10x-{number:03d}"
        self.message = MESSAGES[number] + (f" {detail}" if detail else "")
        self.extra = extra
        super().__init__(f"{self.code}: {self.message}")

    def payload(self):
        return {"ok": False, "error": {"code": self.code, "message": self.message}, **self.extra}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _config(name):
    path = CONFIG_DIR / name
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _vnd(amount):
    return "0 đồng" if amount == 0 else f"{amount:,}".replace(",", ".") + " đ"


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _gemini_engine():
    """Engine TTS thật cho giọng Google AI: "gemini" khi máy có khoá; "gemini-remote" khi khoá nằm trên máy chủ riêng
    (AGS_GEMINI_SSH_HOST + AGS_GEMINI_SSH_ENV_FILE, khoá không về máy này); None khi chưa có cả hai."""
    if (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip():
        return "gemini"
    if os.environ.get("AGS_GEMINI_SSH_HOST", "").strip() and os.environ.get("AGS_GEMINI_SSH_ENV_FILE", "").strip():
        return "gemini-remote"
    return None


def _gemini_key_present():
    return _gemini_engine() is not None


def _reels_module(name):
    """Module của bộ dựng ags-reels-footage cài cạnh gói này (không nằm trong gói skill): AGS_REELS_DIR nếu có,
    không thì thư mục anh em như scripts/ags_setup.py đăng ký MCP "ags-reels"."""
    import importlib

    env_dir = os.environ.get("AGS_REELS_DIR")
    candidates = [Path(env_dir)] if env_dir else [ROOT.parent / "ags-reels-footage",
                                                   ROOT.parent.parent / "services" / "ops" / "ags-reels-footage"]
    reels_dir = next((p for p in candidates if (p / "ags_reels_pipeline.py").is_file()), None)
    if reels_dir is None:
        raise StudioError(11, "Chưa cài bộ dựng ags-reels-footage — chạy lại cài đặt (ags_setup.py).")
    if str(reels_dir) not in sys.path:
        sys.path.insert(0, str(reels_dir))
    return importlib.import_module(name)


def _image_key_present():
    return bool(_reels_module("ags_director_engine").NINE_ROUTER_KEY)


def jobs_root():
    return Path(os.environ.get("AGS_STUDIO_JOBS_DIR") or Path.home() / "AGS-Studio" / "jobs").expanduser()


def job_dir_for(job_id):
    """Thư mục job từ job_id (HTTP); chặn tên lạ để không thoát khỏi thư mục jobs."""
    if not isinstance(job_id, str) or not JOB_ID.fullmatch(job_id):
        raise StudioError(2, "Mã job không hợp lệ.", choices=[])
    return jobs_root() / job_id


def load_job(job_dir):
    path = Path(job_dir) / JOB_FILE
    if not path.is_file():
        raise StudioError(2, f"Không thấy {JOB_FILE} trong {job_dir} — chạy intake trước.", choices=[])
    return json.loads(path.read_text(encoding="utf-8"))


def save_job(job_dir, job):
    job["updated_at"] = _now()
    path = Path(job_dir) / JOB_FILE
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _new_job(job_dir):
    job_dir = Path(job_dir) if job_dir else jobs_root() / f"{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:6]}"
    job_dir.mkdir(parents=True, exist_ok=True)
    job = {
        "job_id": job_dir.name, "status": "intake", "request": "", "answers": {}, "next_question": None,
        "images": None, "image_prompts": [], "script": "", "hook_text": "", "claims": [], "source_url": "",
        "transcreated": True, "quote": None, "script_report": None, "hook_report": None, "claims_report": None,
        "profile": None,
        "render_params": {"sub_color": "#FFFFFF", "sub_size": None, "voice_engine": None, "voice_name": None,
                          "voice_speed": 1.0, "scene_swap": [], "cta_text": None},
        "revisions": [], "variants": [], "scenes": [], "contact_sheet": None, "output": None, "voice": None,
        "checks": None, "created_at": _now(),
    }
    return job_dir, job


# ---------------------------------------------------------------- intake (FR-004)

def _presets():
    return _config("menu.json").get("presets", {})


def _question(key):
    if key == "topic":
        return {"key": "topic", "number": 1, "text": "Anh/chị muốn làm video về ngành hay chủ đề gì? "
                "(ví dụ: dòng tiền quán cà phê, căn hộ ở Thủ Đức)", "choices": []}
    if key == "preset":
        return {"key": "preset", "number": 2, "text": "Anh/chị thích kiểu video nào?",
                "choices": [{"id": k, "label": v["label"]} for k, v in _presets().items()]}
    return {"key": "voice", "number": 3, "text": "Anh/chị muốn giọng đọc nào?",
            "choices": [{"id": k, "label": v} for k, v in VOICES.items()]}


def _next_question(answers):
    return next((_question(k) for k in QUESTION_ORDER if not answers.get(k)), None)


def _match_preset(text):
    low = text.casefold()
    for preset_id, cfg in _presets().items():
        if low.strip() in (preset_id, cfg["label"].casefold()) or any(a in low for a in cfg.get("aliases", [])):
            return preset_id
    return None


def _match_voice(text):
    low = text.casefold().strip()
    return low if low in VOICES else next((v for v, words in VOICE_ALIASES.items() if any(w in low for w in words)), None)


def _choice_index(text, key):
    choices = _question(key)["choices"]
    if text.strip().isdigit() and 1 <= int(text) <= len(choices):
        return choices[int(text) - 1]["id"]
    return None


def detect_answers(request):
    """Câu khách đã nói sẵn trong yêu cầu đầu: chủ đề sau chữ "về", kiểu video (ưu tiên đoạn sau "kiểu"), giọng."""
    found = {}
    topic = re.search(r"\bvề\s+(.+?)(?=\s*(?:[,.;!?]|$|\bkiểu\b|\btheo\b|\bgiọng\b|\bphong cách\b))", request, re.I)
    if topic and len(topic.group(1).strip()) >= 2:
        found["topic"] = topic.group(1).strip()
    style = re.search(r"\b(?:kiểu|phong cách|mẫu)\s+(.+)$", request, re.I)
    preset = (_match_preset(style.group(1)) if style else None) or _match_preset(request)
    if preset:
        found["preset"] = preset
    voice = re.search(r"\bgiọng\s+(.+)$", request, re.I)
    if voice and _match_voice(voice.group(1)):
        found["voice"] = _match_voice(voice.group(1))
    return found


def _parse_answer(key, value):
    value = str(value or "").strip()
    if key == "topic":
        return value if 2 <= len(value) <= 160 else None
    if key == "preset":
        return _choice_index(value, key) or _match_preset(value) if value else None
    return _choice_index(value, key) or _match_voice(value) if value else None


def intake(job_dir=None, request="", topic=None, preset=None, voice=None, images=None):
    assert_client_licensed()
    if job_dir and (Path(job_dir) / JOB_FILE).is_file():
        job_dir, job = Path(job_dir), load_job(job_dir)
    else:
        job_dir, job = _new_job(job_dir)
    answers = job["answers"]
    if request:
        job["request"] = request
        for key, value in detect_answers(request).items():
            answers.setdefault(key, value)
    invalid = None
    for key, raw in (("topic", topic), ("preset", preset), ("voice", voice)):
        if raw is None:
            continue
        parsed = _parse_answer(key, raw)
        if parsed:
            answers[key] = parsed
        elif invalid is None:
            invalid = key
    if images is not None:
        if images not in ("ai", "free"):
            invalid = invalid or "images"
        else:
            job["images"] = images
    job["next_question"] = _next_question(answers)
    job["status"] = "intake" if job["next_question"] else "ready_to_quote"
    save_job(job_dir, job)
    if invalid == "images":
        raise StudioError(2, "Ảnh: chọn ai hoặc free.", choices=[{"id": "ai", "label": "Ảnh AI (có phí)"},
                                                                 {"id": "free", "label": "Hình miễn phí"}])
    if invalid:
        q = _question(invalid)
        raise StudioError(2, q["text"], question=q, choices=q["choices"], job_id=job["job_id"], job_dir=str(job_dir))
    labels = _presets().get(answers.get("preset"), {}).get("label")
    return {"ok": True, "job_id": job["job_id"], "job_dir": str(job_dir), "answers": answers,
            "preset_label": labels, "next_question": job["next_question"]}


# ---------------------------------------------------------------- script checks (lát A) + quote (FR-005, BR-004)

def _sentences(script):
    return [s.strip() for s in SENTENCE_SPLIT.split(script.strip()) if s.strip()]


def _script_for_render(job):
    """Kịch bản đọc thật: câu cuối (CTA) được thay/bỏ theo render_params.cta_text khi khách đã sửa."""
    cta = job["render_params"].get("cta_text")
    if cta is None:
        return job["script"].strip()
    lines = _sentences(job["script"])[:-1] + ([cta.strip()] if cta.strip() else [])
    return " ".join(lines)


def check_script(job):
    """BR-001/002/003/010/012 qua ags_vi_script (lát A); ghi báo cáo vào job, lỗi đầu tiên -> StudioError."""
    from ags_vi_script import check_claims, score_hook, validate_script

    script = _script_for_render(job)
    preset = _presets()[job["answers"]["preset"]]
    job["script_report"] = validate_script(script, float(preset["duration_sec"]), job.get("source_text") or None)
    job["hook_report"] = score_hook(_sentences(script)[0], job.get("hook_text") or None)
    job["claims_report"] = check_claims(script, job.get("claims") or [])
    for report, number in ((job["script_report"], 5), (job["hook_report"], 12), (job["claims_report"], 13)):
        if not report["ok"]:
            codes = {e.get("code") for e in report["errors"]}
            raise StudioError(4 if "E-ags-video-studio-10x-004" in codes else number,
                              errors=report["errors"], job_id=job["job_id"])


def _image_count(job):
    if job["script"]:
        return len(_sentences(_script_for_render(job)))
    return max(1, round(_presets()[job["answers"]["preset"]]["duration_sec"] / 7.5))


def _tts_chars(job):
    from ags_tts import normalize_vietnamese_tts_text

    if job["script"]:
        return len(normalize_vietnamese_tts_text(_script_for_render(job)))
    return round(_presets()[job["answers"]["preset"]]["duration_sec"] * 2.4 * 5)  # BR-002 nhịp 2,4 từ/giây


def build_quote(job, images=None, tts_chars=None):
    """Bảng chi phí: ảnh AI × đơn giá + ký tự Gemini × đơn giá; số nguyên VND làm tròn lên 1.000 đ."""
    pricing = _config("pricing.json")
    voice = job["render_params"].get("voice_engine") or job["answers"]["voice"]
    n_images = (_image_count(job) if images is None else images) if job["images"] == "ai" else 0
    chars = (_tts_chars(job) if tts_chars is None else tts_chars) if voice == "gemini" else 0
    image_price, per_1000 = pricing.get("image_ai_vnd"), pricing.get("gemini_tts_vnd_per_1000_chars")
    items = [
        {"name": "Ảnh AI", "qty": n_images, "unit": "ảnh", "unit_price_vnd": image_price,
         "amount_vnd": n_images * image_price if image_price is not None else (0 if not n_images else None)},
        {"name": "Giọng Google AI (Gemini)", "qty": chars, "unit": "ký tự", "unit_price_vnd_per_1000_chars": per_1000,
         "amount_vnd": math.ceil(chars * per_1000 / 1000) if per_1000 is not None else (0 if not chars else None)},
    ]
    missing = any(i["amount_vnd"] is None for i in items)
    milli = n_images * (image_price or 0) * 1000 + chars * (per_1000 or 0)
    total = None if missing else -(-milli // 1_000_000) * 1000
    minutes = math.ceil(_presets()[job["answers"]["preset"]]["duration_sec"] / 60
                        * float(pricing.get("render_minutes_per_video_minute") or 3))
    return {
        "items": items, "total_vnd": total, "total_text": "chưa có bảng giá" if missing else _vnd(total),
        "images_mode": job["images"], "voice": voice, "render_minutes_estimate": minutes,
        "basis": "kich_ban" if job["script"] else "uoc_tinh_theo_thoi_luong",
        "script_sha256": _sha(_script_for_render(job)) if job["script"] else None, "created_at": _now(),
        "confirm_hint": "Anh/chị trả lời \"chạy\" thì em mới bắt đầu dựng.",
    }


def quote(job_dir, script=None, hook_text=None, claims=None, source_url=None, source_text=None, image_prompts=None):
    assert_client_licensed()
    job_dir, job = Path(job_dir), load_job(job_dir)
    if job["next_question"]:
        q = job["next_question"]
        raise StudioError(2, q["text"], question=q, choices=q["choices"], job_id=job["job_id"])
    if job["images"] is None:
        job["images"] = "ai" if _image_key_present() else "free"
    for key, value in (("script", script), ("hook_text", hook_text), ("claims", claims),
                       ("source_url", source_url), ("source_text", source_text), ("image_prompts", image_prompts)):
        if value is not None:
            job[key] = value
    save_job(job_dir, job)
    voice = job["render_params"].get("voice_engine") or job["answers"]["voice"]
    if voice == "gemini" and not _gemini_key_present():  # AC-004: báo rõ, không tự đổi giọng
        raise StudioError(7, suggestions=["synth", "vieneu"], voice="gemini", job_id=job["job_id"])
    if job["script"]:
        try:
            check_script(job)
        finally:
            save_job(job_dir, job)
    job["quote"] = build_quote(job)
    job["status"] = "quoted"
    save_job(job_dir, job)
    return {"ok": True, "job_id": job["job_id"], "quote": job["quote"]}


# ---------------------------------------------------------------- run (FR-005 gate, FR-009..014, FR-024)

def _ffprobe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt:format=duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), {})
    num, den = (int(x) for x in video["r_frame_rate"].split("/"))
    return {"width": video["width"], "height": video["height"], "fps": round(num / den, 3),
            "video_codec": video["codec_name"], "pix_fmt": video.get("pix_fmt"),
            "audio_codec": audio.get("codec_name"), "duration_sec": round(float(data["format"]["duration"]), 3)}


def _gray_frame(inputs, t, vf):
    """Một khung xám (bytes -> mảng 1 chiều) tại giây `t` (tua sau khi giải mã: đúng khung) qua bộ lọc `vf`."""
    import numpy as np

    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", *inputs, "-vf", vf, "-ss", f"{t:.3f}", "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8)


def check_hook_frame(final_mp4, nohook_mp4, t=0.3):
    """AC-011: khung t=0,3 s của bản cuối khác bản không hook ở dải trên vùng an toàn = chữ hook đã hiện."""
    from ags_common import safe_box

    w, h = 270, 480
    a = _gray_frame(["-i", str(final_mp4)], t, f"scale={w}:{h}").reshape(h, w).astype(int)
    b = _gray_frame(["-i", str(nohook_mp4)], t, f"scale={w}:{h}").reshape(h, w).astype(int)
    x0, y0, x1, y1 = (v // 4 for v in safe_box(1080, 1920))
    band = abs(a[y0:y0 + (y1 - y0) // 2, x0:x1] - b[y0:y0 + (y1 - y0) // 2, x0:x1]) > 40
    ratio = float(band.mean())
    return {"t_sec": t, "changed_ratio": round(ratio, 4), "ok": ratio >= 0.01}


def check_subtitle_safe_zone(ass_path, samples=6):
    """AC-007/BR-006: vẽ đúng file .ass lên nền xám ở mốc các cụm dài nhất; hộp chữ phải nằm trọn SAFE_ZONE_9X16,
    cỡ chữ phụ đề ≥ 5,8% cạnh ngắn."""
    import numpy as np
    from ags_common import font_path, safe_box
    from ags_editorial_sub import STYLES, subtitles_filter

    fonts_dir = Path(font_path(STYLES["bt_vi"]["font"])).parent

    events = []
    for line in Path(ass_path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"Dialogue: 0,(\d+):(\d+):(\d+\.\d+),[^,]*,Caption,,0,0,0,,(.*)$", line)
        if m:
            start = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
            fs = int(re.search(r"\\fs(\d+)", m.group(4)).group(1))
            events.append((len(re.sub(r"\{[^}]*\}", "", m.group(4))), start, fs))
    x0, y0, x1, y1 = safe_box(1080, 1920)
    worst = [1080, 1920, 0, 0]
    for _, start, _fs in sorted(events, reverse=True)[:samples]:
        # Nền xám 1 khung đặt đúng mốc `start` (setpts) rồi vẽ phụ đề: không phải giải mã cả đoạn trước đó.
        frame = _gray_frame(["-f", "lavfi", "-i", "color=c=0x808080:s=1080x1920:r=30:d=0.1"], 0.0,
                            f"setpts=PTS+{start + 0.05:.3f}/TB,{subtitles_filter(ass_path, fonts_dir)}")
        ys, xs = np.where(np.abs(frame.reshape(1920, 1080).astype(int) - 128) > 12)
        if xs.size:
            worst = [min(worst[0], int(xs.min())), min(worst[1], int(ys.min())),
                     max(worst[2], int(xs.max())), max(worst[3], int(ys.max()))]
    min_fs = min((fs for *_, fs in events), default=0)
    inside = worst[2] == 0 or (worst[0] >= x0 and worst[1] >= y0 and worst[2] < x1 and worst[3] < y1)
    return {"safe_box": [x0, y0, x1, y1], "text_bbox": worst, "samples": min(samples, len(events)),
            "min_font_px": min_fs, "ok": inside and min_fs >= round(0.058 * 1080)}


def _asr_ready():
    """FR-012: faster-whisper và mô hình "base" đã có sẵn trên máy (không tải) → phụ đề lấy mốc từng từ của giọng đọc;
    không có thì bộ dựng chia thời gian câu theo độ dài âm tiết."""
    try:
        from faster_whisper.utils import download_model

        download_model("base", local_files_only=True)
        return True
    except Exception:
        return False


def _render(job_dir, job):
    """Dựng lại toàn bộ video theo job (ảnh AI và giọng đã trả tiền được dùng lại từ cache/)."""
    preset = _presets()[job["answers"]["preset"]]
    params = job["render_params"]
    voice = params.get("voice_engine") or job["answers"]["voice"]
    images_ai = job["images"] == "ai" and _image_key_present()
    stem = f"ags-{preset['file_prefix']}-{job['job_id']}" + (f"-r{len(job['revisions'])}" if job["revisions"] else "")
    while (job_dir / f"{stem}.mp4").exists():  # chạy lại: không ghi đè bản cũ
        stem += "-x"
    out = job_dir / f"{stem}.mp4"
    nohook = job_dir / f"{stem}-nohook.mp4"
    script = _script_for_render(job)
    # BR-012: số khai là "vi-du" có mặt trong lời đọc ⇒ nhãn "ví dụ" trên màn hình (kể cả số ngôi thứ ba, vd giá vé).
    example = any(c.get("claim_source") == "vi-du" and (c.get("text") or "").strip()
                  and c["text"].strip().lower() in script.lower() for c in job.get("claims") or [])
    job["status"] = "rendering"
    save_job(job_dir, job)
    try:
        res = _reels_module("ags_reels_pipeline").run_one_prompt_reels_pipeline(
            topic=job["answers"]["topic"], voiceover_script=script, output_mp4=out,
            cta="", tts_engine=_gemini_engine() if voice == "gemini" else voice,
            tts_style=preset.get("voice_style", "") if voice == "gemini" else "",
            subtitle_style="bt_vi", transition="dissolve", archetype=preset["archetype"],
            broll_mode="ai_image" if images_ai else "archetype", strict_hook=False, allow_local_file=False,
            motion="alternate", hook_text=job.get("hook_text") or "", hook_whoosh=True,
            sub_color=params.get("sub_color") or "", sub_size=params.get("sub_size"),
            voice_speed=float(params.get("voice_speed") or 1.0), swap_scenes=params.get("scene_swap") or [],
            ai_fallback=True, ai_style=preset.get("image_style", ""), example_label="ví dụ" if example else "",
            cache_dir=str(job_dir / "cache"), contact_sheet_path=str(job_dir / CONTACT_SHEET), nohook_mp4=str(nohook),
            verify_asr=_asr_ready(), scene_prompts=job.get("image_prompts") or [],
            tts_voice=params.get("voice_name") or None, transition_sec=0.25, fill_to_sec=float(preset["duration_sec"]),
            example_terms=[c["text"].strip() for c in job.get("claims") or []
                           if c.get("claim_source") == "vi-du" and (c.get("text") or "").strip()],
        )
    except Exception as exc:
        job["status"] = "failed"
        save_job(job_dir, job)
        if isinstance(exc, StudioError):
            raise
        cause = exc.__cause__
        if voice == "gemini" and 400 <= getattr(cause, "status", 0) < 500:
            raise StudioError(14, str(cause)[:300], suggestions=["synth", "vieneu"], job_id=job["job_id"]) from None
        raise StudioError(11, str(exc)[:500], job_id=job["job_id"]) from None
    manifest = res["scene_manifest"]
    if not (job_dir / CONTACT_SHEET).is_file():
        raise StudioError(9, job_id=job["job_id"])
    rel = lambda p: Path(p).resolve().relative_to(job_dir.resolve()).as_posix()  # noqa: E731
    job["output"] = {
        "mp4": rel(out), "nohook_mp4": rel(nohook), "scene_json": rel(res["scene_json_path"]),
        "provenance_json": rel(res["provenance_json_path"]), "subtitles_ass": manifest.get("subtitles_ass"),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "ffprobe": _ffprobe(out),
        "guard_exit": res["quality_gate"]["exit_code"], "lufs": res["quality_gate"]["integrated_lufs"],
    }
    job["contact_sheet"] = CONTACT_SHEET
    job["scenes"] = manifest["scenes"]
    job["keywords"] = manifest.get("keywords", [])
    job["voice"] = {"engine": voice, "voice_name": params.get("voice_name"),
                    "speed": float(params.get("voice_speed") or 1.0),
                    "key_present": _gemini_key_present() if voice == "gemini" else False,
                    "transport": ("ssh" if _gemini_engine() == "gemini-remote" else "local") if voice == "gemini" else None,
                    "model": manifest.get("tts_model"), "style": manifest.get("tts_style") or ""}
    job["images_used"] = "ai_image" if images_ai else "archetype"
    job["fallback_scenes"] = manifest.get("fallback_scenes", [])
    asr = manifest.get("asr_verification")
    job["checks"] = {"hook_frame": check_hook_frame(out, nohook),
                     "subtitle_safe_zone": check_subtitle_safe_zone(job_dir / manifest["subtitles_ass"]),
                     "word_timing": {"method": "asr", "asr_match_ratio": asr["asr_match_ratio"]} if asr
                     else {"method": "syllable_length"}}
    job["status"] = "done"
    save_job(job_dir, job)
    warnings = []
    if job["fallback_scenes"]:
        warnings.append({"code": "E-ags-video-studio-10x-006", "message": MESSAGES[6],
                         "lines": [f["line_id"] for f in job["fallback_scenes"]]})
    if not job["checks"]["subtitle_safe_zone"]["ok"]:
        warnings.append({"code": "E-ags-video-studio-10x-008", "message": MESSAGES[8]})
    return warnings


def run(job_dir, confirmed=False):
    assert_client_licensed()
    job_dir, job = Path(job_dir), load_job(job_dir)
    if job["next_question"]:
        q = job["next_question"]
        raise StudioError(2, q["text"], question=q, choices=q["choices"], job_id=job["job_id"])
    if not confirmed:  # trước mọi lệnh gọi dịch vụ ngoài hay render (AC-003)
        raise StudioError(3, quote=job.get("quote"), job_id=job["job_id"])
    voice = job["render_params"].get("voice_engine") or job["answers"]["voice"]
    if voice == "gemini" and not _gemini_key_present():
        raise StudioError(7, suggestions=["synth", "vieneu"], voice="gemini", job_id=job["job_id"])
    if not job["script"]:
        raise StudioError(5, "Chưa có kịch bản: agent viết kịch bản rồi chạy quote --script-file.", job_id=job["job_id"])
    if not job.get("quote") or job["quote"].get("script_sha256") != _sha(_script_for_render(job)):
        raise StudioError(3, "Kịch bản đã đổi sau lần báo giá — báo lại chi phí (quote) rồi xác nhận.", job_id=job["job_id"])
    check_script(job)
    warnings = _render(job_dir, job)
    return {"ok": True, "job_id": job["job_id"], "output": job["output"], "contact_sheet": job["contact_sheet"],
            "checks": job["checks"], "voice": job["voice"], "warnings": warnings}


# ---------------------------------------------------------------- revise (FR-015, BR-007)

def parse_revision(say, params):
    """Câu sửa tiếng Việt -> {tham số whitelist: giá trị mới}; không khớp thì {} (không đoán)."""
    from ags_editorial_sub import BT_VI_SIZE_RANGE

    low = say.casefold()
    changes = {}
    if re.search(r"\b(sub|phụ đề|chữ)\b", low) and re.search(r"\b(màu|sang|thành)\b", low):
        color = next((c for word, c in COLOR_WORDS.items() if re.search(rf"\b{word}\b", low)), None)
        if color:
            changes["sub_color"] = color
    if re.search(r"\b(chữ|sub|phụ đề)\b.*\b(to|lớn)\b", low):
        changes["sub_size"] = BT_VI_SIZE_RANGE[1]
    elif re.search(r"\b(chữ|sub|phụ đề)\b.*\bnhỏ\b", low):
        changes["sub_size"] = BT_VI_SIZE_RANGE[0]
    speed = float(params.get("voice_speed") or 1.0)
    if re.search(r"\b(đọc|nói|giọng)\b.*\bnhanh\b", low):
        changes["voice_speed"] = round(min(1.2, speed + 0.1), 2)
    elif re.search(r"\b(đọc|nói|giọng)\b.*\bchậm\b", low):
        changes["voice_speed"] = round(max(0.85, speed - 0.1), 2)
    engine = re.search(r"\bđổi giọng\b.*\b(google|gemini|vieneu|miễn phí|giọng máy)\b", low)
    if engine:
        changes["voice_engine"] = _match_voice(engine.group(1))
    scene = re.search(r"\bđổi cảnh(?: số)?\s+(\d+)", low)
    if scene:
        changes["scene_swap"] = sorted(set(params.get("scene_swap") or []) | {int(scene.group(1))})
    if re.search(r"\bbỏ\b.*\b(cta|lời kêu gọi|câu chốt)\b", low):
        changes["cta_text"] = ""
    else:
        cta = re.search(r"\b(?:cta|lời kêu gọi|câu chốt)\b\s*(?:thành|sang|là)\s*[\"“']?(.+?)[\"”']?\s*$", say, re.I)
        if cta and len(cta.group(1).split()) <= 10:
            changes["cta_text"] = cta.group(1).strip()
    return changes


def revise(job_dir, say, confirmed=False):
    assert_client_licensed()
    job_dir, job = Path(job_dir), load_job(job_dir)
    params = job["render_params"]
    changes = parse_revision(say or "", params)
    if not changes:
        raise StudioError(10, suggestions=REVISE_SUGGESTIONS, job_id=job["job_id"])
    if changes.get("voice_engine") == "gemini" and not _gemini_key_present():
        raise StudioError(7, suggestions=["synth", "vieneu"], voice="gemini", job_id=job["job_id"])
    if "scene_swap" in changes and job["script"]:
        n_lines = len(_sentences(_script_for_render(job)))
        if not all(1 <= n <= n_lines for n in changes["scene_swap"]):
            raise StudioError(10, f"Video có {n_lines} cảnh.", suggestions=REVISE_SUGGESTIONS, job_id=job["job_id"])
    extra = None
    if job["output"]:
        # Chi phí thêm: chỉ phần phải trả tiền lại (ảnh của cảnh đổi, giọng Google AI mới/đổi tốc độ không tốn).
        new_swaps = len(set(changes.get("scene_swap", [])) - set(params.get("scene_swap") or []))
        old_voice = params.get("voice_engine") or job["answers"]["voice"]
        new_voice = changes.get("voice_engine", old_voice)
        trial = {**job, "render_params": {**params, **changes}}
        extra = build_quote(trial, images=new_swaps,
                            tts_chars=None if (new_voice != old_voice or "cta_text" in changes) else 0)
        if extra["total_vnd"] != 0 and not confirmed:
            raise StudioError(3, "Lần sửa này có chi phí thêm.", quote=extra, job_id=job["job_id"])
    entry = {"at": _now(), "say": say, "changes": {k: {"from": params.get(k), "to": v} for k, v in changes.items()},
             "extra_quote": extra, "rendered": bool(job["output"])}
    params.update(changes)
    if "cta_text" in changes and job["script"]:
        check_script(job)  # câu chốt mới vẫn phải qua BR-002 (CTA ≤ 10 từ, nhịp); lỗi thì không lưu gì
    job["revisions"].append(entry)
    if job["quote"]:
        job["quote"] = build_quote(job)  # giá cho kịch bản/giọng sau khi sửa (run vẫn cần --confirmed)
    save_job(job_dir, job)
    warnings = _render(job_dir, job) if job["output"] else []
    return {"ok": True, "job_id": job["job_id"], "revision": entry, "render_params": params,
            "quote": job["quote"], "output": job["output"], "warnings": warnings}

# ---------------------------------------------------------------- HTTP 127.0.0.1:8792 /api/v1/studio/* (api-map.md)


def http_api(action, data):
    """Cùng lõi với CLI; job nằm trong jobs_root()/<job_id>. Lỗi nghiệp vụ -> StudioError."""
    data = data or {}
    job_dir = job_dir_for(data["job_id"]) if data.get("job_id") else None
    if action == "intake":
        answers = data.get("answers") or {}
        return intake(job_dir, str(data.get("request") or ""), answers.get("topic"), answers.get("preset"),
                      answers.get("voice"), data.get("images"))
    if action == "jobs":
        if job_dir is None:
            raise StudioError(2, "Thiếu job_id.", choices=[])
        return {"ok": True, "job": load_job(job_dir)}
    if job_dir is None and action in ("quote", "run", "revise", "variants"):
        raise StudioError(2, "Thiếu job_id.", choices=[])
    if action == "quote":
        return quote(job_dir, data.get("script"), data.get("hook_text"), data.get("claims"), data.get("source_url"),
                     data.get("source_text"))
    if action == "run":
        return run(job_dir, data.get("confirmed") is True)
    if action == "revise":
        return revise(job_dir, str(data.get("say") or ""), data.get("confirmed") is True)
    if action == "variants":
        return variants(job_dir, int(data.get("count") or 0), data.get("hooks") or [], data.get("confirmed") is True)
    assert_client_licensed()
    from ags_vi_script import profile_samples, score_hook, validate_script

    if action == "validate-script":
        result, key = validate_script(str(data.get("script") or ""), float(data.get("duration_sec") or 60),
                                      data.get("source_text")), "script_report"
    elif action == "hook":
        script = str(data.get("script") or "")
        result, key = score_hook((_sentences(script) or [""])[0], data.get("on_screen")), "hook_report"
        if data.get("type"):
            result = {**result, "requested_type": data["type"], "type_matches": result.get("type") == data["type"]}
    elif action == "profile":
        result, key = profile_samples(list(data.get("samples") or [])), "profile"
    else:
        raise StudioError(2, f"Không có lệnh studio '{action}'.", choices=[])
    if job_dir is not None:
        job = load_job(job_dir)
        job[key] = result
        save_job(job_dir, job)
    return {"ok": True, key: result}



# ---------------------------------------------------------------- variants (FR-023)

def _burn_hook(src, dst, text, seconds):
    from ags_editorial_sub import subtitles_filter, write_ass

    ass = dst.with_suffix(".ass")
    fonts = write_ass([], ass, 1080, 1920, style="bt_vi", highlight="#A8FF3E", hook=(text, seconds))
    try:
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(src), "-vf", subtitles_filter(ass, fonts),
                        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy",
                        "-movflags", "+faststart", "-y", str(dst)], check=True, capture_output=True)
    finally:
        ass.unlink(missing_ok=True)


def variants(job_dir, count=3, hooks=None, confirmed=False):
    assert_client_licensed()
    from ags_vi_script import score_hook

    job_dir, job = Path(job_dir), load_job(job_dir)
    hooks = [h.strip() for h in (hooks or []) if h and h.strip()]
    if count != 3 or len(hooks) != 3:
        raise StudioError(2, "Làm đúng 3 bản thử: cần 3 câu hook khác loại.", choices=[], job_id=job["job_id"])
    if not job.get("output") or not (job_dir / job["output"]["nohook_mp4"]).is_file():
        raise StudioError(11, "Chưa có video gốc — chạy run trước.", job_id=job["job_id"])
    reports = [score_hook(h, h) for h in hooks]
    bad = [{"hook": h, "errors": r["errors"]} for h, r in zip(hooks, reports) if not r["ok"]]
    if bad or len({r["type"] for r in reports}) < 3:
        raise StudioError(12, "Ba câu hook phải đạt và thuộc 3 loại khác nhau.", hooks=bad or reports, job_id=job["job_id"])
    extra = {"items": [], "total_vnd": 0, "total_text": _vnd(0),
             "note": "Dùng lại hình, giọng và phụ đề của video gốc; chỉ đổi chữ hook 3 giây đầu."}
    if not confirmed:
        raise StudioError(3, "Báo trước: làm 3 bản thử tốn " + extra["total_text"] + ".", quote=extra, job_id=job["job_id"])
    scene = json.loads((job_dir / job["output"]["scene_json"]).read_text(encoding="utf-8"))
    seconds = min(3.0, float(scene.get("hook_seconds") or 2.5))
    out_dir = job_dir / "variants"
    out_dir.mkdir(exist_ok=True)
    guard = ROOT / "harness" / "ags_anti_slop_guard.py"
    made = []
    for label, hook, report in zip("ABC", hooks, reports):
        mp4 = out_dir / f"variant-{label}.mp4"
        mp4.unlink(missing_ok=True)
        _burn_hook(job_dir / job["output"]["nohook_mp4"], mp4, hook, seconds)
        exit_code = subprocess.run([sys.executable, str(guard), str(mp4)], capture_output=True).returncode
        made.append({"id": label, "hook": hook, "hook_type": report["type"], "mp4": mp4.relative_to(job_dir).as_posix(),
                     "sha256": hashlib.sha256(mp4.read_bytes()).hexdigest(), "guard_exit": exit_code})
    job["variants"] = made
    save_job(job_dir, job)
    return {"ok": True, "job_id": job["job_id"], "variants": made, "quote": extra,
            "retention_guide": RETENTION_GUIDE, "retention_note": RETENTION_NOTE}


# ---------------------------------------------------------------- proof (FR-016)

PROOF_GROUPS = ({"business-thinking-60s"}, {"jetlag-vi"}, {"bds"}, {"editorial", "isometric-3d"})


def proof(spec_path, out_dir, confirmed=False):
    """Dựng từng mẫu trong spec (JSON list: name, preset, topic, voice, images?, script|script_file, hook_text,
    claims?, source_url?, image_prompts? (1 chủ thể ảnh tiếng Anh/câu), voice_name?, voice_speed?) vào out_dir/<name>/
    rồi ghi out_dir/proof-manifest.json."""
    assert_client_licensed()
    spec_path, out_dir = Path(spec_path), Path(out_dir)
    items = json.loads(spec_path.read_text(encoding="utf-8"))
    presets = {i.get("preset") for i in items}
    missing = [sorted(g) for g in PROOF_GROUPS if not g & presets]
    if len(items) < 4 or missing:
        raise StudioError(11, "Bộ bằng chứng cần ≥ 4 mẫu: Business Thinking, Jetlag, BĐS, Editorial/3D.", missing=missing)
    if not confirmed:
        raise StudioError(3, "Bộ bằng chứng có thể gọi ảnh AI/giọng Google AI (có phí).")
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for item in items:
        name = str(item["name"])
        if not JOB_ID.fullmatch(name):
            raise StudioError(2, f"Tên mẫu '{name}' chỉ dùng chữ thường, số, gạch nối (6–64 ký tự).", choices=[])
        job_dir = out_dir / name
        script = item.get("script") or (spec_path.parent / item["script_file"]).read_text(encoding="utf-8")
        try:
            intake(job_dir, topic=item["topic"], preset=item["preset"], voice=item["voice"], images=item.get("images"))
            job = load_job(job_dir)
            job["render_params"].update({k: item[k] for k in ("voice_name", "voice_speed") if k in item})
            save_job(job_dir, job)
            quote(job_dir, script=script, hook_text=item.get("hook_text", ""), claims=item.get("claims", []),
                  source_url=item.get("source_url", ""), image_prompts=item.get("image_prompts", []))
            res = run(job_dir, confirmed=True)
        except StudioError as err:
            entries.append({"name": name, "preset": item["preset"], "ok": False, "error": err.payload()["error"]})
            continue
        job = load_job(job_dir)
        entries.append({
            "name": name, "preset": item["preset"], "ok": True,
            "mp4": f"{name}/{job['output']['mp4']}", "sha256": job["output"]["sha256"],
            "ffprobe": job["output"]["ffprobe"], "lufs": job["output"]["lufs"], "guard_exit": job["output"]["guard_exit"],
            "contact_sheet": f"{name}/{CONTACT_SHEET}", "voice": job["voice"], "images": job["images_used"],
            "image_model": _reels_module("ags_director_engine").GPT_IMAGE_MODEL if job["images_used"] == "ai_image"
            else None,
            "scenes": [{k: s.get(k) for k in ("scene_id", "line_id", "start_sec", "end_sec", "motion", "archetype",
                                               "fallback")} for s in job["scenes"]],
            "fallback_scenes": job["fallback_scenes"], "checks": job["checks"],
            "claims": job.get("claims") or [],
            "source_url": job.get("source_url") or "", "transcreated": True, "warnings": res["warnings"],
        })
    manifest = {"created_at": _now(), "items": entries, "ok": all(e["ok"] for e in entries)}
    (out_dir / "proof-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"ok": manifest["ok"], "manifest": str(out_dir / "proof-manifest.json"), "items": entries}


def menu():
    assert_client_licensed()
    cfg = _config("menu.json")
    return {"ok": True, "items": cfg.get("items", []),
            "presets": [{"id": k, "label": v["label"]} for k, v in cfg.get("presets", {}).items()],
            "voices": [{"id": k, "label": v} for k, v in VOICES.items()]}


# ---------------------------------------------------------------- CLI

def _read(path):
    return Path(path).read_text(encoding="utf-8-sig") if path else None


def _human(result):
    if not result.get("ok"):
        err = result.get("error", {})
        lines = [f"{err.get('message', '')} [{err.get('code', '')}]"]
        lines += [f"  - {c.get('label', c)}" for c in result.get("choices", [])]
        lines += [f"  - {s}" for s in result.get("suggestions", [])]
        return "\n".join(lines)
    if result.get("next_question"):
        q = result["next_question"]
        return "\n".join([q["text"]] + [f"  {i}. {c['label']}" for i, c in enumerate(q["choices"], 1)])
    if result.get("quote"):
        q = result["quote"]
        return (f"Chi phí ước tính: {q['total_text']} · thời gian dựng khoảng {q.get('render_minutes_estimate', 0)} phút."
                f"\n{q.get('confirm_hint', '')}")
    return json.dumps(result, ensure_ascii=False, indent=2)


def main(argv=None):
    parser = argparse.ArgumentParser(description="AGS Video Studio — hỏi 3 câu, báo giá, dựng, sửa bằng lời thường")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("intake")
    p.add_argument("--request", default="")
    p.add_argument("--topic")
    p.add_argument("--preset")
    p.add_argument("--voice")
    p.add_argument("--images", choices=["ai", "free"])
    p.add_argument("--job-dir")
    p = sub.add_parser("quote")
    p.add_argument("--job-dir", required=True)
    p.add_argument("--script-file")
    p.add_argument("--hook-text")
    p.add_argument("--claims-file", help="JSON [{text, claim_source}] (BR-012)")
    p.add_argument("--source-url")
    p.add_argument("--source-file", help="văn bản nguồn để kiểm trùng > 8 từ (BR-003)")
    p.add_argument("--image-prompts-file", help='JSON ["chủ thể ảnh tiếng Anh cho câu 1", ...] — 1 dòng/câu (FR-009)')
    p = sub.add_parser("run")
    p.add_argument("--job-dir", required=True)
    p.add_argument("--confirmed", action="store_true")
    p = sub.add_parser("revise")
    p.add_argument("--job-dir", required=True)
    p.add_argument("--say", required=True)
    p.add_argument("--confirmed", action="store_true")
    p = sub.add_parser("variants")
    p.add_argument("--job-dir", required=True)
    p.add_argument("--count", type=int, default=3)
    p.add_argument("--hook", action="append", default=[], help="lặp 3 lần: 3 câu hook khác loại")
    p.add_argument("--confirmed", action="store_true")
    p = sub.add_parser("proof")
    p.add_argument("--spec", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--confirmed", action="store_true")
    sub.add_parser("menu")
    for action in sub.choices.values():
        action.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "intake":
            result = intake(args.job_dir, args.request, args.topic, args.preset, args.voice, args.images)
        elif args.command == "quote":
            claims = json.loads(_read(args.claims_file)) if args.claims_file else None
            result = quote(args.job_dir, _read(args.script_file), args.hook_text, claims, args.source_url,
                           _read(args.source_file),
                           json.loads(_read(args.image_prompts_file)) if args.image_prompts_file else None)
        elif args.command == "run":
            result = run(args.job_dir, args.confirmed)
        elif args.command == "revise":
            result = revise(args.job_dir, args.say, args.confirmed)
        elif args.command == "variants":
            result = variants(args.job_dir, args.count, args.hook, args.confirmed)
        elif args.command == "proof":
            result = proof(args.spec, args.out_dir, args.confirmed)
        else:
            result = menu()
        code = 0 if result.get("ok") else 2
    except StudioError as err:
        result, code = err.payload(), 2
    except Exception as exc:  # giấy phép, I/O: một dòng lời thường, không in stack trace (NFR-004)
        result, code = {"ok": False, "error": {"code": "", "message": f"{type(exc).__name__}: {exc}"}}, 1
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else _human(result))
    return code


if __name__ == "__main__":
    sys.exit(main())

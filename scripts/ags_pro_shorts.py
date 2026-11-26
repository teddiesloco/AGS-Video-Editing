#!/usr/bin/env python3
"""
AGS (Agent Space) Pro Shorts VI: video dài của một PRO nước ngoài -> 3–5 short 9:16 lồng tiếng Việt + kho kiến thức.

  ags_pro_shorts.py <URL | file.mp4> [--voice gemini|vieneu] [--n 3] [--plan plan.json] [--ab-first engine:voice]

Chuỗi: tải (yt-dlp) -> bóc băng từng từ (ags_clip_shorts) -> chọn đoạn + dịch/viết lại tiếng Việt (Gemini, hoặc --plan)
-> lồng MỘT giọng (ags_tts) -> bố cục trên/dưới: clip PRO bám mặt ở nửa trên, hook + phụ đề Việt + dòng nguồn ở nửa
dưới (màu/font brand AgentSea) -> ducking tiếng gốc + SFX nhẹ (ags_sfx) -> -14 LUFS -> guard + contact sheet ->
knowledge.md. Không đăng, không đăng nhập tài khoản nào.

Khoá Gemini chỉ đọc từ biến môi trường GEMINI_API_KEY (hoặc GEMINI_API_KEYS, cách nhau dấu phẩy), không in, không ghi file.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from ags_common import align_script_words, group_word_lists, media_duration, nfc, run_cmd, transcribe_words, video_info  # noqa: E402
from ags_editorial_sub import ass_color, ass_text, fit_layout, format_ass_time  # noqa: E402

W, H, SPLIT, FPS = 1080, 1920, 960, 30
PAPER, INK, GREEN, NEON = "#f4f4ef", "#0e1116", "#1f6f3d", "#a8ff3e"
FONTS = ROOT / "assets" / "fonts"
FONT_HOOK = FONTS / "BricolageGrotesque-Bold.ttf"
FONT_CAPTION = FONTS / "BeVietnamPro-Bold.ttf"
# Vùng chữ nửa dưới (px): mọi hộp chữ nằm dưới đường chia (không che mặt người nói ở nửa trên) và trong dải
# x 120–960, y < 1430 (tránh cột nút bên phải và khối mô tả/tên kênh mà TikTok/Reels/Shorts đè lên đáy màn hình).
HOOK_BOX = (120, 985, 960, 1135)
CAPTION_BOX = (120, 1160, 960, 1360)
SOURCE_BOX = (120, 1385, 960, 1425)
MARGIN_X = 120
FIT_MARGIN = 1.1             # dự phòng chênh số đo Pillow so với libass

MAX_SHORT_SECONDS = 60.0     # bản quyền + nền tảng: mỗi short <= 60 s
MIN_CLIP_SECONDS, MAX_CLIP_SECONDS = 30.0, 58.0
AB_ENGINES = {"vieneu", "gemini"}
VOICE_LEAD, VOICE_TAIL = 0.20, 0.60
MAX_VOICE_TEMPO = 1.20
MISMATCH_SECONDS = 4.0       # clip gốc và giọng Việt lệch hơn mức này -> tắt hẳn tiếng gốc
DUCK_DB = -21.0
DUCK_RANGE = (-24.0, -18.0)
CAPTION_MAX_CHARS, CAPTION_MAX_SECONDS = 36, 3.4
CAPTION_HOLD_SECONDS = 1.0  # giữ phụ đề qua khoảng nghỉ ngắn của giọng thay vì để trống
SFX_GAIN, SFX_MIN_GAP = 0.18, 6.0
CHANNEL_VOICE = {"gemini": "Kore", "vieneu": None}  # một giọng cố định cho cả kênh (chốt sau khi nghe A/B)
GEMINI_TTS_STYLE = "giọng người nói tự nhiên, rõ ràng, nhấn con số và ý chính, nhịp vừa phải"
LUFS_TARGET, LUFS_TOLERANCE, TRUE_PEAK_MAX = -14.0, 1.0, -1.0
LIMIT_DBFS = -2.5            # trần đỉnh mẫu; chừa ~1.5 dB cho đỉnh liên mẫu + mã hoá AAC
LLM_MODEL = os.environ.get("AGS_GEMINI_TEXT_MODEL", "").strip() or "gemini-2.5-flash"


class ProShortsError(RuntimeError):
    """Lỗi có mã E-pro-shorts-vi-NNN trong tài liệu docs/pro-shorts-vi/srs/spec.md."""


def fail(code, message):
    raise ProShortsError(f"E-pro-shorts-vi-{code}: {message}")


# --------------------------------------------------------------------------- nguồn + metadata

def slugify(text):
    text = re.sub(r"[đĐ]", "d", unicodedata.normalize("NFD", text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "video"


def source_line(meta):
    """Dòng nguồn hiện suốt video: tên PRO + kênh."""
    pro, channel = meta["pro"], meta["channel"]
    who = pro if pro.lower() == channel.lower() else f"{pro} · kênh {channel}"
    return nfc(f"Nguồn: {who} · lồng tiếng Việt")


def meta_from_info(info, pro=None):
    channel = info.get("channel") or info.get("uploader") or ""
    video_id = re.sub(r"[^A-Za-z0-9_-]", "_", str(info.get("id", "")))[:64]  # một thành phần đường dẫn an toàn
    return {"id": video_id, "title": info.get("title", ""), "channel": channel,
            "pro": pro or channel, "url": info.get("webpage_url") or info.get("original_url") or "",
            "duration": info.get("duration")}


def acquire(source, work, args):
    """URL -> yt-dlp; đường dẫn file -> dùng thẳng. Trả (video_path, meta)."""
    path = Path(source).expanduser()
    if path.is_file():
        info_file = path.with_suffix(".info.json")
        info = json.loads(info_file.read_text(encoding="utf-8")) if info_file.is_file() else {}
        meta = meta_from_info(info, args.pro)
        for key, value in (("title", args.title), ("channel", args.channel), ("url", args.url)):
            meta[key] = value or meta[key]
        meta["pro"] = args.pro or meta["pro"] or meta["channel"]
        if not (meta["channel"] and meta["url"]):
            fail("002", "file cục bộ cần <tên>.info.json cạnh nó hoặc --channel/--url để ghi nguồn")
        meta["id"] = meta["id"] or slugify(path.stem)
        return path.resolve(), meta
    if not re.match(r"https?://", source):
        fail("001", f"không phải URL cũng không phải file: {source}")
    work.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings", "--no-playlist", "-f", "bv*[height<=1080]+ba/b[height<=1080]",
           "--merge-output-format", "mp4", "--write-info-json", "-o", str(work / "%(id)s.%(ext)s"),
           "--print", "after_move:filepath", *os.environ.get("AGS_YTDLP_ARGS", "").split(), source]
    done = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    files = [Path(line) for line in done.stdout.splitlines() if line.strip().endswith(".mp4")]
    if done.returncode != 0 or not files:
        tail = (done.stderr or done.stdout).strip().splitlines()[-1:] or [""]
        hint = (" — YouTube chặn IP máy chủ: tải video bằng máy khác rồi truyền đường dẫn file, hoặc đặt "
                "AGS_YTDLP_ARGS='--proxy ...'" if "not a bot" in done.stderr else "")
        fail("001", f"yt-dlp lỗi: {tail[0][:300]}{hint}")
    video = files[-1].resolve()
    return video, meta_from_info(json.loads(video.with_suffix(".info.json").read_text(encoding="utf-8")), args.pro)


def transcribe(video, work, model):
    out = work / "transcript.json"
    stat = Path(video).stat()
    fingerprint = [stat.st_size, stat.st_mtime_ns]   # thay nội dung cùng đường dẫn -> bóc băng lại
    if out.is_file():
        cached = json.loads(out.read_text(encoding="utf-8"))
        if cached.get("source") == str(video) and cached.get("model") == model and cached.get("fingerprint") == fingerprint:
            return cached
    import ags_clip_shorts
    ags_clip_shorts.cmd_transcript(argparse.Namespace(input=str(video), model=model, out=str(out)))
    result = json.loads(out.read_text(encoding="utf-8"))
    result["fingerprint"] = fingerprint
    out.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return result


# --------------------------------------------------------------------------- kế hoạch (chọn đoạn + dịch + kiến thức)

def mmss(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600}:{seconds // 60 % 60:02d}:{seconds % 60:02d}" if seconds >= 3600 else f"{seconds // 60}:{seconds % 60:02d}"


def validate_plan(plan, duration, n=None):
    """Kiểm kế hoạch trước khi tốn công render. Ném ProShortsError E-pro-shorts-vi-003/004."""
    shorts = plan.get("shorts") if isinstance(plan, dict) else None
    if not shorts or not isinstance(shorts, list):
        fail("003", "plan thiếu danh sách shorts")
    if n is not None and len(shorts) != n:
        fail("003", f"plan có {len(shorts)} short, cần {n}")
    spans = []
    for number, item in enumerate(shorts, 1):
        where = f"short {number}"
        try:
            start, end = float(item["start"]), float(item["end"])
        except (KeyError, TypeError, ValueError):
            fail("003", f"{where}: thiếu start/end")
        if not 0 <= start < end <= duration + 0.5:
            fail("003", f"{where}: mốc {start}-{end} ngoài video {duration:.0f}s")
        if not MIN_CLIP_SECONDS <= end - start <= MAX_CLIP_SECONDS:
            fail("003", f"{where}: dài {end - start:.1f}s, cần {MIN_CLIP_SECONDS:.0f}–{MAX_CLIP_SECONDS:.0f}s")
        hook = str(item.get("hook", "")).strip()
        if not 3 <= len(hook.split()) <= 8:
            fail("003", f"{where}: hook cần 3–8 chữ, có {len(hook.split())}: {hook!r}")
        segments = [str(s).strip() for s in item.get("segments", []) if str(s).strip()]
        if len(segments) < 2:
            fail("003", f"{where}: cần >= 2 câu lời Việt (segments)")
        if not item.get("name"):
            fail("003", f"{where}: thiếu name")
        spans.append((start, end, where))
    spans.sort()
    for (_, end, _), (start, _, where) in zip(spans, spans[1:]):
        if start < end:
            fail("003", f"{where} chồng lấn short trước")
    lessons = (plan.get("knowledge") or {}).get("lessons", [])
    if not (plan.get("knowledge") or {}).get("summary") or not 5 <= len(lessons) <= 10:
        fail("004", "knowledge cần summary và 5–10 bài học")
    for lesson in lessons:
        if not (lesson.get("title") and lesson.get("body") and 0 <= float(lesson.get("t", -1)) <= duration):
            fail("004", f"bài học thiếu title/body hoặc mốc t ngoài video: {lesson}")
    return plan


def gemini_json(prompt, model=LLM_MODEL):
    """Gọi Gemini generateContent, ép trả JSON. Khoá từ env; không có -> lỗi rõ, không fallback."""
    keys = [k for k in re.split(r"[,;\s]+", os.environ.get("GEMINI_API_KEYS", "")) + [os.environ.get("GEMINI_API_KEY", "")] if k]
    if not keys:
        fail("005", "thiếu GEMINI_API_KEY(S) trong môi trường — truyền --plan plan.json hoặc cấp khoá")
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4}}).encode()
    last = ""
    for key in dict.fromkeys(keys):
        request = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                         data=body, headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            data = json.loads(urllib.request.urlopen(request, timeout=180).read())
            return json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
        except urllib.error.HTTPError as error:
            last = f"HTTP {error.code}"
        except (KeyError, IndexError, ValueError, urllib.error.URLError) as error:
            last = type(error).__name__
    fail("005", f"Gemini ({model}) không trả kết quả dùng được: {last}")


PICK_RULES = (Path(ROOT / "skills/ags-clip-shorts/references/chon-doan-short.md").read_text(encoding="utf-8")
              if (ROOT / "skills/ags-clip-shorts/references/chon-doan-short.md").is_file() else "")


def plan_with_llm(transcript, meta, n, llm=gemini_json):
    """Chọn n đoạn đắt -> mỗi đoạn dịch/viết lại tiếng Việt -> kiến thức. `llm(prompt) -> dict` để thay khi test."""
    sentences = transcript["sentences"]
    listing = "\n".join(f"{s['id']}|{s['start']:.1f}|{s['end']:.1f}|{s['text']}" for s in sentences)
    picks = llm(
        f"Video dài của {meta['pro']} ({meta['title']}). Chọn đúng {n} đoạn đắt để làm short, theo luật sau:\n{PICK_RULES}\n"
        f"Ràng buộc cứng: mỗi đoạn là dải câu liên tiếp, tổng {MIN_CLIP_SECONDS:.0f}–{MAX_CLIP_SECONDS - 8:.0f} giây "
        "(tính end câu cuối - start câu đầu), mở bằng vấn đề/con số, trọn một ý, không chồng lấn, ưu tiên bán hàng/closing/offer.\n"
        'Trả JSON: {"picks":[{"first_id":int,"last_id":int,"name":"slug-ngan","reason":"..."}]}\n'
        f"Câu (id|start|end|text):\n{listing}")["picks"]
    by_id = {s["id"]: s for s in sentences}
    shorts = []
    for pick in picks[:n]:
        first, last = by_id[int(pick["first_id"])], by_id[int(pick["last_id"])]
        english = " ".join(by_id[i]["text"] for i in range(first["id"], last["id"] + 1))
        vi = llm(
            f"Lồng tiếng Việt cho đoạn của {meta['pro']}. Viết lại tự nhiên như người Việt đang nói (KHÔNG dịch máy từng chữ), "
            "người nói xưng 'tôi', gọi người nghe 'bạn'. Giữ nguyên thuật ngữ bán hàng quen dùng (closer, offer, lead, close rate, "
            "upsell...). Tiền viết rõ bằng chữ, ví dụ '100.000 đô la'. Không thêm ý video không nói. Độ dài lời Việt đọc ~"
            f"{(last['end'] - first['start']) * 0.95:.0f} giây (khoảng {(last['end'] - first['start']) * 3.4:.0f} từ). "
            "Chia lời thành 6–12 câu ngắn (segments). hook: 3–8 chữ IN HOA, viết lại ý chính của chính đoạn này.\n"
            'Trả JSON: {"hook":"...","segments":["..."]}\nTiếng Anh:\n' + english)
        shorts.append({"name": slugify(pick.get("name") or vi["hook"]), "start": first["start"], "end": last["end"],
                       "hook": nfc(vi["hook"]).upper(), "segments": [nfc(s) for s in vi["segments"]]})
    knowledge = llm(
        f"Từ băng lời của {meta['pro']} (video {meta['title']}), viết kho kiến thức tiếng Việt cho chủ hộ kinh doanh/OPC Việt Nam: "
        'summary (5–8 câu) và 5–10 lessons, mỗi bài {"title","body"(2–3 câu, áp dụng được),"t"(giây trong video gốc)}. '
        'Chỉ dùng ý có trong băng. Trả JSON: {"summary":"...","lessons":[...]}\nBăng:\n'
        + " ".join(f"[{s['start']:.0f}] {s['text']}" for s in sentences))
    return validate_plan({"shorts": shorts, "knowledge": knowledge}, transcript["duration"], n)


# --------------------------------------------------------------------------- giọng + thời gian

def split_segments(plan_item):
    return [nfc(s).strip() for s in plan_item["segments"] if s.strip()]


def fit_voice_tempo(voice_seconds, clip_seconds=MAX_SHORT_SECONDS):
    """Tốc độ nén giọng (>=1) để lead + giọng + tail nằm trong đoạn gốc đã chọn và <= MAX_SHORT_SECONDS;
    vượt MAX_VOICE_TEMPO -> lỗi (rút ngắn lời)."""
    limit = min(MAX_SHORT_SECONDS - 1.0, clip_seconds - 0.1)
    need = VOICE_LEAD + voice_seconds + VOICE_TAIL
    if need <= limit:
        return 1.0
    tempo = voice_seconds / (limit - VOICE_LEAD - VOICE_TAIL)
    if tempo > MAX_VOICE_TEMPO:
        fail("006", f"giọng Việt {voice_seconds:.1f}s quá dài cho đoạn gốc {clip_seconds:.0f}s / short <= {MAX_SHORT_SECONDS:.0f}s (cần nén x{tempo:.2f})")
    return round(tempo, 3)


def build_timeline(voice_seconds, clip_start, clip_end, source_seconds):
    """Dòng thời gian của short: video gốc bắt đầu ở clip_start, dài = lead + giọng + tail (không đứng hình, không quá 60 s).
    Tiếng gốc 'ducked' nếu độ dài clip gốc và giọng Việt khớp trong MISMATCH_SECONDS, ngược lại 'off'."""
    total = round(VOICE_LEAD + voice_seconds + VOICE_TAIL, 3)
    if total > MAX_SHORT_SECONDS:
        fail("006", f"short {total:.1f}s vượt {MAX_SHORT_SECONDS:.0f}s")
    if total > clip_end - clip_start + 0.01:
        fail("006", f"short {total:.1f}s dài hơn đoạn gốc đã chọn {clip_end - clip_start:.1f}s")
    start = clip_start                      # không dịch mốc đầu, không vượt mốc cuối của đoạn đã chọn
    if start + total > source_seconds + 0.01:
        fail("006", "video nguồn ngắn hơn short cần dựng")
    mode = "ducked" if abs(total - (clip_end - clip_start)) <= MISMATCH_SECONDS else "off"
    return {"src_start": round(start, 3), "total": total, "original_audio": mode}


def ducking_gain(duck_db=DUCK_DB):
    lo, hi = DUCK_RANGE
    if not lo <= duck_db <= hi:
        fail("007", f"ducking {duck_db} dB ngoài khoảng {lo}..{hi} dB")
    return f"volume={duck_db}dB"


def synth_voice(engine, voice, text, out_wav):
    import ags_tts
    style = GEMINI_TTS_STYLE if engine == "gemini" else None
    try:
        ags_tts.generate(engine, text, voice, out_wav, style=style)
    except Exception as error:  # noqa: BLE001 — mọi lỗi TTS dừng pipeline, không giọng thay thế
        fail("008", f"TTS {engine} thất bại: {type(error).__name__}: {str(error)[:300]}")
    return media_duration(out_wav)


def apply_tempo(src, dst, tempo):
    run_cmd(["ffmpeg", "-y", "-v", "error", "-i", src, "-filter:a", f"atempo={tempo}", "-ar", "48000", dst])


def align_voice(script, wav, model):
    """[(start, end, word)] theo CHÍNH giọng TTS tiếng Việt (không theo tiếng Anh gốc)."""
    return align_script_words(script, transcribe_words(wav, model))


def segment_starts(segments, words):
    """Giây bắt đầu mỗi câu lời Việt, suy từ từ đã căn (đếm từ theo cùng cách align_script_words tách)."""
    starts, index = [], 0
    for segment in segments:
        starts.append(words[min(index, len(words) - 1)][0])
        index += len([t for t in nfc(segment).split() if re.search(r"\w", t)])
    return starts


# --------------------------------------------------------------------------- phụ đề + bố cục

def caption_cues(words, lead=VOICE_LEAD):
    """Cụm phụ đề theo mốc giọng TTS: [{start, end, words}]; cụm giữ tới cụm kế nếu hở < CAPTION_HOLD_SECONDS
    (không nháy trống ở chỗ giọng nghỉ giữa câu)."""
    groups = group_word_lists([(s + lead, e + lead, w) for s, e, w in words], CAPTION_MAX_CHARS, CAPTION_MAX_SECONDS,
                              clean=False, semantic_chunk=True)
    cues = [{"start": g[0][0], "end": g[-1][1], "words": [w[2] for w in g]} for g in groups]
    for cue, nxt in zip(cues, cues[1:]):
        if nxt["start"] - cue["end"] < CAPTION_HOLD_SECONDS:
            cue["end"] = nxt["start"]
    return cues


def layout_cue(cue_words, font_file=FONT_CAPTION, base=72, floor=56, box=CAPTION_BOX):
    """(cỡ chữ, dòng) cho cụm phụ đề: tối đa 2 dòng, vừa bề ngang hộp chữ."""
    limit = (box[2] - box[0]) / FIT_MARGIN
    size, _, lines = fit_layout(cue_words, "bold", base, 0, limit, 2, floor, font_file)
    return size, [" ".join(cue_words[i] for i in line) for line in lines]


def _family(font_file):
    from PIL import ImageFont
    return ImageFont.truetype(str(font_file), 12).getname()[0]


def _emphasis(line):
    """Số/tiền trong câu tô xanh brand để mắt bắt được con số."""
    mark = "{\\c" + ass_color(GREEN) + "}"
    reset = "{\\c" + ass_color(INK) + "}"
    return " ".join(f"{mark}{ass_text(w)}{reset}" if re.search(r"\d", w) else ass_text(w) for w in line.split())


def fit_source(source):
    """(từ, cỡ chữ, dòng): dòng nguồn luôn đúng 1 dòng, rộng <= SOURCE_BOX, cao vừa SOURCE_BOX; hạ cỡ chữ tới 22,
    còn dài thì bỏ bớt từ cuối (rồi ký tự cuối của từ duy nhất) + '…' cho tới khi vừa."""
    words = nfc(source).split() or ["…"]
    limit = (SOURCE_BOX[2] - SOURCE_BOX[0]) / FIT_MARGIN
    while True:
        size, font, lines = fit_layout(words, "bold", 34, 0, limit, 1, 22, FONT_CAPTION)
        if len(lines) == 1 and font.getlength(" ".join(words)) <= limit:
            from PIL import ImageFont
            box_h = SOURCE_BOX[3] - SOURCE_BOX[1]
            while size > 16:                       # dấu chồng của tiếng Việt cao hơn cỡ chữ: hạ cỡ tới khi glyph vừa hộp
                top, bottom = ImageFont.truetype(str(FONT_CAPTION), size).getbbox(" ".join(words))[1::2]
                if bottom - top <= box_h:
                    break
                size -= 1
            return words, size, lines
        if len(words) > 1:
            words = words[:-1]
        elif len(words[0]) > 1:
            words = [words[0].rstrip("…")[:-1] + "…"]
        else:
            return words, size, lines
        words[-1] = words[-1].rstrip("…") + "…"


def write_ass(path, cues, hook, source, total):
    """ASS 1080x1920: hook (Bricolage, nền neon) + dòng nguồn (xanh) suốt video; phụ đề Be Vietnam Pro ở giữa nửa dưới."""
    hook_words = nfc(hook).upper().split()
    hook_size, _, hook_lines = fit_layout(hook_words, "bold", 56, 0, (HOOK_BOX[2] - HOOK_BOX[0] - 40) / FIT_MARGIN, 2, 42, FONT_HOOK)
    hook_text = "\\N".join(ass_text(" ".join(hook_words[i] for i in line)) for line in hook_lines)
    styles = [
        f"Style: Hook,{_family(FONT_HOOK)},{hook_size},{ass_color(INK)},&H000000,{ass_color(NEON)},&H00000000,-1,0,0,0,100,100,0,0,3,14,0,5,0,0,0,1",
        f"Style: Caption,{_family(FONT_CAPTION)},72,{ass_color(INK)},&H000000,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,{MARGIN_X},{MARGIN_X},0,1",
        f"Style: Source,{_family(FONT_CAPTION)},34,{ass_color(GREEN)},&H000000,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,{MARGIN_X},{MARGIN_X},0,1",
    ]
    cx = W // 2
    hy = (HOOK_BOX[1] + HOOK_BOX[3]) // 2
    cy = (CAPTION_BOX[1] + CAPTION_BOX[3]) // 2
    src_words, src_size, src_lines = fit_source(source)
    src_text = "\\N".join(ass_text(" ".join(src_words[i] for i in line)) for line in src_lines)
    sy = SOURCE_BOX[3] - round(len(src_lines) * src_size * 1.2 / 2)
    events = [f"Dialogue: 1,{format_ass_time(0)},{format_ass_time(total)},Hook,,0,0,0,,{{\\an5\\pos({cx},{hy})}}{hook_text}",
              f"Dialogue: 0,{format_ass_time(0)},{format_ass_time(total)},Source,,0,0,0,,{{\\an5\\pos({cx},{sy})\\fs{src_size}}}{src_text}"]
    for cue in cues:
        size, lines = layout_cue(cue["words"])
        body = "\\N".join(_emphasis(line) for line in lines)
        events.append(f"Dialogue: 2,{format_ass_time(cue['start'])},{format_ass_time(min(cue['end'], total))},Caption,,0,0,0,,"
                      f"{{\\an5\\pos({cx},{cy})\\fs{size}}}{body}")
    Path(path).write_text("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
                          "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,"
                          "Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
                          "%s\n\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n%s\n"
                          % (W, H, "\n".join(styles), "\n".join(events)), encoding="utf-8")


def sfx_events(starts, total):
    """SFX nhẹ: 1 tiếng ở hook, rồi tối đa 3 tiếng ở chuyển ý (cách nhau >= SFX_MIN_GAP, không sát cuối)."""
    events, last = [{"file": "open_001.ogg", "time": 0.05, "gain": SFX_GAIN}], 0.05
    for t in starts[1:]:
        t = t + VOICE_LEAD
        if len(events) >= 4:
            break
        if t - last >= SFX_MIN_GAP and t < total - 3.0:
            events.append({"file": "pluck_001.ogg", "time": round(t, 2), "gain": SFX_GAIN})
            last = t
    return events


# --------------------------------------------------------------------------- render + kiểm

def render_short(video, item, meta, engine, voice, tmp, out_mp4, args):
    """Một short hoàn chỉnh -> out_mp4. Trả dict báo cáo."""
    segments = split_segments(item)
    script = " ".join(segments)
    raw_wav = Path(tmp) / "vo_raw.wav"
    voice_seconds = synth_voice(engine, voice, script, raw_wav)
    tempo = fit_voice_tempo(voice_seconds, item["end"] - item["start"])
    wav = raw_wav
    if tempo != 1.0:
        wav = Path(tmp) / "vo.wav"
        apply_tempo(raw_wav, wav, tempo)
        voice_seconds = media_duration(wav)
    words = align_voice(script, wav, args.align_model)
    timeline = build_timeline(voice_seconds, item["start"], item["end"], video_info(video)["duration"])
    total = timeline["total"]
    ass = Path(tmp) / "short.ass"
    write_ass(ass, caption_cues(words), item["hook"], source_line(meta), total)
    from ags_reframe import reframe_filter
    top = reframe_filter(video, timeline["src_start"], total, tmp, out_size=(W, SPLIT))
    fonts = str(FONTS).replace(":", "\\:")
    graph = (f"color=c={PAPER.replace('#', '0x')}:s={W}x{H}:r={FPS}:d={total}[bg];[0:v]{top},fps={FPS}[top];"
             f"[bg][top]overlay=0:0,drawbox=x=0:y={SPLIT - 6}:w={W}:h=12:color={GREEN.replace('#', '0x')}:t=fill,"
             f"subtitles='{str(ass).replace(':', chr(92) + ':')}':fontsdir='{fonts}',format=yuv420p[v];"
             f"[1:a]aresample=48000,adelay={int(VOICE_LEAD * 1000)}:all=1,apad=whole_dur={total}[vo]")
    inputs = ["-ss", f"{timeline['src_start']:.3f}", "-t", f"{total}", "-i", video, "-i", wav]
    if timeline["original_audio"] == "ducked":
        graph += f";[0:a]aresample=48000,{ducking_gain()}[orig];[vo][orig]amix=inputs=2:duration=first:normalize=0[a]"
    else:
        graph += ";[vo]anull[a]"
    raw = Path(tmp) / "composed.mp4"
    run_cmd(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-t", f"{total}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", FPS, "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", raw])
    import ags_sfx
    mixed = Path(tmp) / "sfx.mp4"
    ags_sfx.mix(raw, sfx_events(segment_starts(segments, words), total), mixed)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    out_mp4.unlink(missing_ok=True)
    normalize_loudness(mixed, out_mp4)
    return {"file": out_mp4.name, "engine": engine, "voice": voice or "(preset mặc định)", "seconds": total,
            "voice_seconds": round(voice_seconds, 2), "tempo": tempo, "original_audio": timeline["original_audio"],
            "cues": len(caption_cues(words))}


def normalize_loudness(src, dst, passes=3):
    """-14 LUFS: bù gain theo độ to đo được rồi chặn đỉnh ở LIMIT_DBFS (true peak <= -1 dBTP cả sau AAC); limiter làm
    hụt độ to nên đo lại và bù tiếp, tối đa `passes` lượt, tới khi lệch <= 0.3 LU. loudnorm một lượt hụt 1–2 LU trên
    clip < 60 s, còn chế độ tuyến tính của nó bị từ chối khi đỉnh giọng TTS cao so với độ to."""
    lufs, _ = measure_loudness(src)
    gain, limit = LUFS_TARGET - lufs, 10 ** (LIMIT_DBFS / 20)
    for _ in range(passes):
        run_cmd(["ffmpeg", "-y", "-v", "error", "-i", src, "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy",
                 "-af", f"volume={gain:.2f}dB,alimiter=limit={limit:.4f}:level=false:latency=true,aresample=48000",
                 "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", dst])
        lufs, _ = measure_loudness(dst)
        if abs(lufs - LUFS_TARGET) <= 0.3:
            break
        gain += LUFS_TARGET - lufs


def ffprobe_summary(path):
    data = json.loads(run_cmd(["ffprobe", "-v", "error", "-show_entries",
                               "stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels:format=duration",
                               "-of", "json", path]).stdout)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    audio = next(s for s in data["streams"] if s["codec_type"] == "audio")
    num, den = video["r_frame_rate"].split("/")
    return {"video": video["codec_name"], "size": f"{video['width']}x{video['height']}", "fps": round(int(num) / int(den), 3),
            "audio": audio["codec_name"], "sample_rate": audio["sample_rate"], "duration": round(float(data["format"]["duration"]), 2)}


def measure_loudness(path):
    """(LUFS tích hợp, true peak dBTP) bằng ebur128."""
    log = subprocess.run(["ffmpeg", "-nostdin", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    summary = log[log.rfind("Summary:"):]
    lufs = re.search(r"I:\s+(-?[\d.]+) LUFS", summary)
    peak = re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary[summary.find("True peak"):])
    if not lufs or not peak:
        fail("009", "không đo được loudness")
    return float(lufs.group(1)), float(peak.group(1))


def check_output(path):
    """Kiểm đặc tả đầu ra; trả dict báo cáo, ném E-009 nếu sai."""
    probe = ffprobe_summary(path)
    lufs, peak = measure_loudness(path)
    problems = []
    if probe["size"] != f"{W}x{H}" or probe["video"] != "h264" or abs(probe["fps"] - FPS) > 0.01 or probe["audio"] != "aac":
        problems.append(f"định dạng {probe}")
    if probe["duration"] > MAX_SHORT_SECONDS:
        problems.append(f"dài {probe['duration']}s > {MAX_SHORT_SECONDS}s")
    if abs(lufs - LUFS_TARGET) > LUFS_TOLERANCE:
        problems.append(f"{lufs} LUFS ngoài {LUFS_TARGET}±{LUFS_TOLERANCE}")
    if peak > TRUE_PEAK_MAX:
        problems.append(f"true peak {peak} dBTP > {TRUE_PEAK_MAX}")
    if problems:
        fail("009", f"{path.name}: " + "; ".join(problems))
    return {**probe, "lufs": lufs, "true_peak": peak}


def run_guard(mp4, sheet):
    """Guard chất lượng (đen/đứng hình, lặng, loudness, lệch hình-tiếng) + contact sheet sạch để người duyệt xem."""
    done = subprocess.run([sys.executable, str(ROOT / "harness" / "ags_anti_slop_guard.py"), str(mp4),
                           "--contact-sheet", str(sheet)], capture_output=True, text=True, encoding="utf-8")
    return done.returncode, done.stdout.strip()[-600:]


# --------------------------------------------------------------------------- caption gợi ý + kho kiến thức

def caption_text(item, meta):
    return nfc(f"{item['hook'].capitalize()}\n\n" + " ".join(item["segments"][:2]) +
               f"\n\nNguồn: {meta['pro']} (kênh {meta['channel']}) — {meta['url']}\n"
               "Bản lồng tiếng và giảng lại tiếng Việt từ video gốc; xem đủ bài ở kênh gốc.\n")


def knowledge_md(plan, meta):
    k = plan["knowledge"]
    lines = [f"# {meta['title']} — kho kiến thức", "",
             f"- **PRO:** {meta['pro']} (kênh {meta['channel']})", f"- **Nguồn:** {meta['url']}",
             "- Tóm tắt và bài học là bản giảng lại tiếng Việt của người làm kho, không phải lời trích nguyên văn.", "",
             "## Tóm tắt", "", nfc(k["summary"]), "", "## Bài học áp dụng cho chủ HKD/OPC Việt", ""]
    for number, lesson in enumerate(k["lessons"], 1):
        t = float(lesson["t"])
        link = f"{meta['url']}{'&' if '?' in meta['url'] else '?'}t={int(t)}s"
        lines += [f"### {number}. {nfc(lesson['title'])} — [{mmss(t)}]({link})", "", nfc(lesson["body"]), ""]
    lines += ["## Short đã dựng từ video này", ""]
    for number, item in enumerate(plan["shorts"], 1):
        lines.append(f"{number}. `{item['name']}` — {item['hook']} ({mmss(item['start'])}–{mmss(item['end'])} trong video gốc)")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- điều phối

def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("source", help="URL video dài hoặc đường dẫn file (kèm <tên>.info.json cạnh nó)")
    p.add_argument("--voice", choices=["gemini", "vieneu"], default="vieneu", help="provider giọng đọc (một giọng cho cả kênh)")
    p.add_argument("--voice-name", help="tên giọng preset của provider (mặc định: giọng kênh đã chốt)")
    p.add_argument("--n", type=int, default=3, help="số short (3–5)")
    p.add_argument("--plan", type=Path, help="plan.json có sẵn (bỏ qua bước Gemini chọn đoạn/dịch)")
    p.add_argument("--ab-first", metavar="ENGINE:VOICE", help="render thêm short #1 bằng giọng này để so sánh (vd vieneu:Ngọc)")
    p.add_argument("--out-dir", type=Path, default=Path("out"))
    p.add_argument("--work-dir", type=Path, default=Path("work"))
    p.add_argument("--whisper-model", default="base", help="model bóc băng video gốc")
    p.add_argument("--align-model", default="small", help="model căn mốc giọng Việt")
    p.add_argument("--pro", help="tên PRO (mặc định = tên kênh)")
    p.add_argument("--title")
    p.add_argument("--channel")
    p.add_argument("--url")
    args = p.parse_args(argv)
    if not 3 <= args.n <= 5:
        p.error("--n phải từ 3 đến 5")
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.ab_first and args.ab_first.partition(":")[0] not in AB_ENGINES:
            fail("003", f"--ab-first chỉ nhận engine {sorted(AB_ENGINES)} (ZeroTTS chỉ để demo, không dùng cho sản phẩm): {args.ab_first!r}")
        for tool in ("ffmpeg", "ffprobe"):
            if not shutil.which(tool):
                fail("010", f"thiếu {tool} trong PATH")
        staging = args.work_dir.resolve()
        video, meta = acquire(args.source, staging / "download", args)
        work = staging / meta["id"]
        work.mkdir(parents=True, exist_ok=True)
        out = args.out_dir.resolve() / f"{slugify(meta['pro'])}-{slugify(meta['title'])[:32]}-{meta['id']}"
        out.mkdir(parents=True, exist_ok=True)
        transcript = transcribe(video, work, args.whisper_model)
        if args.plan:
            plan = validate_plan(json.loads(args.plan.read_text(encoding="utf-8")), transcript["duration"], args.n)
        else:
            plan = plan_with_llm(transcript, meta, args.n)
        (out / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
        (out / "knowledge.md").write_text(knowledge_md(plan, meta), encoding="utf-8")
        voice = args.voice_name or CHANNEL_VOICE[args.voice]
        jobs = [(i, args.voice, voice) for i in range(1, len(plan["shorts"]) + 1)]
        if args.ab_first:
            engine, _, name = args.ab_first.partition(":")
            jobs.append((1, engine, name or None))
        report = {"source": meta, "shorts": []}
        failed = False
        for number, engine, name in jobs:
            item = plan["shorts"][number - 1]
            label = f"short-{number:02d}" + (f"-{engine}-{slugify(name or 'preset')}" if args.ab_first and number == 1 else "")
            mp4 = out / f"{label}.mp4"
            with tempfile.TemporaryDirectory(prefix="ags_proshort_", dir=work) as tmp:
                entry = render_short(video, item, meta, engine, name, tmp, mp4, args)
            entry["check"] = check_output(mp4)
            code, text = run_guard(mp4, out / f"{label}_sheet.jpg")
            entry.update(guard_exit=code, guard=text)
            if code != 0:
                failed = True
                print(f"❌ E-pro-shorts-vi-011: guard báo lỗi trên {mp4.name} (exit {code}) — giữ file để xem", file=sys.stderr)
            (out / f"{label}.caption.txt").write_text(caption_text(item, meta), encoding="utf-8")
            report["shorts"].append(entry)
            print(json.dumps(entry, ensure_ascii=False), flush=True)
        (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps({"out": str(out), "shorts": len(report["shorts"]), "guard_failed": failed}, ensure_ascii=False))
        return 1 if failed else 0
    except ProShortsError as error:
        print(f"❌ {error}", file=sys.stderr)
        return 1
    except RuntimeError as error:
        print(f"❌ {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

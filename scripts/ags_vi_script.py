#!/usr/bin/env python3
"""
AGS (Agent Space) — kiểm kịch bản Việt hoá cho AGS Video Studio: câu ngắn, không dịch máy, đúng nhịp đọc
(BR-001/002), không chép nguồn quá 8 từ liền (BR-003), chấm hook (BR-010), chặn số kết quả bịa (BR-012), chọn màu
từ khoá theo nghĩa (BR-005) và đo mẫu tham khảo của khách (FR-020). Tất định, chỉ dùng thư viện chuẩn; chỉ `profile`
với link mới đọc mạng — chặn link nội bộ (SSRF), chỉ đọc chữ của trang công khai, không tải hình/tiếng.

  python scripts/ags_vi_script.py validate --script-file kb.txt --duration 60 [--source-file nguon.txt] --json
  python scripts/ags_vi_script.py hook --spoken "Vì sao quán đông khách vẫn hết tiền?" [--on-screen "..."] --json
  python scripts/ags_vi_script.py hook --json              (không có --spoken: in thư viện 8 loại hook để viết hook)
  python scripts/ags_vi_script.py claims --script-file kb.txt --claims-file claims.json --json
  python scripts/ags_vi_script.py profile --sample https://... --sample "văn bản mẫu" --json

Mã thoát: 0 đạt, 1 chưa đạt (danh sách lỗi kèm số câu + lý do), 2 sai tham số.
"""
from __future__ import annotations

import argparse
import functools
import html
import http.client
import ipaddress
import json
import math
import re
import socket
import ssl
import statistics
import sys
import unicodedata
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"

E_SOURCE = "E-ags-video-studio-10x-004"
E_SCRIPT = "E-ags-video-studio-10x-005"
E_HOOK = "E-ags-video-studio-10x-012"
E_CLAIM = "E-ags-video-studio-10x-013"

WORDS_PER_SEC = 2.4          # BR-002: ≈ 144 từ/phút
PACE_TOLERANCE = 0.10
MAX_SENTENCE_WORDS = 16      # BR-001
MAX_AVG_SENTENCE_WORDS = 11
MAX_FOREIGN_RATIO = 0.03
CTA_MAX_WORDS = 10
HOOK_SPOKEN_MAX_WORDS = 14   # BR-010 (câu mở của kịch bản = hook đọc)
HOOK_SCREEN_MAX_WORDS = 8
MAX_SOURCE_RUN = 8           # BR-003: chép quá 8 từ liên tiếp là lỗi
KEYWORD_MIN_GAP = 4          # BR-005: 2 từ khoá cách nhau ≥ 4 từ ⇒ mỗi cụm phụ đề ≤ 4 từ có tối đa 1 từ khoá
MAX_SAMPLES = 5

# BR-001: cấu trúc dịch máy và số lần tối đa được phép trong cả kịch bản.
CALQUE_PATTERNS = (
    ("là một trong những", 0),
    ("chính là việc", 0),
    ("nó là", 0),
    ("bạn có thể", 1),
    ("điều này có nghĩa là", 0),
    ("đóng một vai trò", 0),
    ("đóng vai trò quan trọng", 0),
    ("vào cuối ngày", 0),
)
_CALQUE_RE = [(phrase, limit, re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)")) for phrase, limit in CALQUE_PATTERNS]

# Danh từ riêng / từ mượn được phép (so khớp chữ thường). Viết tắt toàn chữ hoa (KPI, CEO, AI, POV) luôn được phép.
ALLOWED_FOREIGN = frozenset({
    "ok", "video", "facebook", "tiktok", "zalo", "shopee", "lazada", "tiki", "grab", "google", "youtube", "instagram",
    "reels", "shorts", "messenger", "iphone", "apple", "samsung", "amazon", "netflix", "starbucks", "excel", "canva",
    "chatgpt", "gemini", "claude", "agentsea",
})

EDGE_PUNCT = ".,;:!?…\"'“”‘’()[]{}«»<>*_–—-/\\"
_SENTENCE_END = re.compile(r"[.!?…:][\"'”’)\]]*$")
_NUMBER_OK = re.compile(r"\d+(?:[.,]\d+)*(?:k|tr|triệu|tỷ|đ|%)?|24/7")
_MONEY_SUFFIX = re.compile(r"\d(?:k|tr|đ)$")
_VI_SYLLABLE = re.compile(
    r"(?:ngh|ng|nh|ch|gh|gi|kh|ph|qu|th|tr|[bcdghklmnprstvx])?"
    r"(?:uyu|uya|uye|uoi|uou|oai|oay|oeo|ieu|yeu|uay|ai|ao|au|ay|eo|eu|ia|ie|iu|oa|oe|oi|oo|ua|ue|ui|uo|uu|uy|ya|ye"
    r"|[aeiouy])"
    r"(?:ng|nh|ch|[cmnpt])?")

# BR-010: dấu hiệu hook, theo thứ tự ưu tiên khi báo "type".
_W = r"(?<!\w)"
_E = r"(?!\w)"
HOOK_TRIGGERS = (
    ("pov", re.compile(rf"^\W*pov{_E}|{_W}(?:khi bạn là|nếu bạn là){_E}")),
    ("truoc-sau", re.compile(rf"{_W}trước{_E}.*{_W}sau{_E}")),
    ("cau-hoi", re.compile(rf"\?|{_W}(?:tại sao|vì sao|làm sao|bao nhiêu|bao giờ|có nên|là gì|thế nào){_E}")),
    ("canh-bao", re.compile(rf"{_W}(?:đừng|cảnh báo|cẩn thận|sai lầm|mất|lỗ|phá sản|cạn|nợ|bẫy|tránh|nguy hiểm|chết){_E}")),
    ("nghich-ly", re.compile(rf"{_W}(?:nhưng|ngược lại|nghịch lý|không phải|thật ra|sự thật|hoá ra|hóa ra){_E}"
                             rf"|{_W}càng{_E}.+{_W}càng{_E}")),
    ("con-so", re.compile(r"\d")),
)
_GREETING = re.compile(r"(?:xin chào|chào(?! giá| hàng| bán)|chào mừng|hello|hi|hey|alo|a lô|welcome|các bạn ơi"
                       r"|mình là|tôi là|em là|hôm nay mình|hôm nay tôi|hôm nay em)(?!\w)")

# BR-012: câu nói về kết quả của CHÍNH người nói = ngôi thứ nhất + con số + từ chỉ kết quả/tiền/khách.
_FIRST_PERSON = re.compile(rf"{_W}(?:tôi|mình|em|chúng tôi|chúng mình|bọn mình|tụi mình|bọn em|tụi em){_E}")
_RESULT = re.compile(rf"{_W}(?:kiếm|lãi|lời|doanh thu|doanh số|thu nhập|lợi nhuận|bán được|chốt|đơn|khách|tăng|triệu"
                     rf"|tỷ|tỉ|nghìn|ngàn|đồng|follow\w*){_E}|\d\s*(?:k|tr|%)(?!\w)")
EXAMPLE_SOURCE = "vi-du"

MEDIA_EXT = (".mp4", ".mov", ".m4v", ".webm", ".mkv", ".m3u8", ".mp3", ".m4a", ".wav", ".aac",
             ".jpg", ".jpeg", ".png", ".gif", ".webp")


def _nfc(text):
    return unicodedata.normalize("NFC", str(text or ""))


def _clean(token):
    return token.strip(EDGE_PUNCT)


def _tokens(text):
    """Từ của đoạn chữ (NFC, bỏ dấu câu dính hai đầu, giữ %); '99k', '1,9tr' là 1 từ."""
    return [t for t in (_clean(raw) for raw in _nfc(text).split()) if any(c.isalnum() for c in t)]


def _sentences(text):
    parts = re.split(r"(?<=[.!?…])\s+|\n+", _nfc(text).strip())
    return [p.strip() for p in parts if _tokens(p)]


def _target_range(duration_sec):
    mid = duration_sec * WORDS_PER_SEC
    return (math.ceil(round(mid * (1 - PACE_TOLERANCE), 6)), math.floor(round(mid * (1 + PACE_TOLERANCE), 6)))


def _is_foreign(token):
    if any(c.isdigit() for c in token):
        return False
    if token.isupper() and sum(c.isalpha() for c in token) >= 2:
        return False
    low = token.lower()
    if low in ALLOWED_FOREIGN:
        return False
    base = "".join(c for c in unicodedata.normalize("NFD", low) if unicodedata.category(c) != "Mn").replace("đ", "d")
    return not _VI_SYLLABLE.fullmatch(base)


def _triggers(text):
    low = _nfc(text).lower()
    return [name for name, pattern in HOOK_TRIGGERS if pattern.search(low)]


@functools.lru_cache(maxsize=None)
def _config(name):
    return json.loads((CONFIG_DIR / name).read_text(encoding="utf-8"))


def validate_script(script: str, duration_sec: float, source_text: str | None = None) -> dict:
    """BR-001/002 (E-005), câu mở theo BR-010 (`score_hook`) và BR-003 (E-004).
    sentence = số thứ tự câu (từ 1); 0 = lỗi của cả kịch bản."""
    if not duration_sec > 0:
        raise ValueError("duration_sec phải > 0")
    errors = []

    def err(code, sentence, rule, reason):
        errors.append({"code": code, "sentence": sentence, "rule": rule, "reason": reason})

    sentences = _sentences(script)
    per = [_tokens(s) for s in sentences]
    words = sum(len(p) for p in per)
    lo, hi = _target_range(duration_sec)
    stats = {"words": words, "target_range": [lo, hi],
             "avg_sentence_words": round(words / len(per), 2) if per else 0.0,
             "max_sentence_words": max((len(p) for p in per), default=0)}
    if not per:
        err(E_SCRIPT, 0, "nhip", "Kịch bản đang trống.")
        return {"ok": False, "errors": errors, "stats": stats}

    for n, toks in enumerate(per, 1):
        if len(toks) > MAX_SENTENCE_WORDS:
            err(E_SCRIPT, n, "cau-dai",
                f"Câu {n} dài {len(toks)} từ (tối đa {MAX_SENTENCE_WORDS}) — tách thành 2 câu ngắn.")
        for tok in toks:
            if any(c.isdigit() for c in tok) and not _NUMBER_OK.fullmatch(tok.lower()):
                err(E_SCRIPT, n, "so", f"Câu {n}: '{tok}' khó đọc thành lời — viết kiểu 99k, 1,9tr, 40%, 30 năm.")
    if stats["avg_sentence_words"] > MAX_AVG_SENTENCE_WORDS:
        avg = f"{stats['avg_sentence_words']:g}".replace(".", ",")
        err(E_SCRIPT, 0, "tb-cau", f"Trung bình {avg} từ/câu (tối đa {MAX_AVG_SENTENCE_WORDS}) — viết câu ngắn hơn.")
    alpha = [t for toks in per for t in toks if not any(c.isdigit() for c in t)]
    foreign = [t for t in alpha if _is_foreign(t)]
    if alpha and len(foreign) / len(alpha) > MAX_FOREIGN_RATIO:
        err(E_SCRIPT, 0, "tu-ngoai", f"{len(foreign)}/{len(alpha)} từ không phải tiếng Việt "
                                     f"({len(foreign) / len(alpha):.1%}, tối đa 3%): "
                                     f"{', '.join(dict.fromkeys(foreign))} — đổi sang lời Việt.")
    lowered = [s.lower() for s in sentences]
    for phrase, limit, pattern in _CALQUE_RE:
        seen = 0
        for n, sentence in enumerate(lowered, 1):
            seen += len(pattern.findall(sentence))
            if seen > limit:
                cap = f" quá {limit} lần" if limit else ""
                err(E_SCRIPT, n, "dich-may", f"Câu {n} dùng '{phrase}'{cap} — nghe như dịch máy, nói lại kiểu Việt.")
                break

    if not lo <= words <= hi:
        err(E_SCRIPT, 0, "nhip", f"Kịch bản {words} từ; {duration_sec:g} giây cần {lo}–{hi} từ "
                                 f"(2,4 từ/giây ±10%) — {'thêm' if words < lo else 'bớt'} {lo - words if words < lo else words - hi} từ.")
    for hook_error in score_hook(sentences[0])["errors"]:
        err(E_SCRIPT, 1, "hook", hook_error["reason"])
    if len(per[-1]) > CTA_MAX_WORDS:
        err(E_SCRIPT, len(per), "cta", f"Câu kêu gọi cuối dài {len(per[-1])} từ (tối đa {CTA_MAX_WORDS}).")

    if source_text:
        size = MAX_SOURCE_RUN + 1
        src = [t.lower() for t in _tokens(source_text)]
        grams = {tuple(src[i:i + size]) for i in range(len(src) - size + 1)}
        flat = [(n, t.lower()) for n, toks in enumerate(per, 1) for t in toks]
        seq = [w for _, w in flat]
        i = 0
        while i <= len(seq) - size:
            if tuple(seq[i:i + size]) not in grams:
                i += 1
                continue
            j = i + 1
            while j <= len(seq) - size and tuple(seq[j:j + size]) in grams:
                j += 1
            run = j - 1 + size - i
            n = flat[i][0]
            err(E_SOURCE, n, "trung-nguon", f"Câu {n} chép nguyên {run} từ liên tiếp của nguồn "
                                            f"(\"{' '.join(seq[i:i + run])}\"; tối đa {MAX_SOURCE_RUN}) — viết lại bằng lời của mình.")
            i += run
    return {"ok": not errors, "errors": errors, "stats": stats}


def score_hook(spoken: str, on_screen: str | None = None) -> dict:
    """BR-010: lời nói ≤ 14 từ, chữ trên màn hình ≤ 8 từ, có ≥ 1 dấu hiệu, không mở bằng lời chào.
    type = dấu hiệu chính: pov | truoc-sau | cau-hoi | canh-bao | nghich-ly | con-so."""
    errors = []

    def err(rule, reason):
        errors.append({"code": E_HOOK, "rule": rule, "reason": reason})

    spoken_words = _tokens(spoken)
    if not spoken_words:
        err("trong", "Chưa có câu mở đầu.")
    elif len(spoken_words) > HOOK_SPOKEN_MAX_WORDS:
        err("qua-dai", f"Câu mở đọc {len(spoken_words)} từ (tối đa {HOOK_SPOKEN_MAX_WORDS}) — cắt bớt.")
    if on_screen is not None and len(_tokens(on_screen)) > HOOK_SCREEN_MAX_WORDS:
        err("chu-qua-dai", f"Chữ hook trên màn hình {len(_tokens(on_screen))} từ (tối đa {HOOK_SCREEN_MAX_WORDS}).")
    for label, text in (("Câu mở", spoken), ("Chữ hook", on_screen)):
        if text and _GREETING.match(_nfc(text).lower().lstrip(EDGE_PUNCT + " ")):
            err("loi-chao", f"{label} bắt đầu bằng lời chào/giới thiệu — vào thẳng vấn đề.")
    found = _triggers(spoken or "") or _triggers(on_screen or "")
    if spoken_words and not found:
        err("thieu-luc", "Câu mở thiếu con số, câu hỏi, mâu thuẫn, cảnh báo, POV hoặc trước–sau.")
    return {"ok": not errors, "type": found[0] if found else None, "errors": errors}


def check_claims(script: str, claims: list[dict]) -> dict:
    """BR-012: câu nói kết quả của chính khách (ngôi thứ nhất + số + kết quả) phải khớp 1 claim có claim_source.
    claims = [{"text": "50 triệu", "claim_source": "khach-nhap" | "tai-lieu:<tên>" | "vi-du"}];
    claim_source "vi-du" ⇒ label "ví dụ" (in nhãn lên video)."""
    provided = []
    for claim in claims or []:
        text = _nfc(claim.get("text", "")).strip()
        source = str(claim.get("claim_source") or "").strip()
        if text and source:
            provided.append((text, source))
    errors, matched = [], []
    for n, sentence in enumerate(_sentences(script), 1):
        low = sentence.lower()
        if not (_FIRST_PERSON.search(low) and re.search(r"\d", low) and _RESULT.search(low)):
            continue
        hit = next(((t, s) for t, s in provided if t.lower() in low), None)
        if hit is None:
            errors.append({"code": E_CLAIM, "sentence": n, "rule": "chua-co-nguon",
                           "reason": f"Câu {n} (\"{sentence}\") nói kết quả thật của anh/chị nhưng chưa có số liệu — "
                                     f"đưa số của anh/chị hoặc chọn 'ví dụ minh hoạ'."})
        else:
            matched.append({"sentence": n, "text": hit[0], "claim_source": hit[1],
                            "label": "ví dụ" if hit[1] == EXAMPLE_SOURCE else None})
    return {"ok": not errors, "errors": errors, "claims": matched}


def pick_keywords(words: list[str]) -> list[tuple[int, str]]:
    """BR-005: [(chỉ số từ, màu)] cho các từ được tô; cụm nhiều từ ('500 triệu') trả mỗi từ 1 cặp cùng màu.
    Ưu tiên (1) số/tiền/%/thời gian, (2) config/keywords-vi.json, (3) danh từ riêng; 2 từ khoá cách nhau ≥ 4 từ.
    Không có nghĩa tiền/cảnh báo nào ⇒ xen xanh ↔ vàng."""
    cfg = _config("keywords-vi.json")
    colors = cfg["colors"]
    money, time_units, function = set(cfg["money_units"]), set(cfg["time_units"]), set(cfg["function_words"])
    phrases = sorted(((tuple(p.split()), label) for label, items in cfg["keywords"].items() for p in items),
                     key=lambda item: -len(item[0]))
    raw = [_nfc(w) for w in words]
    norm = [_clean(w).lower() for w in raw]

    def proper(i):
        tok = _clean(raw[i])
        return (i > 0 and tok[:1].isupper() and not _SENTENCE_END.search(raw[i - 1])
                and norm[i] not in function and not any(c.isdigit() for c in tok))

    candidates = []  # (ưu tiên, đầu, cuối, nhãn)
    for i, w in enumerate(norm):
        if not w:
            continue
        if any(c.isdigit() for c in w):
            unit = norm[i + 1] if i + 1 < len(norm) and not _SENTENCE_END.search(raw[i]) else ""
            if unit in money:
                candidates.append((1, i, i + 1, "tien"))
            elif unit in time_units:
                candidates.append((1, i, i + 1, "nhan"))
            else:
                candidates.append((1, i, i, "tien" if _MONEY_SUFFIX.search(w) else "nhan"))
            continue
        phrase = next(((p, label) for p, label in phrases if tuple(norm[i:i + len(p)]) == p), None)
        if phrase:
            candidates.append((2, i, i + len(phrase[0]) - 1, phrase[1]))
        elif proper(i):
            j = i
            while j + 1 < len(raw) and not _SENTENCE_END.search(raw[j]) and proper(j + 1):
                j += 1
            # Tên 2 tiếng mở đầu câu ("Việt Nam", "Phú Quý"): chữ hoa đầu câu ngay trước 1 tên riêng đơn thuộc về tên
            # (tên đã đủ 2 tiếng như "Khách Sài Gòn" thì không kéo chữ đầu câu vào).
            head = i - 1 if j == i and (i - 1 == 0 or _SENTENCE_END.search(raw[i - 2])) \
                and _clean(raw[i - 1])[:1].isupper() and norm[i - 1] not in function \
                and not any(c.isdigit() for c in raw[i - 1]) else i
            candidates.append((3, head, j, "nhan"))

    chosen = []
    for _, start, end, label in sorted(candidates, key=lambda c: (c[0], c[1], c[1] - c[2])):
        if all(start - e >= KEYWORD_MIN_GAP or s - end >= KEYWORD_MIN_GAP for s, e, _ in chosen):
            chosen.append((start, end, label))
    chosen.sort()
    semantic = any(label in ("tien", "canh-bao") for _, _, label in chosen)
    picked = []
    for k, (start, end, label) in enumerate(chosen):
        color = colors[label] if semantic else (colors["tien"], colors["nhan"])[k % 2]
        picked.extend((i, color) for i in range(start, end + 1))
    return picked


def _public_ip(host, port):
    """Phân giải DNS 1 lần; mọi địa chỉ phải là IP công khai (cùng luật _resolve_validated_public_ip của
    ags-reels-footage — gói khách không mang pipeline đó nên kiểm lại ở đây)."""
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except OSError:
        infos = []
    if not infos or any(not ipaddress.ip_address(info[4][0].split("%")[0]).is_global for info in infos):
        raise ValueError("ssrf", "Link trỏ vào máy/mạng nội bộ hoặc không tra được địa chỉ — em chặn, "
                                 "dán link công khai hoặc dán chữ.")
    return infos[0][4][0]


def _fetch_public_page(url, max_redirects=3):
    """Chỉ đọc trang chữ (text/html, text/plain ≤ 512 KB): nối thẳng tới IP đã kiểm (chống DNS rebinding), kiểm lại
    từng lần chuyển hướng. Lỗi: ValueError(rule, lý do)."""
    for _ in range(max_redirects + 1):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            raise ValueError("link-khong-hop-le", "Chỉ nhận link http(s) công khai.")
        if parsed.path.lower().endswith(MEDIA_EXT):
            raise ValueError("media", "Link trỏ thẳng vào file hình/tiếng — em chỉ đo chữ của trang, không tải media.")
        https = parsed.scheme.lower() == "https"
        port = parsed.port or (443 if https else 80)
        ip = _public_ip(parsed.hostname, port)
        try:
            sock = socket.create_connection((ip, port), timeout=15)
            if https:
                sock = ssl.create_default_context().wrap_socket(sock, server_hostname=parsed.hostname)
            conn = http.client.HTTPConnection(parsed.hostname, port, timeout=15)
            conn.sock = sock
            try:
                conn.request("GET", (parsed.path or "/") + (f"?{parsed.query}" if parsed.query else ""),
                             headers={"User-Agent": "AGS-Vi-Script/1.0", "Accept": "text/html,text/plain",
                                      "Connection": "close"})
                resp = conn.getresponse()
                location = resp.getheader("Location")
                if resp.status in (301, 302, 303, 307, 308) and location:
                    url = urllib.parse.urljoin(url, location)
                    continue
                content_type = (resp.getheader("Content-Type") or "").lower()
                if resp.status >= 400 or not content_type.startswith(("text/html", "text/plain", "application/xhtml")):
                    raise ValueError("doc-loi", f"Trang trả mã {resp.status} / kiểu '{content_type or '?'}' — em chỉ "
                                                f"đọc trang chữ công khai, dán nội dung chữ thay cho link.")
                return resp.read(512_000).decode("utf-8", errors="ignore")
            finally:
                conn.close()
        except (OSError, http.client.HTTPException):
            raise ValueError("doc-loi", "Không đọc được trang (mạng lỗi hoặc trang chặn) — "
                                        "dán nội dung chữ thay cho link.") from None
    raise ValueError("doc-loi", "Trang chuyển hướng quá nhiều lần — dán nội dung chữ thay cho link.")


def _read_public_page(url):
    """(chữ mô tả của trang, thời lượng video giây | None). Lỗi: ValueError(rule, lý do)."""
    page = _fetch_public_page(url)
    metas = {}
    for tag in re.findall(r"<meta\b[^>]*>", page, re.I):
        attrs = {k.lower(): html.unescape(a or b)
                 for k, a, b in re.findall(r"([\w:-]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')", tag)}
        key = (attrs.get("property") or attrs.get("name") or attrs.get("itemprop") or "").lower()
        if key and "content" in attrs:
            metas.setdefault(key, attrs["content"])
    text = metas.get("og:description") or metas.get("description")
    if not text:
        body = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", page)
        text = " ".join(re.sub(r"<[^>]+>", " ", html.unescape(p)).strip()
                        for p in re.findall(r"(?is)<p\b[^>]*>(.*?)</p>", body))
    duration = None
    raw_duration = metas.get("og:video:duration") or metas.get("video:duration")
    if raw_duration and re.fullmatch(r"\d+(?:\.\d+)?", raw_duration.strip()):
        duration = float(raw_duration)
    else:
        iso = re.search(r"\"duration\"\s*:\s*\"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?\"", page)
        if iso and any(iso.groups()):
            h, m, s = (float(g or 0) for g in iso.groups())
            duration = h * 3600 + m * 60 + s
    return text, duration or None


def profile_samples(samples: list[str]) -> dict:
    """FR-020: đo 1–5 mẫu (link http(s) công khai hoặc văn bản): số từ, độ dài câu, độ dài + loại hook, số nhóm ý,
    từ/giây (khi trang có thời lượng video). Chỉ trả số đo, không trả lại chữ của nguồn."""
    errors, measured = [], []

    def err(index, rule, reason):
        errors.append({"code": E_SOURCE, "sample": index, "rule": rule, "reason": reason})

    if not 1 <= len(samples) <= MAX_SAMPLES:
        err(0, "so-mau", f"Cần 1–{MAX_SAMPLES} mẫu, nhận {len(samples)}.")
        return {"ok": False, "errors": errors, "samples": [], "suggested": None}
    for index, sample in enumerate(samples, 1):
        sample = _nfc(sample).strip()
        is_link = bool(re.match(r"[a-z][a-z0-9+.-]*://", sample, re.I))
        duration = None
        if is_link:
            try:
                text, duration = _read_public_page(sample)
            except ValueError as exc:
                err(index, *exc.args)
                continue
        else:
            text = sample
        sentences = _sentences(text)
        per = [_tokens(s) for s in sentences]
        words = sum(len(p) for p in per)
        if not words:
            err(index, "khong-co-chu", "Mẫu không có chữ để đo.")
            continue
        hook_types = _triggers(sentences[0])
        measured.append({
            "index": index, "source": "url" if is_link else "text", "words": words, "sentences": len(per),
            "avg_sentence_words": round(words / len(per), 2), "max_sentence_words": max(len(p) for p in per),
            "hook_words": len(per[0]), "hook_type": hook_types[0] if hook_types else None,
            "idea_groups": max(0, len(per) - 2), "duration_sec": duration,
            "words_per_sec": round(words / duration, 2) if duration else None,
        })
    suggested = None
    if measured:
        paces = [m["words_per_sec"] for m in measured if m["words_per_sec"]]
        suggested = {
            "words_per_sec": round(statistics.median(paces), 2) if paces else WORDS_PER_SEC,
            "pace_measured": bool(paces),
            "avg_sentence_words": min(MAX_AVG_SENTENCE_WORDS,
                                      round(statistics.median(m["avg_sentence_words"] for m in measured), 1)),
            "hook_words": min(HOOK_SPOKEN_MAX_WORDS, round(statistics.median(m["hook_words"] for m in measured))),
            "hook_types": sorted({m["hook_type"] for m in measured if m["hook_type"]}),
            "ideas": round(statistics.median(m["idea_groups"] for m in measured)),
        }
    return {"ok": not errors and bool(measured), "errors": errors, "samples": measured, "suggested": suggested}


def _read_text(parser, path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        parser.error(f"Không đọc được {path}: {exc.strerror}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — kiểm kịch bản Việt hoá, hook, số liệu, đo mẫu")
    sub = parser.add_subparsers(dest="command", required=True)

    def script_args(p):
        group = p.add_mutually_exclusive_group(required=True)
        group.add_argument("--script", help="Kịch bản (chuỗi UTF-8)")
        group.add_argument("--script-file", type=Path, help="File UTF-8 chứa kịch bản")

    p = sub.add_parser("validate", help="Chấm kịch bản theo BR-001/002/003")
    script_args(p)
    p.add_argument("--duration", type=float, required=True, help="Thời lượng mục tiêu (giây)")
    p.add_argument("--source-file", type=Path, help="Văn bản nguồn tham khảo để kiểm chép quá 8 từ")
    p = sub.add_parser("hook", help="Chấm hook theo BR-010; bỏ --spoken để in thư viện hook")
    p.add_argument("--spoken", help="Câu mở đọc thành lời")
    p.add_argument("--on-screen", help="Chữ hook hiện trên màn hình")
    p = sub.add_parser("claims", help="Kiểm số kết quả cá nhân có nguồn (BR-012)")
    script_args(p)
    p.add_argument("--claims-file", type=Path, help='JSON [{"text": "50 triệu", "claim_source": "khach-nhap|vi-du"}]')
    p = sub.add_parser("profile", help="Đo 1–5 mẫu tham khảo (link công khai hoặc văn bản)")
    p.add_argument("--sample", action="append", default=[], help="Link http(s) công khai hoặc văn bản (lặp được)")
    p.add_argument("--sample-file", type=Path, action="append", default=[], help="File văn bản mẫu (lặp được)")
    for p in sub.choices.values():
        p.add_argument("--json", action="store_true", help="In kết quả JSON")
    args = parser.parse_args(argv)

    from ags_client_license import assert_client_licensed
    try:
        assert_client_licensed()
    except PermissionError as exc:
        parser.exit(1, f"{exc}\n")

    script = None
    if args.command in ("validate", "claims"):
        script = args.script if args.script is not None else _read_text(parser, args.script_file)
    if args.command == "validate":
        if not args.duration > 0:
            parser.error("--duration phải > 0")
        source = _read_text(parser, args.source_file) if args.source_file else None
        result = validate_script(script, args.duration, source)
    elif args.command == "hook":
        if args.spoken is None:
            print(json.dumps(_config("hooks-vi.json"), ensure_ascii=False, indent=1))
            return 0
        result = score_hook(args.spoken, args.on_screen)
    elif args.command == "claims":
        claims = []
        if args.claims_file:
            try:
                claims = json.loads(_read_text(parser, args.claims_file))
            except json.JSONDecodeError as exc:
                parser.error(f"--claims-file không phải JSON: {exc.msg}")
            if not isinstance(claims, list) or not all(isinstance(c, dict) for c in claims):
                parser.error('--claims-file phải là danh sách [{"text": ..., "claim_source": ...}]')
        result = check_claims(script, claims)
    else:
        samples = args.sample + [_read_text(parser, f) for f in args.sample_file]
        result = profile_samples(samples)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        print("ĐẠT" if result["ok"] else "CHƯA ĐẠT")
        for error in result["errors"]:
            print(f"- {error['reason']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

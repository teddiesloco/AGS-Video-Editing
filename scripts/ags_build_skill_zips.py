#!/usr/bin/env python3
"""
AGS (Agent Space) — đóng gói bản phân phối từ mã nguồn trong repo. Chạy:  python scripts/ags_build_skill_zips.py

Tạo hai file trong dist/ (dist/ không commit):
  dist/ags-video-editing.zip      BẢN CÀI ĐẶT CỤC BỘ — thả vào thư mục skill của Claude Code / Antigravity / Codex /
                                  Gemini CLI / Cursor. Gốc zip là thư mục `ags-video-editing/` có SKILL.md ở gốc, kèm
                                  đủ mã nguồn (scripts/, mcp/, harness/, tests/), assets/ (SFX CC0), 9 skill con,
                                  requirements*.txt, installer macOS/Windows, adapters, giấy phép và thông báo bên thứ ba.
                                  Không kèm venv, model, cấu hình sinh ra từ máy (.mcp.json, .cursor/mcp.json).
  dist/ags-video-editing-web.zip  Skill cho claude.ai (Customize → Skills → Upload) — CHỈ hướng dẫn/lập kế hoạch,
                                  không có script chạy (web không đảm bảo FFmpeg/pip/Internet).

Trước khi ghi zip, script kiểm: frontmatter mọi SKILL.md theo Agent Skills spec (agentskills.io), mọi đường dẫn
scripts/harness/mcp/assets/skills/adapters nhắc trong tài liệu đều tồn tại, import nội bộ của mọi file .py đều có mặt,
pin TTS đủ cả hai engine, không còn đường dẫn máy tác giả/biến ${...} chưa giải. Sau khi ghi, giải nén zip vào thư mục
có dấu cách và chạy thử `ags_setup.py --check` + biên dịch toàn bộ .py (không cài gì, không cần Internet).
Zip chỉ để dùng trên máy/tài khoản của chính bạn — giấy phép không cho phân phối lại.
"""

import ast
import compileall
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
PACK_NAME = "ags-video-editing"
WEB_NAME = "ags-video-editing-web"
WEB_SOURCE = ROOT / "adapters" / "web" / WEB_NAME
TOP_FILES = ["SKILL.md", "AGENTS.md", "GEMINI.md", "README.md", "HUONG-DAN-SU-DUNG.md", "CHANGELOG.md", "LICENSE",
             "LICENSE-VI.md", "THIRD_PARTY_NOTICES.md", "CAI-DAT-MAC.sh", "CAI-DAT-WIN.bat", "gemini-extension.json",
             "requirements.txt", "requirements-mcp.txt", "requirements-tts.txt"]
TOP_DIRS = ["scripts", "mcp", "harness", "assets", "skills", "adapters", "tests", ".cursor/rules"]
SKIP_PARTS = {"__pycache__", ".DS_Store", ".git", "venv", "dist", "output"}
SKIP_SUFFIX = {".pyc", ".pyo", ".wav", ".mp4", ".mov", ".mkv", ".webm", ".mp3", ".m4a"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DOC_PATH_RE = re.compile(r"\b((?:scripts|harness|mcp|assets|skills|adapters)/[\w./-]*\.(?:py|md|ogg|txt|json))\b")
# Chuỗi không được lọt vào bản phân phối: đường dẫn máy tác giả, biến client chưa giải, tên nội bộ.
FORBIDDEN = [r"/Users/", r"/tmp/ags", r"C:\\Users\\", r"\$\{workspaceFolder\}", r"\$\{CLAUDE_PROJECT_DIR",
             r"teddiesloco", r"Teddy", r"AgentSea", r"AGENTSEA"]
TEXT_SUFFIX = {".md", ".py", ".json", ".txt", ".sh", ".bat", ".mdc", ".toml", ""}


def frontmatter(text):
    """Các cặp key: value (một dòng) giữa hai dòng '---' đầu file."""
    lines = text.splitlines()
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if not lines or lines[0].strip() != "---" or end is None:
        return None
    fields = {}
    for line in lines[1:end]:
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "\t")):
            value = value.strip()
            fields[key.strip()] = json.loads(value) if value.startswith('"') else value.strip("'")
    return fields


def check_skill(skill_md, expected_name):
    text = skill_md.read_text(encoding="utf-8")
    meta = frontmatter(text)
    where = skill_md.relative_to(ROOT).as_posix()
    if meta is None:
        return [f"{where}: thiếu frontmatter YAML"]
    name, desc = meta.get("name", ""), meta.get("description", "")
    errors = []
    if not (1 <= len(name) <= 64 and NAME_RE.match(name)) or name != expected_name:
        errors.append(f"{where}: name '{name}' sai quy tắc hoặc khác '{expected_name}'")
    if not 1 <= len(desc) <= 1024:
        errors.append(f"{where}: description dài {len(desc)} ký tự (cần 1–1024)")
    if len(meta.get("compatibility", "")) > 500:
        errors.append(f"{where}: compatibility dài hơn 500 ký tự")
    if len(text.splitlines()) >= 500:
        errors.append(f"{where}: SKILL.md phải dưới 500 dòng")
    return errors


def collect(base_dirs, base_files):
    files = {}
    for rel in base_files:
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"❌ Thiếu file bắt buộc: {rel}")
        files[rel] = path
    for rel_dir in base_dirs:
        directory = ROOT / rel_dir
        if not directory.is_dir():
            raise SystemExit(f"❌ Thiếu thư mục bắt buộc: {rel_dir}")
        for path in sorted(directory.rglob("*")):
            if path.is_file() and not (SKIP_PARTS & set(path.relative_to(ROOT).parts)) and path.suffix not in SKIP_SUFFIX:
                files[path.relative_to(ROOT).as_posix()] = path
    return files


def local_modules(files):
    """Tên module nội bộ: file .py trong scripts/, harness/, mcp/ và gói con (scripts/bds)."""
    names = {}
    for rel in files:
        parts = rel.split("/")
        if rel.endswith(".py") and parts[0] in ("scripts", "harness", "mcp"):
            names[parts[-1][:-3] if len(parts) == 2 else parts[1]] = rel
            if len(parts) > 2:
                names[parts[1]] = rel
    return names


def validate(files):
    errors = []
    local = local_modules(files)
    # 1. import nội bộ đều có mặt trong gói
    for rel, path in files.items():
        if not rel.endswith(".py"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        for node in ast.walk(tree):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""] if isinstance(node, ast.ImportFrom) and not node.level else [])
            for full in names:
                top = full.split(".")[0]
                if top.startswith("ags_") and top not in local:
                    errors.append(f"{rel}: import '{top}' không có trong gói")
    # 2. đường dẫn nhắc trong tài liệu phải tồn tại; chuỗi cấm không lọt vào gói
    forbidden = re.compile("|".join(FORBIDDEN))
    for rel, path in files.items():
        if path.suffix not in TEXT_SUFFIX or rel.startswith("assets/") or rel == "scripts/ags_build_skill_zips.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in forbidden.finditer(text):
            errors.append(f"{rel}: chứa chuỗi cấm '{match.group(0)}'")
        if rel.endswith(".md"):
            for ref in sorted(set(DOC_PATH_RE.findall(text))):
                if not (ROOT / ref).exists():
                    errors.append(f"{rel}: nhắc đường dẫn không tồn tại '{ref}'")
    # 3. cả hai engine TTS được pin; SFX và giấy phép asset có mặt
    tts = (ROOT / "requirements-tts.txt").read_text(encoding="utf-8")
    for engine in ("vieneu==", "zerotts=="):
        if engine not in tts:
            errors.append(f"requirements-tts.txt thiếu pin {engine}")
    if not any(rel.startswith("assets/sfx/") and rel.endswith(".ogg") for rel in files):
        errors.append("assets/sfx không có file .ogg")
    if "assets/sfx/License.txt" not in files:
        errors.append("thiếu assets/sfx/License.txt")
    return errors


def write_zip(target, entries, top):
    """entries: [(đường dẫn nguồn, đường dẫn trong zip tính từ thư mục gốc skill)]."""
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, arc in entries:
            info = zipfile.ZipInfo.from_file(path, f"{top}/{arc}")
            info.compress_type = zipfile.ZIP_DEFLATED
            executable = path.suffix == ".sh" or bool(path.stat().st_mode & 0o100)
            info.external_attr = (0o755 if executable else 0o644) << 16
            data = path.read_bytes()
            if path.suffix in (".bat", ".sh"):  # .bat cần CRLF để `call :nhãn` chạy đúng; .sh cần LF
                data = data.replace(b"\r\n", b"\n")
                data = data.replace(b"\n", b"\r\n") if path.suffix == ".bat" else data
            archive.writestr(info, data)


def verify_pack(target):
    """Giải nén vào thư mục có dấu cách; kiểm chạy được --check và biên dịch được toàn bộ .py."""
    with tempfile.TemporaryDirectory(prefix="ags pack ") as tmp:
        with zipfile.ZipFile(target) as archive:
            archive.extractall(tmp)
        skill = Path(tmp) / PACK_NAME
        if not (skill / "SKILL.md").is_file():
            raise SystemExit("❌ Giải nén xong không thấy SKILL.md ở gốc thư mục skill")
        if not compileall.compile_dir(str(skill), quiet=1, force=True, legacy=False):
            raise SystemExit("❌ Có file .py không biên dịch được")
        proc = subprocess.run([sys.executable, str(skill / "scripts" / "ags_setup.py"), "--check"],
                              capture_output=True, text=True, encoding="utf-8")
        report = json.loads(proc.stdout)
        if Path(report["skill_dir"]).resolve() != skill.resolve() or report["venv"]["healthy"]:
            raise SystemExit("❌ --check trả đường dẫn sai hoặc thấy venv lạ trong bản giải nén")
        if len(report["sfx_files"]) < 1:
            raise SystemExit("❌ --check không thấy SFX trong bản giải nén")


def build():
    skills = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())
    errors = check_skill(ROOT / "SKILL.md", PACK_NAME) + check_skill(WEB_SOURCE / "SKILL.md", WEB_NAME)
    errors += [e for folder in skills for e in check_skill(folder / "SKILL.md", folder.name)]
    files = collect(TOP_DIRS, TOP_FILES)
    errors += validate(files)
    if errors:
        sys.exit("❌ Chưa đóng gói được:\n  - " + "\n  - ".join(errors))
    DIST.mkdir(exist_ok=True)
    pack = DIST / f"{PACK_NAME}.zip"
    web = DIST / f"{WEB_NAME}.zip"
    for stale in DIST.glob("*.zip"):
        if stale not in (pack, web):
            stale.unlink()  # zip kiểu cũ (từng skill riêng lẻ) — không còn được hỗ trợ
    write_zip(pack, [(path, rel) for rel, path in sorted(files.items())], PACK_NAME)
    web_entries = [(path, path.relative_to(WEB_SOURCE).as_posix()) for path in sorted(WEB_SOURCE.rglob("*"))
                   if path.is_file() and not (SKIP_PARTS & set(path.relative_to(WEB_SOURCE).parts))]
    web_entries += [(ROOT / rel, rel) for rel in ("LICENSE", "LICENSE-VI.md", "THIRD_PARTY_NOTICES.md",
                                                   "harness/QUY-TRINH-KIEM-DINH.md",
                                                   "skills/ags-clip-shorts/references/chon-doan-short.md")]
    write_zip(web, web_entries, WEB_NAME)
    verify_pack(pack)
    report = [{"zip": str(p), "files": n, "bytes": p.stat().st_size,
               "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
              for p, n in ((pack, len(files)), (web, len(web_entries)))]
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""
AGS (Agent Space) — đóng gói từng skill trong skills/ thành file zip để tải lên claude.ai (Customize → Skills → Upload).

Mỗi zip chứa chính thư mục skill ở cấp cao nhất (<tên-skill>/SKILL.md — claude.ai chỉ nhận cấu trúc này), kèm:
references/ của skill, các script mà SKILL.md gọi (quét import để lấy đủ module phụ), harness/, requirements.txt,
LICENSE, LICENSE-VI.md, THIRD_PARTY_NOTICES.md. Lệnh trong SKILL.md vẫn chạy được vì scripts/ và harness/ nằm ngay trong
thư mục skill.
Trước khi đóng gói, kiểm frontmatter theo Agent Skills spec (https://agentskills.io/specification): name 1–64 ký tự
[a-z0-9-], khớp tên thư mục, không có '--', không bắt đầu/kết thúc bằng '-'; description 1–1024 ký tự; compatibility
tối đa 500 ký tự; SKILL.md dưới 500 dòng.

Chạy:  python scripts/ags_build_skill_zips.py   → dist/<tên-skill>.zip (dist/ không commit).
Zip chỉ để tải lên tài khoản của chính bạn — giấy phép không cho phân phối lại.
"""

import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
ALWAYS = ["harness/ags_anti_slop_guard.py", "harness/QUY-TRINH-KIEM-DINH.md", "requirements.txt",
          "LICENSE", "LICENSE-VI.md", "THIRD_PARTY_NOTICES.md"]
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SCRIPT_RE = re.compile(r"\b((?:scripts|harness)/[\w/-]+\.py)\b")
IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(ags_\w+|bds)\b", re.MULTILINE)


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


def check_skill(folder):
    text = (folder / "SKILL.md").read_text(encoding="utf-8")
    meta = frontmatter(text)
    if meta is None:
        return [f"{folder.name}: SKILL.md thiếu frontmatter YAML"]
    name, desc = meta.get("name", ""), meta.get("description", "")
    errors = []
    if not (1 <= len(name) <= 64 and NAME_RE.match(name)) or name != folder.name:
        errors.append(f"{folder.name}: name '{name}' sai quy tắc hoặc khác tên thư mục")
    if not 1 <= len(desc) <= 1024:
        errors.append(f"{folder.name}: description dài {len(desc)} ký tự (cần 1–1024)")
    if len(meta.get("compatibility", "")) > 500:
        errors.append(f"{folder.name}: compatibility dài hơn 500 ký tự")
    if len(text.splitlines()) >= 500:
        errors.append(f"{folder.name}: SKILL.md phải dưới 500 dòng")
    return errors


def bundled_files(folder):
    """Đường dẫn (tính từ gốc repo) của mọi file chạy cần kèm theo skill."""
    docs = [folder / "SKILL.md", *sorted((folder / "references").glob("*.md"))]
    pending = {m for doc in docs for m in SCRIPT_RE.findall(doc.read_text(encoding="utf-8"))}
    pending.update(ALWAYS)
    files = set()
    while pending:
        rel = pending.pop()
        if rel in files or not (ROOT / rel).is_file():
            continue
        files.add(rel)
        if rel.endswith(".py"):
            for module in IMPORT_RE.findall((ROOT / rel).read_text(encoding="utf-8")):
                if module == "bds":
                    pending.update(p.relative_to(ROOT).as_posix() for p in (ROOT / "scripts" / "bds").iterdir()
                                   if p.suffix in (".py", ".json"))
                else:
                    pending.add(f"scripts/{module}.py")
    return sorted(files)


def build():
    skills = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())
    errors = [e for folder in skills for e in check_skill(folder)]
    if errors:
        sys.exit("❌ Skill chưa đúng Agent Skills spec:\n  - " + "\n  - ".join(errors))
    DIST.mkdir(exist_ok=True)
    report = []
    for folder in skills:
        target = DIST / f"{folder.name}.zip"
        entries = [(p, p.relative_to(folder).as_posix()) for p in sorted(folder.rglob("*"))
                   if p.is_file() and "__pycache__" not in p.parts]
        entries += [(ROOT / rel, rel) for rel in bundled_files(folder)]
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, arc in entries:
                zf.write(path, f"{folder.name}/{arc}")
        report.append({"zip": str(target), "files": len(entries), "bytes": target.stat().st_size})
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    build()

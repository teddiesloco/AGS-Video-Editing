#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing — cài môi trường cho chính thư mục skill này (chỉ dùng thư viện chuẩn của Python).

  python scripts/ags_setup.py                 cài đầy đủ: lõi + MCP + cả hai giọng đọc cục bộ (VieNeu, ZeroTTS) + SFX
  python scripts/ags_setup.py --core          chỉ lõi + MCP + SFX (không cài thư viện TTS)
  python scripts/ags_setup.py --check         chỉ kiểm tra, không đổi gì; in JSON (exit 0 khi lõi sẵn sàng)
  python scripts/ags_setup.py --warmup-tts    tải trước model TTS (~2,7 GB tổng, cần Internet) ngoài client MCP
  python scripts/ags_setup.py --print-mcp     in cấu hình MCP với đường dẫn tuyệt đối cho từng client
  python scripts/ags_setup.py --register-claude-code   đăng ký MCP `ags` ở phạm vi user của Claude Code
  python scripts/ags_setup.py --machine-id     in mã máy để xin mã kích hoạt bản quyền
  python scripts/ags_setup.py --activate <TOKEN>   kích hoạt bản quyền trên máy này (~/.ags/client_license.json)
  python scripts/ags_setup.py --license-status     trạng thái bản quyền (JSON; exit 0 khi hợp lệ)

Môi trường ảo nằm trong <thư mục skill>/venv; không động đến pip toàn cục. Mọi đường dẫn suy từ vị trí file này nên thư
mục skill có dấu cách vẫn chạy được. Di chuyển/đổi tên thư mục skill thì chạy lại lệnh này (venv và cấu hình MCP chứa
đường dẫn tuyệt đối). Exit: 0 xong · 2 cài xong nhưng kiểm tra lỗi · 3 thiếu điều kiện tiên quyết (Python/FFmpeg).
"""
import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / "venv"
IS_WIN = sys.platform == "win32"
SUPPORTED = ((3, 11), (3, 12))  # 3.11 là bản đã chạy thật; 3.12 cho phép nhưng chưa kiểm chứng
CORE_MODULES = ["numpy", "PIL", "cv2", "faster_whisper", "rembg", "onnxruntime", "mcp"]
TTS_MODULES = ["vieneu", "zerotts"]
FFMPEG_HELP = {
    "darwin": "brew install ffmpeg",
    "win32": "winget install -e --id Gyan.FFmpeg   (rồi mở terminal mới để PATH cập nhật)",
    "linux": "sudo apt install ffmpeg   (hoặc trình quản lý gói của bản phân phối)",
}
PYTHON_HELP = {
    "darwin": "brew install python@3.11   (hoặc: uv python install 3.11)",
    "win32": "winget install -e --id Python.Python.3.11",
    "linux": "sudo apt install python3.11 python3.11-venv   (hoặc: uv python install 3.11)",
}


def venv_python():
    return VENV / ("Scripts/python.exe" if IS_WIN else "bin/python")


def run_out(cmd, timeout=60):
    try:
        proc = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc


def probe_venv():
    """Trả về (khỏe?, phiên bản) — venv hỏng/đã dời chỗ/Python gốc đã mất thì cần dựng lại."""
    python = venv_python()
    if not python.exists():
        return False, None
    proc = run_out([python, "-c", "import sys, json; print(json.dumps([sys.prefix, sys.version_info[:2]]))"])
    if proc is None or proc.returncode != 0:
        return False, None
    prefix, version = json.loads(proc.stdout.strip().splitlines()[-1])
    return Path(prefix).resolve() == VENV.resolve(), tuple(version)


def check_ffmpeg():
    report = {"ffmpeg": shutil.which("ffmpeg"), "ffprobe": shutil.which("ffprobe"), "libass": None, "version": None}
    if report["ffmpeg"]:
        proc = run_out([report["ffmpeg"], "-hide_banner", "-version"])
        if proc and proc.returncode == 0:
            report["version"] = proc.stdout.splitlines()[0]
        proc = run_out([report["ffmpeg"], "-hide_banner", "-filters"])
        if proc and proc.returncode == 0:
            report["libass"] = " subtitles " in proc.stdout and " ass " in proc.stdout
    return report


def find_modules(python, modules):
    code = ("import importlib.util, json, sys\n"
            "print(json.dumps({m: importlib.util.find_spec(m) is not None for m in sys.argv[1:]}))")
    proc = run_out([python, "-c", code, *modules])
    if proc is None or proc.returncode != 0:
        return {m: False for m in modules}
    return json.loads(proc.stdout.strip().splitlines()[-1])


def mcp_entry(python):
    return {"type": "stdio", "command": str(python), "args": [str(ROOT / "mcp" / "ags_mcp_server.py")],
            "cwd": str(ROOT)}


def load_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"{path} không phải JSON hợp lệ ({error}); sửa hoặc xoá file rồi chạy lại.")


def write_configs(python):
    """Ghi cấu hình MCP với đường dẫn tuyệt đối thật — không dùng biến ${...} mà client có thể không nạp."""
    written = []
    for path in (ROOT / ".mcp.json", ROOT / ".cursor" / "mcp.json"):
        data = load_json(path)
        data.setdefault("mcpServers", {})["ags"] = mcp_entry(python)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(str(path))
    manifest = ROOT / "gemini-extension.json"
    if manifest.exists():
        data = load_json(manifest)
        interpreter = "${extensionPath}${/}venv${/}" + ("Scripts${/}python.exe" if IS_WIN else "bin${/}python")
        server = data.setdefault("mcpServers", {}).setdefault("ags", {})
        if server.get("command") != interpreter:
            server["command"] = interpreter
            manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            written.append(str(manifest))
    return written


def quote(parts):
    return subprocess.list2cmdline([str(p) for p in parts]) if IS_WIN else shlex.join([str(p) for p in parts])


def print_mcp(python):
    entry = mcp_entry(python)
    server = entry["args"][0]
    block = {"mcpServers": {"ags": {"command": entry["command"], "args": entry["args"]}}}
    print("# Claude Code (user scope, mọi dự án):")
    print(quote(["claude", "mcp", "add", "--transport", "stdio", "--scope", "user", "ags", "--", python, server]))
    print("\n# Antigravity CLI:")
    print(quote(["agy", "mcp", "add", "ags", python, server]))
    print("\n# Claude Desktop (claude_desktop_config.json) · Antigravity (mcp_config.json) · Gemini CLI"
          " (~/.gemini/settings.json, thêm \"timeout\": 1800000) · Cursor (~/.cursor/mcp.json):")
    print(json.dumps(block, ensure_ascii=False, indent=2))
    print("\n# OpenAI Codex (~/.codex/config.toml):")
    print(f"[mcp_servers.ags]\ncommand = {json.dumps(entry['command'])}\nargs = {json.dumps(entry['args'])}\n"
          "tool_timeout_sec = 1800")


def register_claude_code(python):
    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("Không thấy lệnh `claude` trong PATH; dùng `--print-mcp` để lấy lệnh/cấu hình thủ công.")
    server = str(ROOT / "mcp" / "ags_mcp_server.py")
    subprocess.run([claude, "mcp", "remove", "ags", "--scope", "user"], capture_output=True)
    subprocess.run([claude, "mcp", "add", "--transport", "stdio", "--scope", "user", "ags", "--",
                    str(python), server], check=True)
    print("Đã đăng ký MCP `ags` (user scope) cho Claude Code.")


def build_report():
    healthy, version = probe_venv()
    python = venv_python()
    modules = find_modules(python, CORE_MODULES + TTS_MODULES) if healthy else {}
    ffmpeg = check_ffmpeg()
    sfx = sorted(p.name for p in (ROOT / "assets" / "sfx").glob("*.ogg"))
    ready_core = bool(healthy and ffmpeg["ffmpeg"] and ffmpeg["ffprobe"]
                      and all(modules.get(m) for m in CORE_MODULES))
    tts = {m: bool(modules.get(m)) for m in TTS_MODULES}
    next_steps = []
    if not (ffmpeg["ffmpeg"] and ffmpeg["ffprobe"]):
        next_steps.append("Cài FFmpeg: " + FFMPEG_HELP.get(sys.platform, FFMPEG_HELP["linux"]))
    if not ready_core:
        next_steps.append(f'Chạy cài đặt: "{sys.executable}" "{ROOT / "scripts" / "ags_setup.py"}"')
    elif not all(tts.values()):
        next_steps.append("Thiếu thư viện TTS: chạy lại ags_setup.py không kèm --core (cần Internet).")
    return {"skill_dir": str(ROOT), "platform": sys.platform, "running_python": sys.version.split()[0],
            "venv": {"python": str(python), "healthy": healthy,
                     "version": ".".join(map(str, version)) if version else None},
            "ffmpeg": ffmpeg, "modules": modules, "tts_installed": tts, "sfx_files": sfx,
            "mcp_configs": {p: (ROOT / p).exists() for p in (".mcp.json", ".cursor/mcp.json")},
            "ready_core": ready_core, "ready_tts": ready_core and all(tts.values()), "next": next_steps}


def fail_prerequisites(lines):
    print("\n".join(["Thiếu điều kiện tiên quyết:"] + [f" - {line}" for line in lines]), file=sys.stderr)
    print("AGS_SETUP_RESULT " + json.dumps({"ok": False, "missing": lines}, ensure_ascii=False))
    sys.exit(3)


def install(args):
    missing = []
    ffmpeg = check_ffmpeg()
    if not (ffmpeg["ffmpeg"] and ffmpeg["ffprobe"]):
        missing.append("FFmpeg + ffprobe chưa có trong PATH. Cài: " + FFMPEG_HELP.get(sys.platform, FFMPEG_HELP["linux"]))
    healthy, _ = probe_venv()
    if not healthy and sys.version_info[:2] not in SUPPORTED:
        missing.append(f"Python {sys.version.split()[0]} không được hỗ trợ; cần 3.11 (khuyên dùng) hoặc 3.12. Cài: "
                       + PYTHON_HELP.get(sys.platform, PYTHON_HELP["linux"]) + " rồi chạy lại bằng Python đó "
                       "(hoặc dùng CAI-DAT-MAC.sh / CAI-DAT-WIN.bat tự chọn đúng bản)")
    if missing:
        fail_prerequisites(missing)
    if ffmpeg["libass"] is False:
        print("Cảnh báo: FFmpeg này không có bộ lọc ass/subtitles (libass) — phụ đề sẽ không đốt được. "
              "Dùng bản FFmpeg đầy đủ (Homebrew, Gyan.FFmpeg).", file=sys.stderr)
    if not healthy:
        if VENV.exists():
            print(f"venv cũ hỏng hoặc đã dời chỗ — dựng lại: {VENV}", flush=True)
        # Symlink (không copy) trên macOS/Linux: Python tải sẵn của uv/python-build-standalone nạp libpython qua
        # @executable_path/../lib; bản copy trong venv/bin không tìm thấy thư viện và bị dyld giết (SIGABRT).
        try:
            venv.EnvBuilder(with_pip=True, symlinks=not IS_WIN, clear=VENV.exists()).create(VENV)
        except subprocess.CalledProcessError as error:
            message = f"không tạo được venv bằng {sys.executable} (ensurepip thoát {error.returncode}); dùng Python 3.11 khác qua AGS_PYTHON"
            print("AGS_SETUP_RESULT " + json.dumps({"ok": False, "errors": [message]}, ensure_ascii=False))
            sys.exit(2)
        if not probe_venv()[0]:
            message = f"venv tạo xong nhưng {venv_python()} không chạy được; dùng Python 3.11 khác qua AGS_PYTHON"
            print("AGS_SETUP_RESULT " + json.dumps({"ok": False, "errors": [message]}, ensure_ascii=False))
            sys.exit(2)
    python = venv_python()
    env = {**os.environ, "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PYTHONUTF8": "1"}
    env.pop("PIP_REQUIRE_VIRTUALENV", None)
    command = [str(python), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt"),
               "-r", str(ROOT / "requirements-mcp.txt")]
    if not args.core:
        command += ["-r", str(ROOT / "requirements-tts.txt")]
        print("Cài cả hai giọng đọc cục bộ (VieNeu, ZeroTTS). Thư viện ~0,9 GB trong venv; model TTS KHÔNG kèm sẵn — "
              "tải ~2,7 GB từ Hugging Face ở lần dùng đầu (hoặc chạy --warmup-tts). Giấy phép: THIRD_PARTY_NOTICES.md.",
              flush=True)
    if subprocess.run(command, cwd=str(ROOT), env=env).returncode:
        message = "pip install thất bại (xem log phía trên; kiểm tra Internet rồi chạy lại)"
        print("AGS_SETUP_RESULT " + json.dumps({"ok": False, "errors": [message]}, ensure_ascii=False))
        sys.exit(2)
    errors = []
    if subprocess.run([str(python), "-m", "pip", "check"], cwd=str(ROOT), env=env).returncode:
        errors.append("pip check báo xung đột phụ thuộc")
    wanted = CORE_MODULES + ([] if args.core else TTS_MODULES)
    importer = "import importlib, sys\nfor m in sys.argv[1:]:\n    importlib.import_module(m)\n"
    proc = subprocess.run([str(python), "-c", importer, *wanted], cwd=str(ROOT), env=env)
    if proc.returncode:
        errors.append("import thư viện thất bại (xem lỗi phía trên)")
    sfx = subprocess.run([str(python), str(ROOT / "scripts" / "ags_sfx.py"), "list"], cwd=str(ROOT), env=env,
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if sfx.returncode:
        errors.append("ags_sfx.py list lỗi: " + sfx.stderr.strip()[-300:])
    configs = [] if args.no_configs else write_configs(python)
    result = {"ok": not errors, "mode": "core" if args.core else "full", "python": str(python),
              "configs_written": configs, "errors": errors}
    print("AGS_SETUP_RESULT " + json.dumps(result, ensure_ascii=False))
    if errors:
        sys.exit(2)
    print(f"Sẵn sàng: {python}\nMCP: {ROOT / '.mcp.json'} (đã ghi đường dẫn tuyệt đối). Dời thư mục skill thì chạy lại.")


def warmup_tts(python):
    for engine in ("vieneu", "zerotts"):
        print(f"Tải model {engine} (lần đầu, cần Internet)…", flush=True)
        subprocess.run([str(python), str(ROOT / "scripts" / "ags_tts.py"), "voices", "--engine", engine],
                       check=True, cwd=str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--core", action="store_true", help="Không cài thư viện TTS")
    parser.add_argument("--check", action="store_true", help="Chỉ kiểm tra, in JSON")
    parser.add_argument("--yes", action="store_true", help="Chấp nhận mặc định (script không bao giờ hỏi; để tương thích)")
    parser.add_argument("--no-configs", action="store_true", help="Không ghi .mcp.json/.cursor/mcp.json")
    parser.add_argument("--warmup-tts", action="store_true", help="Tải trước model của cả hai engine TTS")
    parser.add_argument("--print-mcp", action="store_true", help="In cấu hình MCP theo từng client")
    parser.add_argument("--register-claude-code", action="store_true", help="Đăng ký MCP ở user scope")
    parser.add_argument("--machine-id", action="store_true", help="In mã máy để xin mã kích hoạt")
    parser.add_argument("--activate", metavar="TOKEN", help="Kích hoạt bản quyền client trên máy này")
    parser.add_argument("--license-status", action="store_true", help="Trạng thái bản quyền client (JSON)")
    args = parser.parse_args()
    if args.machine_id or args.activate or args.license_status:
        import ags_client_license as lic
        if args.machine_id:
            print(lic.get_machine_id())
        if args.activate:
            try:
                print(json.dumps(lic.activate_license_token(args.activate), ensure_ascii=False, indent=2))
            except PermissionError as error:
                raise SystemExit(str(error))
        if args.license_status:
            status = lic.license_status()
            print(json.dumps(status, ensure_ascii=False, indent=2))
            sys.exit(0 if status["valid"] else 1)
        return
    if args.check:
        report = build_report()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(0 if report["ready_core"] else 1)
    if args.print_mcp or args.register_claude_code or args.warmup_tts:
        healthy, _ = probe_venv()
        if not healthy:
            raise SystemExit("Chưa có venv hợp lệ — chạy `ags_setup.py` (không kèm tuỳ chọn) trước.")
        if args.warmup_tts:
            warmup_tts(venv_python())
        if args.print_mcp:
            print_mcp(venv_python())
        if args.register_claude_code:
            register_claude_code(venv_python())
        return
    install(args)


if __name__ == "__main__":
    main()

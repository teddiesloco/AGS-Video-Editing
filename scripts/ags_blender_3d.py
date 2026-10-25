#!/usr/bin/env python3
"""
AGS (Agent Space) — dựng cảnh 3D Blender headless 1080x1920 30fps (FR-ags-anti-rea-shield-002, BR-002).

Preset: blender_3d_bds (lô đất nhô cao + cột mốc #A8FF3E + camera bay quỹ đạo), blender_3d_isometric
(01 INTAKE -> 02 AI CORE -> 03 OUTCOME, đèn studio 3 điểm, camera trượt), blender_3d_product (bục xoay 360°),
auto (chọn theo title).
Dò Blender: BLENDER_BIN -> /Applications/Blender.app -> C:\\Program Files\\Blender Foundation\\Blender*\\blender.exe
(bản mới nhất) -> PATH. Script bpy chỉ lấy qua ags_vault_loader.read_asset("blender/scene_*.py").
mode=auto: thiếu Blender hoặc Blender lỗi -> Canvas 30fps của ags-reels (ghi fallback_reason); mode=blender: báo lỗi.

Chạy:  python scripts/ags_blender_3d.py --preset blender_3d_bds --out canh.mp4 [--seconds 6] [--title "..."] [--mode auto]
"""

import argparse
import glob
import importlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from ags_common import font_path, nfc, run_cmd, safe_box

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
SAMPLES = 16
ENGINES = ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH")
MAC_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
WIN_BLENDER_GLOB = r"C:\Program Files\Blender Foundation\Blender*\blender.exe"
# Preset -> archetype Canvas 30fps tương ứng của ags-reels khi không dựng được bằng Blender.
CANVAS_FALLBACK = {"blender_3d_bds": "property_map", "blender_3d_isometric": "system_isometric",
                   "blender_3d_product": "editorial_grid"}
SCENE_PRESETS = ("auto", *CANVAS_FALLBACK)
BDS_WORDS = ("bất động sản", "bđs", "đất", "lô ", "nhà", "dự án")
PRODUCT_WORDS = ("sản phẩm", "product", "hộp", "chai", "mỹ phẩm")


def find_blender():
    """Đường dẫn Blender chạy được đầu tiên theo thứ tự BR-002, hoặc None."""
    windows = sorted(glob.glob(WIN_BLENDER_GLOB), reverse=True,
                     key=lambda p: tuple(int(n) for n in re.findall(r"\d+", Path(p).parent.name)))
    for cand in (os.environ.get("BLENDER_BIN", "").strip(), MAC_BLENDER, *windows, shutil.which("blender")):
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def resolve_preset(scene_preset, title=""):
    if scene_preset not in SCENE_PRESETS:
        raise ValueError(f"scene_preset '{scene_preset}' không hợp lệ. Cho phép: {list(SCENE_PRESETS)}")
    if scene_preset != "auto":
        return scene_preset
    low = f" {nfc(title).casefold()} "
    if any(w in low for w in BDS_WORDS):
        return "blender_3d_bds"
    if any(w in low for w in PRODUCT_WORDS):
        return "blender_3d_product"
    return "blender_3d_isometric"


def _render_with_blender(blender, preset, out, duration_sec, title):
    from ags_vault_loader import read_asset

    script = read_asset(f"blender/{preset.replace('blender_3d_', 'scene_')}.py")
    frames = max(1, math.ceil(duration_sec * FPS - 1e-6))
    try:
        font = font_path("bold")
    except RuntimeError:
        font = ""
    with tempfile.TemporaryDirectory(prefix="ags_blender_") as tmp:
        args = {"frames_dir": tmp, "frames": frames, "fps": FPS, "width": W, "height": H, "samples": SAMPLES,
                "engines": list(ENGINES), "title": nfc(title).strip()[:48], "font": font,
                "safe_box": list(safe_box(W, H))}
        fd, script_path = tempfile.mkstemp(suffix=".py", dir=tmp)  # 0600, chỉ để Blender đọc
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(script)
            proc = subprocess.run([blender, "--background", "--factory-startup", "--python-exit-code", "1",
                                   "--python", script_path, "--", json.dumps(args)],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace",
                                  timeout=60 + 20 * frames)
        finally:
            os.unlink(script_path)
        pngs = sorted(Path(tmp).glob("f_*.png"))
        if proc.returncode != 0 or len(pngs) != frames:
            last = next((ln for ln in reversed(proc.stderr.splitlines() + proc.stdout.splitlines()) if ln.strip()), "")
            raise RuntimeError(f"Blender thoát mã {proc.returncode}, {len(pngs)}/{frames} khung: {last.strip()[:200]}")
        run_cmd(["ffmpeg", "-nostdin", "-v", "error", "-y", "-framerate", FPS, "-start_number", 1,
                 "-i", Path(tmp) / "f_%04d.png", "-c:v", "libx264", "-preset", "medium", "-crf", 18,
                 "-pix_fmt", "yuv420p", "-vf", "setsar=1", "-r", FPS, "-an", "-movflags", "+faststart", out])


def _render_canvas(preset, out, duration_sec, title):
    reels_dir = os.environ.get("AGS_REELS_DIR") or str(ROOT.parent.parent / "services" / "ops" / "ags-reels-footage")
    if reels_dir not in sys.path:
        sys.path.insert(0, reels_dir)
    render = importlib.import_module("ags_reels_pipeline")._render_procedural_editorial_broll  # bộ dựng cài cạnh gói

    render(0, "", title, title, duration_sec, out, archetype=CANVAS_FALLBACK[preset])


def render_blender_scene(scene_preset: str, out_mp4: str, duration_sec: float = 6.0, title: str = "",
                         mode: str = "auto") -> dict:
    if mode not in ("auto", "blender"):
        raise ValueError(f"mode '{mode}' không hợp lệ (auto | blender)")
    preset = resolve_preset(scene_preset, title)
    out = Path(out_mp4).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    blender = find_blender()
    result = {"engine": "blender", "blender_bin": blender, "scene_preset": preset, "fps": FPS, "size": [W, H],
              "output": str(out), "fallback_reason": None}
    if blender is None:
        reason = "Không tìm thấy Blender (BLENDER_BIN, /Applications/Blender.app, Program Files, PATH)"
        if mode == "blender":
            raise RuntimeError(reason)
    else:
        try:
            _render_with_blender(blender, preset, out, duration_sec, title)
            return result
        except PermissionError:
            raise  # VaultError / bản quyền: không che bằng Canvas
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            if mode == "blender":
                raise
            reason = f"Blender lỗi, chuyển Canvas 30fps: {exc}"
    _render_canvas(preset, out, duration_sec, title)
    result.update(engine="canvas", fallback_reason=reason)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--preset", default="auto", choices=SCENE_PRESETS)
    parser.add_argument("--out", required=True, help="File MP4 đầu ra")
    parser.add_argument("--seconds", type=float, default=6.0)
    parser.add_argument("--title", default="")
    parser.add_argument("--mode", default="auto", choices=("auto", "blender"))
    args = parser.parse_args()
    print(json.dumps(render_blender_scene(args.preset, args.out, args.seconds, args.title, args.mode),
                     ensure_ascii=False))


if __name__ == "__main__":
    main()

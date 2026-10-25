#!/usr/bin/env python3
"""
AGS (Agent Space) — kiểm thử dựng cảnh Blender 3D (scripts/ags_blender_3d.py, AC-ags-anti-rea-shield-004):
thứ tự dò Blender, script bpy chỉ lấy qua ags_vault_loader.read_asset, mode=auto tự về Canvas 30fps khi thiếu hoặc
lỗi Blender, mode=blender báo lỗi. Có Blender thật (BLENDER_BIN/...) thì dựng thật cả 3 preset và soát vùng an toàn.

Chạy:  venv/bin/python -m unittest tests.ags_test_blender -v      (cần FFmpeg trong PATH)
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ags_blender_3d as b3d  # noqa: E402
import ags_vault_loader  # noqa: E402
from ags_common import safe_box  # noqa: E402

# Blender giả: chép script bpy + tham số ra AGS_TEST_CAPTURE rồi ghi đúng số khung PNG như Blender thật.
STUB = """#!/bin/sh
exec "{py}" - "$@" <<'EOF'
import json, os, shutil, subprocess, sys
argv = sys.argv[1:]
script = argv[argv.index("--python") + 1]
args = json.loads(argv[argv.index("--") + 1])
cap = os.environ["AGS_TEST_CAPTURE"]
shutil.copy(script, cap + ".py")
with open(cap + ".json", "w") as fh:
    json.dump({{"argv": argv, "args": args, "mode": os.stat(script).st_mode & 0o777}}, fh)
subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                "color=c=0x1F6F3D:s={{}}x{{}}:r={{}}".format(args["width"], args["height"], args["fps"]),
                "-frames:v", str(args["frames"]), os.path.join(args["frames_dir"], "f_%04d.png")], check=True)
EOF
"""


def probe(mp4):
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=width,height,r_frame_rate,pix_fmt", "-of", "csv=p=0", str(mp4)],
                          capture_output=True, text=True, check=True).stdout.strip()


def executable(path, body="#!/bin/sh\nexit 0\n"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    path.chmod(0o755)
    return str(path)


class TestAgsBlender3D(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ags_test_blender_")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def no_blender(self):
        return patch.multiple(b3d, MAC_BLENDER=str(self.tmp / "none" / "Blender"),
                              WIN_BLENDER_GLOB=str(self.tmp / "none" / "Blender*" / "blender.exe"))

    def test_discovery_order(self):
        env_bin = executable(self.tmp / "env" / "blender")
        mac_bin = executable(self.tmp / "mac" / "Blender")
        for ver in ("4.5", "5.10", "5.2"):
            executable(self.tmp / "win" / f"Blender {ver}" / "blender.exe")
        path_bin = executable(self.tmp / "path" / "blender")
        not_exec = self.tmp / "env" / "plain"
        not_exec.write_text("")
        win_glob = str(self.tmp / "win" / "Blender*" / "blender.exe")
        with patch.dict(os.environ, {"BLENDER_BIN": env_bin, "PATH": str(self.tmp / "path")}), \
                patch.multiple(b3d, MAC_BLENDER=mac_bin, WIN_BLENDER_GLOB=win_glob):
            self.assertEqual(b3d.find_blender(), env_bin)
            os.environ["BLENDER_BIN"] = str(not_exec)  # BLENDER_BIN hỏng: bỏ qua, dò tiếp
            self.assertEqual(b3d.find_blender(), mac_bin)
            b3d.MAC_BLENDER = str(self.tmp / "mac" / "missing")
            self.assertEqual(b3d.find_blender(), str(self.tmp / "win" / "Blender 5.10" / "blender.exe"))
            b3d.WIN_BLENDER_GLOB = str(self.tmp / "none" / "Blender*" / "blender.exe")
            self.assertEqual(b3d.find_blender(), path_bin)
            os.environ["PATH"] = str(self.tmp / "empty")
            self.assertIsNone(b3d.find_blender())

    def test_missing_blender_auto_falls_back_to_canvas_and_blender_mode_raises(self):
        out = self.tmp / "canvas.mp4"
        with patch.dict(os.environ, {"BLENDER_BIN": ""}), self.no_blender(), patch("shutil.which", return_value=None):
            with self.assertRaises(RuntimeError):
                b3d.render_blender_scene("blender_3d_bds", str(self.tmp / "x.mp4"), 1.0, mode="blender")
            self.assertFalse((self.tmp / "x.mp4").exists())
            res = b3d.render_blender_scene("blender_3d_bds", str(out), 1.0, title="Đất nền 120m²")
        self.assertEqual((res["engine"], res["blender_bin"], res["scene_preset"]), ("canvas", None, "blender_3d_bds"))
        self.assertIn("Blender", res["fallback_reason"])
        self.assertEqual((res["fps"], res["size"], res["output"]), (30, [1080, 1920], str(out)))
        self.assertEqual(probe(out), "1080,1920,yuv420p,30/1")

    def test_bpy_script_comes_only_from_read_asset(self):
        stub = executable(self.tmp / "bin" / "blender", STUB.format(py=sys.executable))
        cap = self.tmp / "cap"
        out = self.tmp / "iso.mp4"
        asked = []

        def fake_read_asset(relpath):
            asked.append(relpath)
            return b"# AGS_VAULT_SENTINEL\n"

        with patch.dict(os.environ, {"BLENDER_BIN": stub, "AGS_TEST_CAPTURE": str(cap)}), \
                patch.object(ags_vault_loader, "read_asset", fake_read_asset):
            res = b3d.render_blender_scene("blender_3d_isometric", str(out), 1.0, mode="blender")
        self.assertEqual(asked, ["blender/scene_isometric.py"])
        self.assertEqual(Path(f"{cap}.py").read_bytes(), b"# AGS_VAULT_SENTINEL\n")
        run = json.loads(Path(f"{cap}.json").read_text())
        script_path = run["argv"][run["argv"].index("--python") + 1]
        self.assertEqual(run["mode"], 0o600)
        self.assertFalse(Path(script_path).exists(), "script bpy tạm phải bị xoá ngay sau khi Blender chạy")
        self.assertIn("--background", run["argv"])
        self.assertEqual(run["args"]["engines"], ["BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"])
        self.assertEqual((run["args"]["frames"], run["args"]["fps"]), (30, 30))
        self.assertEqual(run["args"]["safe_box"], list(safe_box(1080, 1920)))
        self.assertEqual((res["engine"], res["blender_bin"], res["fallback_reason"]), ("blender", stub, None))
        self.assertEqual(probe(out), "1080,1920,yuv420p,30/1")

    def test_blender_crash_auto_falls_back_blender_mode_raises(self):
        crash = executable(self.tmp / "bin" / "blender", "#!/bin/sh\necho 'Error: GPU init failed' >&2\nexit 1\n")
        with patch.dict(os.environ, {"BLENDER_BIN": crash}):
            with self.assertRaises(RuntimeError):
                b3d.render_blender_scene("blender_3d_product", str(self.tmp / "x.mp4"), 1.0, mode="blender")
            res = b3d.render_blender_scene("blender_3d_product", str(self.tmp / "p.mp4"), 1.0)
        self.assertEqual((res["engine"], res["blender_bin"]), ("canvas", crash))
        self.assertIn("GPU init failed", res["fallback_reason"])
        self.assertEqual(probe(self.tmp / "p.mp4"), "1080,1920,yuv420p,30/1")

    def test_license_error_is_not_hidden_by_canvas_fallback(self):
        stub = executable(self.tmp / "bin" / "blender", STUB.format(py=sys.executable))

        def locked(_relpath):
            raise ags_vault_loader.VaultError("CLIENT_LICENSE_REQUIRED — thử")

        out = self.tmp / "khoa.mp4"
        with patch.dict(os.environ, {"BLENDER_BIN": stub}), patch.object(ags_vault_loader, "read_asset", locked):
            with self.assertRaises(ags_vault_loader.VaultError):
                b3d.render_blender_scene("blender_3d_bds", str(out), 1.0)  # mode=auto vẫn báo lỗi bản quyền
        self.assertFalse(out.exists())

    @unittest.skipIf(b3d.find_blender() is None, "chưa có Blender thật (BLENDER_BIN / Blender.app / PATH)")
    def test_real_blender_renders_each_preset_inside_safe_zone(self):
        x0, y0, x1, y1 = safe_box(1080, 1920)
        with patch.object(b3d, "SAMPLES", 4):
            for preset in ("blender_3d_bds", "blender_3d_isometric", "blender_3d_product"):
                out = self.tmp / f"{preset}.mp4"
                res = b3d.render_blender_scene(preset, str(out), 1.0, title="Đất nền Phú Quốc 120m²", mode="blender")
                self.assertEqual(res["engine"], "blender")
                self.assertEqual(probe(out), "1080,1920,yuv420p,30/1")
                raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out), "-vf", "select='not(mod(n,10))'",
                                      "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                     capture_output=True, check=True).stdout
                for frame in np.frombuffer(raw, np.uint8).reshape(-1, 1920, 1080, 3).astype(int):
                    ys, xs = np.nonzero(np.abs(frame - frame[4, 4]).sum(-1) > 30)
                    self.assertTrue(len(xs) > 5000, f"{preset}: khung trống")
                    self.assertTrue(x0 <= xs.min() and xs.max() <= x1 and y0 <= ys.min() and ys.max() <= y1,
                                    (preset, xs.min(), xs.max(), ys.min(), ys.max()))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
AGS (Agent Space) — kiểm thử `ags_setup.py --install-all-clients` trên HOME giả: gộp cấu hình 4 client (Antigravity/Gemini,
Claude Code, Codex, Cursor) không mất MCP có sẵn, chạy lại không đổi gì, skill `ags-studio` tới đủ 4 client, JSON hỏng →
E-ags-anti-rea-shield-001 mà client khác vẫn cài, --activate ghi bản quyền 0600 dưới --home.

Chạy:  venv/bin/python -m unittest tests.ags_test_installer -v      (cần venv đã cài)
"""

import contextlib
import io
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETUP = ROOT / "scripts" / "ags_setup.py"
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

import ags_client_license as lic  # noqa: E402
import ags_setup  # noqa: E402

try:
    import tomllib
except ImportError:
    tomllib = None

OURS = ("ags", "ags-auto-editor", "ags-reels")
FOREIGN = {"command": "/usr/bin/true", "args": ["--khach"]}
JSON_CONFIGS = {"antigravity": ".gemini/config/mcp_config.json", "claude": ".claude.json", "cursor": ".cursor/mcp.json"}
CODEX_SEED = ('model = "gpt-5"\n\n# máy chủ riêng của khách\n[mcp_servers.khach]\ncommand = "/usr/bin/true"\n'
              'args = ["--khach"]\n\n[mcp_servers.khach.env]\nTOKEN_KHACH = "giu-nguyen"\n')


def run_setup(home, *extra):
    proc = subprocess.run([sys.executable, str(SETUP), "--install-all-clients", "--home", str(home), *extra],
                          capture_output=True, text=True, encoding="utf-8")
    line = next(x for x in proc.stdout.splitlines() if x.startswith("AGS_SETUP_RESULT "))
    return proc, json.loads(line.split(" ", 1)[1])


def seed(home):
    for rel in JSON_CONFIGS.values():
        path = home / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"numStartups": 7, "mcpServers": {"khach": FOREIGN}}), encoding="utf-8")
    (home / ".codex").mkdir()
    (home / ".codex" / "config.toml").write_text(CODEX_SEED, encoding="utf-8")


def snapshot(home):
    return {p.relative_to(home).as_posix(): p.read_bytes() for p in sorted(home.rglob("*")) if p.is_file()}


class InstallAllClientsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="ags home ")  # dấu cách trong đường dẫn là cố ý
        self.home = Path(self._tmp.name).resolve()  # macOS: /var → /private/var, installer ghi đường dẫn đã resolve

    def tearDown(self):
        self._tmp.cleanup()

    def assert_our_server(self, entry):
        for path in (entry["command"], entry["args"][0]):
            self.assertTrue(Path(path).is_absolute() and Path(path).exists(), path)
            self.assertNotIn("$", path)

    def test_merges_four_clients_keeps_foreign_servers_and_rerun_is_noop(self):
        seed(self.home)
        original_claude = (self.home / ".claude.json").read_bytes()
        proc, result = run_setup(self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(set(result["targets"]), {"antigravity", "claude", "codex", "cursor"})
        for target, rel in JSON_CONFIGS.items():
            data = json.loads((self.home / rel).read_text(encoding="utf-8"))
            self.assertEqual(data["numStartups"], 7, target)
            self.assertEqual(data["mcpServers"]["khach"], FOREIGN, target)
            for name in OURS:
                self.assert_our_server(data["mcpServers"][name])
        self.assertEqual((self.home / ".claude.json.bak").read_bytes(), original_claude)

        codex_text = (self.home / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertTrue(codex_text.startswith(CODEX_SEED.rstrip("\n")), codex_text)
        if tomllib:
            codex = tomllib.loads(codex_text)
            self.assertEqual(codex["model"], "gpt-5")
            self.assertEqual(codex["mcp_servers"]["khach"]["env"], {"TOKEN_KHACH": "giu-nguyen"})
            for name in OURS:
                self.assert_our_server(codex["mcp_servers"][name])

        self.assertTrue({"ags-video-editing", "ags-auto-editor", "ags-reels-footage", "ags-edit-bds"} <= set(result["skills"]))
        for skills_dir in (".claude/skills", ".codex/skills", ".gemini/config/skills", ".gemini/antigravity-cli/skills"):
            self.assertEqual(sorted(p.name for p in (self.home / skills_dir).iterdir()), result["skills"], skills_dir)
            skill = (self.home / skills_dir / "ags-edit-bds" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(f"SKILL_DIR thật: `{ROOT}`", skill)
        extension = json.loads((self.home / ".gemini/extensions/ags-video-editing/gemini-extension.json").read_text("utf-8"))
        for name in OURS:
            self.assert_our_server(extension["mcpServers"][name])
        self.assertTrue((self.home / ".cursor/rules/ags-video-editing.mdc").read_text("utf-8").startswith("---\n"))
        self.assertIn("<!-- AGS:BEGIN -->", (self.home / ".codex/AGENTS.md").read_text("utf-8"))

        before = snapshot(self.home)
        proc, again = run_setup(self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual([t["changed"] for t in again["targets"].values()], [[]] * 4)

    def test_studio_skill_reaches_all_four_clients(self):
        proc, result = run_setup(self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ags-studio", result["skills"])
        self.assertTrue((ROOT / "scripts" / "ags_studio.py").is_file(), "skill trỏ tới lệnh phải có trong gói")
        # Cursor nạp thêm ~/.claude/skills và ~/.codex/skills (cursor.com/docs/skills, mục tương thích) + rule trỏ tới skill.
        for skills_dir in (".claude/skills", ".codex/skills", ".gemini/config/skills", ".gemini/antigravity-cli/skills"):
            skill = (self.home / skills_dir / "ags-studio" / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(skill.startswith("---\nname: ags-studio\n"), skills_dir)
            self.assertIn(f"SKILL_DIR thật: `{ROOT}`", skill)
            self.assertIn("scripts/ags_studio.py", skill)
        self.assertIn("skills/ags-studio/SKILL.md", (self.home / ".cursor/rules/ags-video-editing.mdc").read_text("utf-8"))
        extension_guide = (self.home / ".gemini/extensions/ags-video-editing/AGENTS.md").read_text("utf-8")
        self.assertIn("skills/ags-studio/SKILL.md", extension_guide)

    def test_marketing_skill_reaches_host_discovery_roots(self):
        proc, result = run_setup(self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ags-marketing-editor", result["skills"])
        for root in (".claude/skills", ".codex/skills", ".gemini/config/skills", ".gemini/antigravity-cli/skills"):
            skill = (self.home / root / "ags-marketing-editor" / "SKILL.md").read_text("utf-8")
            self.assertTrue(skill.startswith("---\nname: ags-marketing-editor\n"), root)
            frontmatter = skill.split("---", 2)[1]
            self.assertNotIn("\ncompatibility:", frontmatter, root)
            self.assertIn("scripts/ags_marketing_editor.py", skill)
            self.assertIn(f"SKILL_DIR thật: `{ROOT}`", skill)

    def test_corrupt_claude_json_fails_with_code_while_other_clients_install(self):
        seed(self.home)
        (self.home / ".claude.json").write_text("{khong phai json", encoding="utf-8")
        proc, result = run_setup(self.home)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("E-ags-anti-rea-shield-001", proc.stderr)
        self.assertIn(str(self.home / ".claude.json"), result["targets"]["claude"]["error"])
        self.assertFalse(result["targets"]["claude"]["ok"])
        self.assertEqual((self.home / ".claude.json").read_text(encoding="utf-8"), "{khong phai json")
        for target in ("antigravity", "codex", "cursor"):
            self.assertTrue(result["targets"][target]["ok"], target)
        for name in OURS:
            self.assert_our_server(json.loads((self.home / ".cursor/mcp.json").read_text("utf-8"))["mcpServers"][name])

    def test_activate_writes_0600_license_under_home(self):
        from ags_test_core import _test_prime  # khoá thử sinh tại chỗ, không dùng khoá ký thật

        rng = random.Random(2410)
        while True:
            p, q = _test_prime(512, rng), _test_prime(512, rng)
            phi = (p - 1) * (q - 1)
            if p != q and phi % lic.PUBLIC_E:
                break
        n, d = p * q, pow(lic.PUBLIC_E, -1, phi)
        key = self.home / "issuer_test_key.json"
        key.write_text(json.dumps({"e": lic.PUBLIC_E, "n_hex": f"{n:x}", "d_hex": f"{d:x}"}), encoding="utf-8")
        saved_env, real_n, argv = os.environ.get("AGS_CLIENT_LICENSE_PATH"), lic.PUBLIC_N, sys.argv
        lic.PUBLIC_N = n
        try:
            token = lic.issue_license_token("khach-thu", mid=lic.get_machine_id(), days=30, issuer_key_path=key)
            sys.argv = [str(SETUP), "--install-all-clients", "--home", str(self.home), "--targets", "cursor",
                        "--activate", token]
            out = io.StringIO()
            with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as exit_info:
                ags_setup.main()
        finally:
            lic.PUBLIC_N, sys.argv = real_n, argv
            os.environ.pop("AGS_CLIENT_LICENSE_PATH", None)
            if saved_env is not None:
                os.environ["AGS_CLIENT_LICENSE_PATH"] = saved_env
        result = json.loads(next(x for x in out.getvalue().splitlines() if x.startswith("AGS_SETUP_RESULT ")).split(" ", 1)[1])
        license_file = self.home / ".ags" / "client_license.json"
        self.assertEqual(result["license"]["path"], str(license_file))
        self.assertEqual(result["license"]["payload"]["sub"], "khach-thu")
        self.assertTrue(license_file.stat().st_mode & 0o777 == 0o600 or sys.platform == "win32")
        self.assertTrue(result["targets"]["cursor"]["ok"])
        if not (ROOT / "assets" / "vault.ags.enc").exists():
            self.assertFalse(result["vault"]["checked"])
            self.assertEqual(exit_info.exception.code, 0)


if __name__ == "__main__":
    unittest.main()

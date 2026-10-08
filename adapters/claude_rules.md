# ⚡ AGS Video Editing — Claude Code & Desktop Harness

Hướng dẫn vận hành dành cho Claude Code / Claude Desktop:

1. **Nhận diện Slash Commands:**
   - `/ags-edit-az <video>`: Tự động chạy `python scripts/cut_silence.py`
   - `/ags-edit-hook <video> --text "<HOOK>"`: Tự động chạy `python scripts/text_behind_person.py`
   - `/ags-edit-editorial <video>`: Tự động chạy `python scripts/editorial_sub.py`
   - `/ags-voice-kinetic <audio>`: Tự động chạy `python scripts/voice_to_kinetic.py`
   - `/ags-voice-doodle <audio>`: Tự động chạy `python scripts/voice_to_doodle.py`

2. **Quality Gate:**
   - Luôn chạy kèm `python harness/anti_slop_guard.py <out.mp4>` sau render để thẩm định độ đồng bộ âm thanh và âm lượng -14 LUFS.

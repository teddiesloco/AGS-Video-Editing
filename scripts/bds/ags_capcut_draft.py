"""
AGS (Agent Space) — sinh draft CapCut desktop (thử nghiệm)

Draft gồm 3 file trong 1 thư mục:
- draft_info.json     : timeline (tên file CapCut macOS đọc)
- draft_content.json  : cùng nội dung (tên file CapCut Windows đọc)
- draft_meta_info.json: thông tin thư mục, danh sách media
Khung trường lấy từ ags_capcut_template.json (bộ key + giá trị mặc định quan sát từ draft CapCut thật,
version 360000). Thời gian tính bằng micro-giây. Không bao giờ ghi đè thư mục đã tồn tại.
"""

import copy
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from ags_common import nfc, run_cmd

TEMPLATE = json.loads(Path(__file__).with_name("ags_capcut_template.json").read_text(encoding="utf-8"))
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
PHOTO_DURATION_US = 10_800_000_000  # CapCut ghi ảnh tĩnh là 3 giờ
DEFAULT_PHOTO_SECONDS = 3.0


def capcut_drafts_dir() -> Path:
    """Thư mục draft mặc định của CapCut desktop."""
    if sys.platform == "darwin":
        return Path.home() / "Movies" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
    if os.name == "nt":
        return Path(os.environ["LOCALAPPDATA"]) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
    raise RuntimeError("CapCut desktop chỉ có trên macOS và Windows; hãy dùng --out để ghi draft ra thư mục khác.")


def _id() -> str:
    return str(uuid.uuid4()).upper()


def _us(seconds: float) -> int:
    return int(round(seconds * 1_000_000))


def _new(kind: str, **values):
    obj = copy.deepcopy(TEMPLATE[kind])
    obj.update(values)
    return obj


def _hex_to_rgb_float(color: str) -> List[float]:
    color = color.lstrip("#")
    return [round(int(color[i:i + 2], 16) / 255, 4) for i in (0, 2, 4)]


def _capcut_default_font() -> str:
    """Font hệ thống CapCut dùng cho chữ mặc định (rỗng nếu không tìm thấy)."""
    mac = Path("/Applications/CapCut.app/Contents/Resources/Font/SystemFont/en.ttf")
    if mac.exists():
        return mac.as_posix()
    local = os.environ.get("LOCALAPPDATA")
    if local:
        hits = sorted(Path(local, "CapCut", "Apps").glob("*/Resources/Font/SystemFont/en.ttf"))
        if hits:
            return hits[-1].as_posix()
    return ""


def probe_media(path: Path) -> Dict[str, object]:
    """Thông số thật của file: kiểu, thời lượng (us), kích thước, có tiếng hay không."""
    if path.suffix.lower() in PHOTO_EXTS:
        from PIL import Image
        with Image.open(path) as im:
            width, height = im.size
        return {"kind": "photo", "duration_us": PHOTO_DURATION_US, "width": width, "height": height, "has_audio": False}
    info = json.loads(run_cmd(["ffprobe", "-v", "error", "-show_entries",
                               "format=duration:stream=codec_type,width,height", "-of", "json", path]).stdout)
    video = next((s for s in info["streams"] if s.get("codec_type") == "video"), None)
    return {
        "kind": "video" if video else "audio",
        "duration_us": _us(float(info["format"]["duration"])),
        "width": video["width"] if video else 0,
        "height": video["height"] if video else 0,
        "has_audio": any(s.get("codec_type") == "audio" for s in info["streams"]),
    }


class AgsCapCutDraft:
    def __init__(self, name: str, width: int = 1080, height: int = 1920, fps: int = 30):
        if not name or any(c in name for c in '/\\:') or name in (".", ".."):
            raise ValueError("Tên draft không được rỗng hoặc chứa / \\ :")
        self.name = name
        ratio = "9:16" if (width, height) == (1080, 1920) else ("16:9" if (width, height) == (1920, 1080) else "original")
        self.draft = _new("draft", id=_id(), fps=float(fps),
                          canvas_config={"background": None, "height": height, "ratio": ratio, "width": width})
        self.platform = {"os": "mac" if sys.platform == "darwin" else ("windows" if os.name == "nt" else sys.platform)}
        self.draft["platform"].update(self.platform)
        self.draft["last_modified_platform"].update(self.platform)
        self.media: List[Dict[str, object]] = []  # cho draft_meta_info.json

    # ---- nội bộ -------------------------------------------------------------
    def _track(self, kind: str) -> Dict[str, object]:
        for track in self.draft["tracks"]:
            if track["type"] == kind:
                return track
        track = _new("track", id=_id(), type=kind)
        self.draft["tracks"].append(track)
        return track

    def _material(self, group: str, kind: str, **values) -> str:
        obj = _new(kind, id=_id(), **values)
        self.draft["materials"][group].append(obj)
        return obj["id"]

    def _segment(self, kind: str, material_id: str, refs: List[str], start_us: int, duration_us: int,
                 source_start_us: Optional[int], **values) -> str:
        track = self._track(kind)
        seg = _new(
            "segment", id=_id(), material_id=material_id, extra_material_refs=refs,
            target_timerange={"duration": duration_us, "start": start_us},
            source_timerange=None if source_start_us is None else {"duration": duration_us, "start": source_start_us},
            track_render_index=self.draft["tracks"].index(track), **values,
        )
        track["segments"].append(seg)
        self.draft["duration"] = max(self.draft["duration"], start_us + duration_us)
        return seg["id"]

    def _common_refs(self) -> List[str]:
        return [
            self._material("speeds", "speed", speed=1.0),
            self._material("placeholder_infos", "placeholder_info"),
            self._material("sound_channel_mappings", "sound_channel_mapping"),
            self._material("vocal_separations", "vocal_separation"),
        ]

    def _register_media(self, path: Path, info: Dict[str, object], bucket: int, metetype: str) -> None:
        now = time.time()
        self.media.append({"bucket": bucket, "entry": _new(
            "meta_media", id=str(uuid.uuid4()), file_Path=path.as_posix(), extra_info=path.name,
            metetype=metetype, duration=info["duration_us"], width=info["width"], height=info["height"],
            create_time=int(now), import_time=int(now), import_time_ms=int(now * 1_000_000),
            roughcut_time_range={"duration": info["duration_us"], "start": 0}, type=bucket,
        )})

    def track_end(self, kind: str) -> float:
        """Điểm kết thúc (giây) của track loại `kind`; 0 nếu chưa có."""
        ends = [s["target_timerange"]["start"] + s["target_timerange"]["duration"]
                for t in self.draft["tracks"] if t["type"] == kind for s in t["segments"]]
        return max(ends, default=0) / 1_000_000

    # ---- API ----------------------------------------------------------------
    def add_clip(self, file_path: str, duration: Optional[float] = None, source_start: float = 0.0) -> str:
        """Nối video/ảnh vào cuối track hình chính. duration=None: video lấy hết phần còn lại, ảnh 3s."""
        path = Path(file_path).resolve()
        info = probe_media(path)
        if info["kind"] == "audio":
            raise ValueError(f"{path.name} không có hình — dùng add_music()")
        photo = info["kind"] == "photo"
        available = None if photo else info["duration_us"] / 1_000_000 - source_start
        if duration is None:
            duration = DEFAULT_PHOTO_SECONDS if photo else available
        if available is not None:
            duration = min(duration, available)
        if duration <= 0:
            raise ValueError(f"{path.name}: thời lượng cắt phải > 0")
        material_id = self._material(
            "videos", "video", type="photo" if photo else "video", path=path.as_posix(), material_name=path.name,
            duration=info["duration_us"], width=info["width"], height=info["height"], has_audio=info["has_audio"],
        )
        refs = self._common_refs()
        refs.insert(2, self._material("canvases", "canvas"))
        self._register_media(path, info, 0, "photo" if photo else "video")
        return self._segment("video", material_id, refs, _us(self.track_end("video")), _us(duration),
                             0 if photo else _us(source_start))

    def add_music(self, file_path: str, start_at: float = 0.0, duration: Optional[float] = None,
                  volume: float = 1.0) -> str:
        """Nhạc nền / voice-over trên track audio; mặc định kéo dài bằng track hình (không vượt độ dài file)."""
        path = Path(file_path).resolve()
        info = probe_media(path)
        if duration is None:
            duration = max(0.0, self.track_end("video") - start_at) or info["duration_us"] / 1_000_000
        duration = min(duration, info["duration_us"] / 1_000_000)
        material_id = self._material("audios", "audio", path=path.as_posix(), name=path.stem,
                                     music_id=str(uuid.uuid4()), duration=info["duration_us"])
        self._register_media(path, info, 0, "music")
        return self._segment("audio", material_id, self._common_refs(), _us(start_at), _us(duration), 0,
                             volume=volume, clip=None, hdr_settings=None, uniform_scale=None)

    def add_text(self, text: str, start_at: float, duration: float, color: str = "#F7B503",
                 size: float = 12.0, y: float = 0.55) -> str:
        """Chữ tiêu đề (chuẩn hoá NFC); y trong [-1, 1] (0 = giữa khung, dương = phía trên)."""
        text = nfc(text)
        font = _capcut_default_font()
        content = {
            "styles": [{
                "fill": {"content": {"render_type": "solid", "solid": {"color": _hex_to_rgb_float(color)}}},
                "range": [0, len(text.encode("utf-16-le")) // 2],
                "size": size,
                "bold": True,
                "font": {"id": "", "path": font},
                "strokes": [{"content": {"render_type": "solid", "solid": {"color": [0, 0, 0]}},
                             "width": TEMPLATE["text"]["border_width"], "mode": 0}],
                "useLetterColor": True,
            }],
            "text": text,
        }
        material_id = self._material("texts", "text", content=json.dumps(content, ensure_ascii=False),
                                     font_size=size, font_path=font, text_color=color.lower())
        animation = self._material("material_animations", "material_animation")
        clip = copy.deepcopy(TEMPLATE["segment"]["clip"])
        clip["transform"]["y"] = y
        return self._segment("text", material_id, [animation], _us(start_at), _us(duration), None,
                             clip=clip, hdr_settings=None, render_index=14000)

    def save(self, draft_dir: str) -> Dict[str, object]:
        """Ghi draft vào draft_dir (thư mục chưa tồn tại hoặc rỗng)."""
        folder = Path(draft_dir).resolve()
        if folder.exists() and any(folder.iterdir()):
            raise FileExistsError(f"Thư mục đã có dữ liệu, không ghi đè: {folder}")
        folder.mkdir(parents=True, exist_ok=True)
        now_us = int(time.time() * 1_000_000)
        content = json.dumps(self.draft, ensure_ascii=False)
        (folder / "draft_info.json").write_text(content, encoding="utf-8")
        (folder / "draft_content.json").write_text(content, encoding="utf-8")

        meta = _new("meta", draft_id=self.draft["id"], draft_name=self.name,
                    draft_fold_path=folder.as_posix(), draft_root_path=folder.parent.as_posix(),
                    tm_draft_create=now_us, tm_draft_modified=now_us, tm_duration=self.draft["duration"])
        for bucket in meta["draft_materials"]:
            bucket["value"] = [m["entry"] for m in self.media if m["bucket"] == bucket["type"]]
        (folder / "draft_meta_info.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
        return {
            "draft_dir": str(folder),
            "files": ["draft_info.json", "draft_content.json", "draft_meta_info.json"],
            "duration_sec": self.draft["duration"] / 1_000_000,
            "tracks": {t["type"]: len(t["segments"]) for t in self.draft["tracks"]},
        }

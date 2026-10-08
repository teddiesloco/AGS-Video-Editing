"""
AGS (Agent Space) — engine dựng video Bất Động Sản.

- AgsCapCutDraft: sinh draft CapCut desktop (draft_info.json + draft_content.json + draft_meta_info.json).
- AgsCinematicStyle: Công thức Dự án Đô thị (Cinematic) — mốc cắt theo beat nhạc, prompt AI hook.
- AgsLandParcelStyle: Công thức Đất nền (GIS) — viền ranh giới thửa đất, lưới phân lô, ticker bản tin.
- AgsDirectRenderer: render slideshow 9:16 bằng FFmpeg (Ken Burns), không cần CapCut.

Package dùng chung `ags_common` nằm ở thư mục `scripts/` (được đưa vào sys.path khi chạy scripts/ags_bds_cli.py).
"""

from .ags_capcut_draft import AgsCapCutDraft, capcut_drafts_dir
from .ags_direct_renderer import AgsDirectRenderer
from .ags_style_cinematic import AgsCinematicStyle
from .ags_style_land_parcel import AgsLandParcelStyle

__all__ = ["AgsCapCutDraft", "capcut_drafts_dir", "AgsCinematicStyle", "AgsLandParcelStyle", "AgsDirectRenderer"]

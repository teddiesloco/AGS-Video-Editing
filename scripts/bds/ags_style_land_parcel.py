"""
AGS (Agent Space) — Công thức Đất nền (GIS)
- Viền ranh giới thửa đất phát sáng (neon) trên ảnh vệ tinh / flycam.
- Lưới phân lô đổi màu theo trạng thái: Đã bán (đỏ) | Còn trống (xanh) | Đang cọc (vàng).
- Thanh ticker bản tin BĐS (đặt trong vùng an toàn 9:16, không dùng emoji).
Tọa độ polygon / ô lô tính theo khung đầu ra (mặc định 1080x1920); ảnh nền được cắt cho vừa khung, không bóp méo.
"""

from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from ags_common import fit_text, load_font

STATUS = {
    "SOLD": ((220, 38, 38, 190), "ĐÃ BÁN"),
    "AVAILABLE": ((22, 163, 74, 190), "CÒN TRỐNG"),
    "DEPOSITED": ((202, 138, 4, 190), "ĐANG CỌC"),
}


def _save_jpeg(image: Image.Image, output_path: str) -> str:
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(out, "JPEG", quality=95)
    return str(out)


class AgsLandParcelStyle:
    def __init__(self, width: int = 1080, height: int = 1920):
        self.width = width
        self.height = height

    def _base(self, base_img_path: str) -> Image.Image:
        """Ảnh nền cắt-cho-vừa khung (giữ tỉ lệ, không kéo giãn)."""
        with Image.open(base_img_path) as im:
            return ImageOps.fit(im.convert("RGBA"), (self.width, self.height), Image.LANCZOS)

    def render_parcel_boundary(
        self,
        base_img_path: str,
        polygon_points: Sequence[Tuple[int, int]],
        output_path: str,
        label: str = "RANH GIỚI THỬA ĐẤT",
        color: Tuple[int, int, int] = (239, 68, 68),
    ) -> str:
        points = [tuple(p) for p in polygon_points]
        if len(points) < 3:
            raise ValueError("Polygon cần ít nhất 3 điểm")
        base = self._base(base_img_path)
        ring = points + [points[0]]

        # Lớp glow: nền mờ + 3 nét viền rộng dần, làm mờ Gaussian
        glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw_glow = ImageDraw.Draw(glow)
        draw_glow.polygon(points, fill=(*color, 45))
        for width, alpha in [(26, 70), (14, 150), (7, 230)]:
            draw_glow.line(ring, fill=(*color, alpha), width=width, joint="curve")
        combined = Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(7)))

        # Viền sắc nét: màu chính + lõi trắng
        draw = ImageDraw.Draw(combined)
        draw.line(ring, fill=(*color, 255), width=6, joint="curve")
        draw.line(ring, fill=(255, 255, 255, 255), width=2, joint="curve")

        # Nhãn ở tâm polygon, giữ trong khung hình
        font, lines = fit_text(draw, label, "bold", max_width=self.width * 0.8, max_lines=2, size=34, min_size=22)
        line_h = int(font.size * 1.25)
        box_w = max(draw.textlength(l, font=font) for l in lines) + 40
        box_h = len(lines) * line_h + 24
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)
        x0 = min(max(cx - box_w / 2, 20), self.width - box_w - 20)
        y0 = min(max(cy - box_h / 2, 20), self.height - box_h - 20)
        draw.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], radius=12,
                               fill=(15, 23, 42, 235), outline=(*color, 255), width=3)
        y = y0 + 12
        for line in lines:
            draw.text((x0 + (box_w - draw.textlength(line, font=font)) / 2, y), line, font=font, fill=(255, 255, 255, 255))
            y += line_h
        return _save_jpeg(combined, output_path)

    def render_subdivision_grid(self, base_img_path: str, lots: List[Dict[str, Any]], output_path: str) -> str:
        """lots = [{"code": "Lô 01", "status": "SOLD|AVAILABLE|DEPOSITED", "rect": [x1, y1, x2, y2],
                    "price": "1.2 Tỷ", "area": "120m²"}, ...]"""
        base = self._base(base_img_path)
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for lot in lots:
            if lot.get("status", "AVAILABLE") not in STATUS:
                raise ValueError(f"Trạng thái lô không hợp lệ: {lot.get('status')} (dùng {', '.join(STATUS)})")
            x1, y1, x2, y2 = lot["rect"]
            fill, status_text = STATUS[lot.get("status", "AVAILABLE")]
            draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=fill, outline=(255, 255, 255, 240), width=3)
            inner = (x2 - x1) - 30
            f_code, code_lines = fit_text(draw, f"{lot['code']} • {status_text}", "bold", inner, 1, 30, 16)
            desc = " | ".join(str(lot[k]) for k in ("area", "price") if lot.get(k))
            draw.text((x1 + 15, y1 + 15), code_lines[0], font=f_code, fill=(255, 255, 255, 255))
            if desc:
                f_desc, desc_lines = fit_text(draw, desc, "regular", inner, 1, 24, 14)
                draw.text((x1 + 15, y1 + 25 + f_code.size), desc_lines[0], font=f_desc, fill=(254, 240, 138, 255))
        return _save_jpeg(Image.alpha_composite(base, overlay), output_path)

    def render_news_ticker_bar(self, base_img_path: str, headline: str, ticker_text: str, output_path: str) -> str:
        """Khung bản tin: thanh đỏ (tiêu đề) + thanh xanh đậm (nội dung, tối đa 2 dòng) ở ~2/3 chiều cao."""
        base = self._base(base_img_path)
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        pad = 40
        max_w = self.width - 2 * pad - 40

        f_head, head_lines = fit_text(draw, f"BẢN TIN BĐS: {headline.upper()}", "bold", max_w, 1, 34, 20)
        f_tick, tick_lines = fit_text(draw, f"THÔNG TIN QUY HOẠCH: {ticker_text}", "regular", self.width - 2 * pad, 2, 30, 20)
        head_h = int(f_head.size * 1.9)
        tick_line_h = int(f_tick.size * 1.35)
        tick_h = len(tick_lines) * tick_line_h + 36
        bar_top = int(self.height * 0.64)

        draw.rectangle([0, bar_top, self.width, bar_top + head_h], fill=(225, 29, 72, 245))
        draw.rectangle([0, bar_top + head_h, self.width, bar_top + head_h + tick_h], fill=(15, 23, 42, 245))
        dot_r = f_head.size // 3
        dot_cy = bar_top + head_h // 2
        draw.ellipse([pad, dot_cy - dot_r, pad + 2 * dot_r, dot_cy + dot_r], fill=(255, 255, 255, 255))
        draw.text((pad + 2 * dot_r + 16, dot_cy), head_lines[0], font=f_head, fill=(255, 255, 255, 255), anchor="lm")
        y = bar_top + head_h + 18
        for line in tick_lines:
            draw.text((pad, y), line, font=f_tick, fill=(254, 240, 138, 255))
            y += tick_line_h
        return _save_jpeg(Image.alpha_composite(base, overlay), output_path)

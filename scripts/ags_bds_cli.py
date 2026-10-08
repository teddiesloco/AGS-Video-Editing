#!/usr/bin/env python3
"""
AGS (Agent Space) Video Editing: CLI dựng video Bất Động Sản
  draft        Sinh draft CapCut (thử nghiệm) từ clip/ảnh + chữ tiêu đề + nhạc.
  render       Render slideshow MP4 9:16 trực tiếp bằng FFmpeg (Ken Burns, cắt theo beat).
  parcel       Ảnh viền ranh giới thửa đất phát sáng.
  subdivision  Ảnh lưới phân lô đổi màu theo trạng thái.
  ticker       Ảnh khung bản tin BĐS có thanh chữ.
  beats        In mốc cắt theo BPM.
  prompt       In prompt AI hook (Tòa nhà rơi / Virtual Staging / Ngày sang đêm).
"""

import argparse
import json
import sys
from pathlib import Path

from bds import AgsCapCutDraft, AgsCinematicStyle, AgsDirectRenderer, AgsLandParcelStyle, capcut_drafts_dir
from bds.ags_style_cinematic import HOOK_PROMPTS


def clip_seconds(args):
    """Thời lượng mỗi clip: --bpm/--beat-step (cắt theo beat) hoặc --seconds."""
    if args.bpm:
        return AgsCinematicStyle(args.bpm).beat_interval * args.beat_step
    return args.seconds


def parse_points(text):
    try:
        points = [tuple(int(float(v)) for v in pair.split(",")) for pair in text.split()]
    except ValueError:
        raise argparse.ArgumentTypeError("--points dạng 'x,y x,y x,y ...'")
    if len(points) < 3 or any(len(p) != 2 for p in points):
        raise argparse.ArgumentTypeError("--points cần ít nhất 3 điểm dạng 'x,y'")
    return points


def cmd_draft(args):
    parent = capcut_drafts_dir() if args.capcut else Path(args.out)
    draft = AgsCapCutDraft(args.name, args.width, args.height, args.fps)
    seconds = clip_seconds(args)
    for clip in args.clips:
        draft.add_clip(clip, duration=seconds)
    total = draft.track_end("video")
    if args.title:
        draft.add_text(args.title, start_at=0.0, duration=min(4.0, total))
    if args.music:
        draft.add_music(args.music)
    print(json.dumps(draft.save(parent / args.name), ensure_ascii=False))


def cmd_render(args):
    seconds = clip_seconds(args) or 2.0
    renderer = AgsDirectRenderer(args.width, args.height, args.fps)
    out = renderer.render_image_slideshow(args.images, [seconds] * len(args.images), args.out, args.music)
    print(json.dumps({"output": out, "slides": len(args.images), "seconds_per_slide": round(seconds, 3)},
                     ensure_ascii=False))


def cmd_parcel(args):
    out = AgsLandParcelStyle(args.width, args.height).render_parcel_boundary(args.image, args.points, args.out, args.label)
    print(json.dumps({"output": out}, ensure_ascii=False))


def cmd_subdivision(args):
    lots = json.loads(Path(args.lots).read_text(encoding="utf-8"))
    out = AgsLandParcelStyle(args.width, args.height).render_subdivision_grid(args.image, lots, args.out)
    print(json.dumps({"output": out, "lots": len(lots)}, ensure_ascii=False))


def cmd_ticker(args):
    out = AgsLandParcelStyle(args.width, args.height).render_news_ticker_bar(args.image, args.headline, args.text, args.out)
    print(json.dumps({"output": out}, ensure_ascii=False))


def cmd_beats(args):
    cuts = AgsCinematicStyle(args.bpm).calculate_beat_cuts(args.duration, args.beat_step)
    print(json.dumps({"bpm": args.bpm, "beat_step": args.beat_step, "cuts": cuts}, ensure_ascii=False))


def cmd_prompt(args):
    data = AgsCinematicStyle().generate_ai_hook_prompt(args.name, args.location, args.type)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description="AGS (Agent Space) — engine dựng video Bất Động Sản")
    sub = parser.add_subparsers(dest="command", required=True)

    def frame_opts(p):
        p.add_argument("--width", type=int, default=1080)
        p.add_argument("--height", type=int, default=1920)

    def timing_opts(p, default_seconds):
        p.add_argument("--seconds", type=float, default=default_seconds, help="Thời lượng mỗi clip/ảnh (giây)")
        p.add_argument("--bpm", type=float, default=0, help="BPM nhạc: thời lượng mỗi clip = beat-step beat")
        p.add_argument("--beat-step", type=int, default=4, help="Số beat mỗi lần cắt (2/4/8)")

    p = sub.add_parser("draft", help="Sinh draft CapCut (thử nghiệm)")
    p.add_argument("--name", required=True, help="Tên draft (= tên thư mục)")
    p.add_argument("--clips", nargs="+", required=True, help="Video/ảnh theo thứ tự trên timeline")
    timing_opts(p, None)
    p.add_argument("--title", default="", help="Chữ tiêu đề hiện 4 giây đầu")
    p.add_argument("--music", default="", help="Nhạc nền / voice-over")
    where = p.add_mutually_exclusive_group(required=True)
    where.add_argument("--out", help="Thư mục cha; draft ghi vào <out>/<name>")
    where.add_argument("--capcut", action="store_true", help="Ghi thẳng vào thư mục draft của CapCut desktop")
    frame_opts(p)
    p.add_argument("--fps", type=int, default=30)
    p.set_defaults(func=cmd_draft)

    p = sub.add_parser("render", help="Render slideshow MP4 9:16 bằng FFmpeg")
    p.add_argument("--images", nargs="+", required=True)
    timing_opts(p, 2.0)
    p.add_argument("--music", default=None)
    p.add_argument("--out", required=True, help="File MP4 đầu ra")
    frame_opts(p)
    p.add_argument("--fps", type=int, default=30)
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("parcel", help="Viền ranh giới thửa đất phát sáng")
    p.add_argument("--image", required=True, help="Ảnh vệ tinh / flycam")
    p.add_argument("--points", required=True, type=parse_points, help="Tọa độ đỉnh trên khung đầu ra: 'x,y x,y x,y ...'")
    p.add_argument("--label", default="RANH GIỚI THỬA ĐẤT")
    p.add_argument("--out", required=True)
    frame_opts(p)
    p.set_defaults(func=cmd_parcel)

    p = sub.add_parser("subdivision", help="Lưới phân lô đổi màu")
    p.add_argument("--image", required=True)
    p.add_argument("--lots", required=True, help="File JSON danh sách lô (code, status, rect, area, price)")
    p.add_argument("--out", required=True)
    frame_opts(p)
    p.set_defaults(func=cmd_subdivision)

    p = sub.add_parser("ticker", help="Khung bản tin BĐS")
    p.add_argument("--image", required=True)
    p.add_argument("--headline", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--out", required=True)
    frame_opts(p)
    p.set_defaults(func=cmd_ticker)

    p = sub.add_parser("beats", help="Mốc cắt theo BPM")
    p.add_argument("--bpm", type=float, required=True)
    p.add_argument("--beat-step", type=int, default=4)
    p.add_argument("--duration", type=float, required=True, help="Tổng thời lượng (giây)")
    p.set_defaults(func=cmd_beats)

    p = sub.add_parser("prompt", help="Prompt AI hook")
    p.add_argument("--type", choices=list(HOOK_PROMPTS), default="falling_building")
    p.add_argument("--name", required=True, help="Tên dự án")
    p.add_argument("--location", required=True, help="Vị trí")
    p.set_defaults(func=cmd_prompt)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (FileExistsError, ValueError, RuntimeError, OSError) as exc:
        sys.exit(f"❌ {exc}")


if __name__ == "__main__":
    main()

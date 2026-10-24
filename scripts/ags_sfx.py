#!/usr/bin/env python3
"""Mix CC0/custom effects into a video without shortening it or replacing its audio."""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import tempfile

from ags_common import LOUDNORM, run_cmd, video_info

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "sfx"
MAX_EVENTS = 256


def mix(input_path, events, output_path):
    source, output = Path(input_path).expanduser().resolve(), Path(output_path).expanduser().resolve()
    if not source.is_file() or source == output or output.exists() or output.suffix.lower() != ".mp4":
        raise ValueError("Input must exist; output must be a new, different .mp4")
    info = video_info(source)
    duration = info["duration"]
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Video must have a finite positive duration")
    if not isinstance(events, list) or not events:
        raise ValueError("Events must be a nonempty list of {file, time, gain}")
    if len(events) > MAX_EVENTS:
        raise ValueError(f"At most {MAX_EVENTS} events per mix")
    resolved = []
    for event in events:
        if not isinstance(event, dict) or set(event) - {"file", "time", "gain"}:
            raise ValueError("Each event accepts only file, time, gain")
        time, gain = event.get("time"), event.get("gain", 0.25)
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
               for v in (time, gain)) or not 0 <= time < duration or not 0 <= gain <= 1:
            raise ValueError("time must be finite within video; gain must be finite in [0, 1]")
        if not isinstance(event.get("file"), str):
            raise ValueError("Effect file must be a path or bundled filename")
        path = Path(event["file"]).expanduser()
        if not path.is_file() and path.name == str(path):
            path = ASSETS / path
        path = path.resolve()
        if not path.is_file() or path == output:
            raise ValueError(f"Invalid effect: {path}")
        probe = json.loads(run_cmd(["ffprobe", "-v", "error", "-show_streams", "-of", "json", path]).stdout)
        if not any(s.get("codec_type") == "audio" for s in probe["streams"]):
            raise ValueError(f"Effect has no audio: {path}")
        resolved.append((path, time, gain))
    # Keep the source layout (mono/stereo/5.1); anything else is mixed down to stereo.
    layout = {1: "mono", 2: "stereo", 6: "5.1"}.get(info["audio_channels"], "stereo")
    fmt = f"aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts={layout}"
    args = ["ffmpeg", "-nostdin", "-v", "error", "-i", source]
    filters = []
    if info["audio_channels"]:
        filters.append(f"[0:a:0]{fmt},apad,atrim=duration={duration}[base]")
    else:
        filters.append(f"anullsrc=r=48000:cl={layout},atrim=duration={duration}[base]")
    for i, (path, time, gain) in enumerate(resolved, 1):
        args += ["-i", path]
        # Resample before adelay: the delay is counted in samples at 48 kHz.
        filters.append(f"[{i}:a:0]{fmt},atrim=duration={duration-time},asetpts=PTS-STARTPTS,"
                       f"volume={gain},adelay={round(time*48000)}S:all=1[s{i}]")
    labels = "[base]" + "".join(f"[s{i}]" for i in range(1, len(resolved)+1))
    # Same -14 LUFS / TP -2 stage as every other renderer. A silent source has no program
    # level to match: normalizing would inflate the effects, so it only gets the peak limiter.
    final = (f"{LOUDNORM},aresample=48000,apad,atrim=duration={duration}" if info["audio_channels"]
             else "alimiter=limit=0.794:level=false:latency=true")
    filters.append(f"{labels}amix=inputs={len(resolved)+1}:duration=first:normalize=0,{final}[out]")
    fd, temporary = tempfile.mkstemp(suffix=".mp4", dir=output.parent)
    os.close(fd)
    try:
        run_cmd(args + ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[out]",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-movflags", "+faststart", "-y", temporary])
        try:
            os.link(temporary, output)  # atomic: never replaces a file created meanwhile
        except FileExistsError:
            raise ValueError(f"Output already exists: {output}")
        except OSError:  # filesystem without hard links
            with open(temporary, "rb") as produced, output.open("xb") as target:
                shutil.copyfileobj(produced, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {"output": str(output), "events": len(events), "seconds": duration}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["list", "mix"])
    parser.add_argument("input", nargs="?")
    parser.add_argument("--events", type=Path, help="UTF-8 JSON array; custom paths relative to this file")
    parser.add_argument("--out")
    args = parser.parse_args()
    try:
        if args.command == "list":
            result = {"license": "CC0-1.0", "effects": [p.name for p in sorted(ASSETS.glob("*.ogg"))]}
        else:
            if not args.input or not args.events or not args.out:
                parser.error("mix requires input, --events and --out")
            events = json.loads(args.events.read_text(encoding="utf-8-sig"))
            if isinstance(events, list):
                for event in events:
                    if isinstance(event, dict) and isinstance(event.get("file"), str):
                        path = Path(event["file"])
                        local = args.events.resolve().parent / path
                        if not path.is_absolute() and local.is_file():
                            event["file"] = str(local)
            result = mix(args.input, events, args.out)
        print(json.dumps(result))
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f"SFX: {error}\n")


if __name__ == "__main__":
    main()

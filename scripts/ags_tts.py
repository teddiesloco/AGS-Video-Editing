#!/usr/bin/env python3
"""Vietnamese TTS synthesis (vieneu, gemini, synth, zerotts) + Vietnamese number/currency normalizer."""
import argparse
import base64
import contextlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
import wave

_VI_DIGITS = {
    0: "không", 1: "một", 2: "hai", 3: "ba", 4: "bốn",
    5: "năm", 6: "sáu", 7: "bảy", 8: "tám", 9: "chín",
}


def _vi_int_under_1000(n: int) -> str:
    if n < 0:
        return "âm " + _vi_int_under_1000(-n)
    if n < 10:
        return _VI_DIGITS[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        head = "mười" if tens == 1 else f"{_VI_DIGITS[tens]} mươi"
        if ones == 0:
            return head
        if ones == 1 and tens > 1:
            return f"{head} mốt"
        if ones == 4 and tens > 1:
            return f"{head} tư"
        if ones == 5:
            return f"{head} lăm"
        return f"{head} {_VI_DIGITS[ones]}"
    hundreds, rem = divmod(n, 100)
    head = f"{_VI_DIGITS[hundreds]} trăm"
    if rem == 0:
        return head
    if rem < 10:
        return f"{head} lẻ {_VI_DIGITS[rem]}"
    return f"{head} {_vi_int_under_1000(rem)}"


def _vi_number_str(num_str: str) -> str:
    clean = num_str.strip().replace(",", ".")
    if "." in clean:
        left, right = clean.split(".", 1)
        left_w = _vi_int_under_1000(int(left)) if left.isdigit() and int(left) < 1000 else left
        right_w = _vi_int_under_1000(int(right)) if right.isdigit() and int(right) < 1000 else right
        return f"{left_w} phẩy {right_w}"
    if clean.isdigit() and int(clean) < 1000:
        return _vi_int_under_1000(int(clean))
    return clean


def normalize_vietnamese_tts_text(text: str) -> str:
    """Normalize Vietnamese currency shorthands (99k, 1,9tr), percentages (40%), and 24/7 into spoken words."""
    s = unicodedata.normalize("NFC", str(text or "")).strip()
    s = re.sub(r"\b24/7\b", "hai mươi bốn trên bảy", s)
    s = re.sub(
        r"(?<![\w.])(\d+(?:[.,]\d+)?)\s*(?:tr|triệu)\b",
        lambda m: f"{_vi_number_str(m.group(1))} triệu",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(
        r"(?<![\w.])(\d+(?:[.,]\d+)?)\s*tỷ\b",
        lambda m: f"{_vi_number_str(m.group(1))} tỷ",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(
        r"(?<![\w.])(\d+(?:[.,]\d+)?)\s*k\b",
        lambda m: f"{_vi_number_str(m.group(1))} nghìn",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(
        r"(?<![\w.])(\d+(?:[.,]\d+)?)\s*%",
        lambda m: f"{_vi_number_str(m.group(1))} phần trăm",
        s,
    )
    return re.sub(r"\s+", " ", s).strip()


def _synth_fallback_audio(text: str, sample_rate: int = 48000):
    """Generate speech-cadence harmonic envelope WAV (uses macOS 'say' Vietnamese voice when available)."""
    import numpy as np
    words = [w for w in re.split(r"\s+", text.strip()) if w]
    dur = max(1.6, min(60.0, len(words) / 2.35))
    if sys.platform == "darwin":
        with tempfile.TemporaryDirectory(prefix="ags_say_") as td:
            aiff = Path(td) / "say.aiff"
            wav_p = Path(td) / "say.wav"
            r = subprocess.run(["say", "-v", "Linh", "-o", str(aiff), text], capture_output=True)
            if r.returncode != 0:
                r = subprocess.run(["say", "-o", str(aiff), text], capture_output=True)
            if r.returncode == 0 and aiff.is_file():
                c = subprocess.run(
                    ["ffmpeg", "-nostdin", "-v", "error", "-i", str(aiff), "-ac", "1", "-ar", str(sample_rate), "-f", "f32le", "-"],
                    capture_output=True,
                )
                if c.returncode == 0 and c.stdout:
                    arr = np.frombuffer(c.stdout, dtype="<f4").copy()
                    if arr.size > sample_rate // 4:
                        return arr, sample_rate
    n = int(round(dur * sample_rate))
    t = np.arange(n, dtype=np.float32) / float(sample_rate)
    syllable_env = 0.55 + 0.45 * np.sin(2.0 * math.pi * 3.8 * t)
    sig = (0.18 * np.sin(2.0 * math.pi * 190.0 * t) + 0.09 * np.sin(2.0 * math.pi * 380.0 * t)) * syllable_env
    return sig.astype(np.float32), sample_rate


def _save_wav_f32(audio, path: str, sample_rate: int = 48000) -> None:
    import numpy as np
    arr = np.clip(np.asarray(audio, dtype=np.float32), -0.98, 0.98)
    pcm16 = (arr * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(sample_rate))
        wf.writeframes(pcm16.tobytes())


def generate(engine, text=None, voice=None, output=None):
    if text is not None and not text.strip():
        raise ValueError("Text must not be empty")
    if text is not None and output is None:
        raise ValueError("Synthesis requires an output WAV path")
    if output is not None:
        output = Path(output).expanduser().resolve()
        if output.suffix.lower() != ".wav" or output.exists():
            raise ValueError("Output must be a new .wav file")
    if text is not None:
        text = normalize_vietnamese_tts_text(text)
    if engine == "vieneu":
        from vieneu import Vieneu
        tts = Vieneu(mode="v3turbo", backend="onnx", device="cpu", precision="fp32")
        voices = tts.list_preset_voices()
        names = [v[1] if isinstance(v, (tuple, list)) else v for v in voices]
        if voice is not None and voice not in names:
            raise ValueError(f"Unknown preset voice: {voice}; available: {names}")
        if text is None:
            return {"engine": engine, "voices": voices}
        audio = tts.infer(text, **({"voice": voice} if voice else {}))
        save = tts.save
    elif engine == "zerotts":
        from zerotts import ZeroTTS, normalize_vi_text
        from zerotts.audio import concat_with_silence
        from zerotts.chunking import chunk_text, clean_segment_punctuation, normalize_punctuation
        from zerotts.voices import list_voices, load_voice
        tts = ZeroTTS.from_pretrained("zeroweight-ai/ZeroTTS")
        names = list_voices(tts.voices_root)
        if text is None:
            return {"engine": engine, "voices": names, "usage": "evaluation and demos only"}
        voice = voice or "maichi"
        if voice not in names:
            raise ValueError(f"Unknown bundled voice: {voice}; available: {names}")
        # Load directly from bundled assets: user-installed voices must not shadow presets.
        preset = load_voice(tts.voices_root, voice, expect_queries=tts.n_voice_queries)
        segments = [clean_segment_punctuation(s) for s in chunk_text(
            normalize_punctuation(normalize_vi_text(text)), max_chunk_sec=15.0)]
        segments = [s for s in segments if s]
        if not segments:
            raise ValueError("Text contains no speech")
        audio = concat_with_silence([tts.synthesize(s, voice=preset) for s in segments],
                                    silence_sec=0.15, sample_rate=tts.sample_rate)
        save = tts.save_audio
    elif engine == "gemini":
        gemini_voices = ["Kore", "Aoede", "Puck", "Charon", "Fenrir"]
        if text is None:
            return {"engine": engine, "voices": gemini_voices}
        voice_name = voice or "Kore"
        api_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required for engine=gemini")
        sr = 48000
        model = os.environ.get("AGS_GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice_name}}},
            },
        }
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            part = body["candidates"][0]["content"]["parts"][0]["inlineData"]
            raw_pcm = base64.b64decode(part["data"])
            import numpy as np
            pcm24 = np.frombuffer(raw_pcm, dtype="<i2").astype(np.float32) / 32768.0
            audio = np.repeat(pcm24, 2)  # 24kHz -> 48kHz
        except Exception as exc:
            raise RuntimeError(f"Gemini TTS synthesis failed: {exc}") from exc
        class _Holder:
            sample_rate = sr
        tts = _Holder()
        save = lambda arr, p: _save_wav_f32(arr, p, sample_rate=sr)
    elif engine == "synth":
        if text is None:
            return {"engine": engine, "voices": ["Linh", "harmonic"]}
        audio, sr = _synth_fallback_audio(text, sample_rate=48000)
        class _Holder:
            sample_rate = sr
        tts = _Holder()
        save = lambda arr, p: _save_wav_f32(arr, p, sample_rate=sr)
    else:
        raise ValueError("Engine must be vieneu, gemini, synth, or zerotts")
    import numpy as np
    if not np.asarray(audio).size or not np.isfinite(audio).all():
        raise RuntimeError("Engine returned empty or non-finite audio")
    fd, temporary = tempfile.mkstemp(suffix=".wav", dir=output.parent)
    os.close(fd)
    try:
        save(audio, temporary)
        # Exclusive creation protects an output created while inference was running.
        with open(temporary, "rb") as source, output.open("xb") as target:
            import shutil
            shutil.copyfileobj(source, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {"engine": engine, "output": str(output), "sample_rate": tts.sample_rate,
            "seconds": np.asarray(audio).size / tts.sample_rate}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["voices", "synthesize"])
    parser.add_argument("--engine", required=True, choices=["vieneu", "gemini", "synth", "zerotts"])
    parser.add_argument("--text-file", type=Path, help="UTF-8 Vietnamese text")
    parser.add_argument("--voice", help="Bundled preset name")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.command == "synthesize" and (args.text_file is None or args.out is None):
        parser.error("synthesize requires --text-file and --out")
    try:
        text = args.text_file.read_text(encoding="utf-8-sig") if args.command == "synthesize" else None
        if args.text_file and args.out and args.text_file.resolve() == args.out.resolve():
            raise ValueError("Input and output must differ")
        with contextlib.redirect_stdout(sys.stderr):  # engine banners must not corrupt the JSON result
            result = generate(args.engine, text, args.voice, args.out)
        print(json.dumps(result))  # ASCII-escaped: safe on non-UTF-8 Windows consoles
    except ImportError as error:
        parser.exit(1, f"Missing optional TTS dependency: {error}. Install requirements-tts.txt into the AGS venv.\n")
    except Exception as error:  # model download, ONNX runtime or I/O failure: one clean line, exit 1
        parser.exit(1, f"TTS: {type(error).__name__}: {error}\n")


if __name__ == "__main__":
    main()

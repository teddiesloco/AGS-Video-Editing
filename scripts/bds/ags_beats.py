"""
AGS (Agent Space) — dò BPM và mốc beat từ file nhạc (chỉ dùng numpy, không thêm thư viện).
1. Onset strength: năng lượng STFT gom vào 24 dải tần log từ 30 Hz tới 4 kHz (trống kick, snare; bỏ hi-hat vốn
   rơi vào nửa nhịp), cộng phần tăng giữa 2 khung liên tiếp (spectral flux).
2. Tempo: tự tương quan của onset strength trong khoảng 60–180 BPM, ưu tiên quanh 120 BPM để tránh nhầm nửa/gấp đôi.
3. Pha: chọn độ lệch có tổng onset lớn nhất trên lưới beat, rồi nắn từng beat về đỉnh onset gần nhất.
Hợp với nhạc nền có nhịp đều (pop, EDM, nhạc quảng cáo); nhạc đổi tempo liên tục thì nên dùng --bpm.
"""

from typing import List, Tuple

import numpy as np

from ags_common import load_audio

SAMPLE_RATE = 22050
N_FFT = 1024
HOP = 256
# Đỉnh spectral flux xuất hiện khi tiếng gõ vừa lọt vào cửa sổ Hann: dời mốc 3/4 cửa sổ (hiệu chỉnh bằng click track
# tổng hợp 97/128/140 BPM: sai số trung bình < 1 ms, lớn nhất 6 ms).
ONSET_OFFSET = 0.75 * N_FFT


BANDS = np.geomspace(30.0, 4000.0, 25)


def onset_strength(samples: np.ndarray) -> np.ndarray:
    frames = 1 + (len(samples) - N_FFT) // HOP
    if frames < 16:
        raise ValueError("File nhạc quá ngắn để dò beat")
    window = np.hanning(N_FFT).astype(np.float32)
    band_of_bin = np.digitize(np.fft.rfftfreq(N_FFT, 1 / SAMPLE_RATE), BANDS) - 1
    in_range = (band_of_bin >= 0) & (band_of_bin < len(BANDS) - 1)
    flux = np.zeros(frames)
    prev = None
    for start in range(0, frames, 2048):
        idx = np.arange(start, min(frames, start + 2048))[:, None] * HOP + np.arange(N_FFT)[None, :]
        power = np.abs(np.fft.rfft(samples[idx] * window, axis=1)) ** 2
        bands = np.zeros((len(power), len(BANDS) - 1))
        np.add.at(bands.T, band_of_bin[in_range], power[:, in_range].T)
        level = np.log1p(1000.0 * bands)
        first = level[:1] if prev is None else prev
        flux[start:start + len(level)] = np.maximum(0.0, np.diff(level, axis=0, prepend=first)).sum(axis=1)
        prev = level[-1:]
    local = np.convolve(flux, np.ones(43) / 43, mode="same")  # trung bình trượt ~0.5 s
    env = np.maximum(0.0, flux - local)
    return env / (env.std() + 1e-9)


def detect_beats(audio_path: str, min_bpm: float = 60.0, max_bpm: float = 180.0) -> Tuple[float, List[float]]:
    """(BPM, [mốc beat theo giây]) của file nhạc."""
    env = onset_strength(load_audio(audio_path, SAMPLE_RATE))
    n = len(env)
    spectrum = np.fft.rfft(env, 2 * n)
    ac = np.fft.irfft(spectrum * np.conj(spectrum))[:n]
    frame_rate = SAMPLE_RATE / HOP
    lags = np.arange(max(2, int(frame_rate * 60 / max_bpm)), min(n - 1, int(frame_rate * 60 / min_bpm) + 1))
    if len(lags) < 3:
        raise ValueError("File nhạc quá ngắn để dò tempo")
    bpms = 60 * frame_rate / lags
    score = ac[lags] * np.exp(-0.5 * (np.log2(bpms / 120.0) / 0.9) ** 2)
    i = int(np.argmax(score))
    lag = float(lags[i])
    if 0 < i < len(lags) - 1:  # nội suy parabol cho độ trễ lẻ
        a, b, c = score[i - 1], score[i], score[i + 1]
        if a - 2 * b + c != 0:
            lag += 0.5 * (a - c) / (a - 2 * b + c)
    phases = np.arange(int(np.ceil(lag)))
    grid = np.arange(0, n, lag)
    totals = [env[np.minimum(n - 1, np.round(p + grid).astype(int))].sum() for p in phases]
    beats = np.arange(phases[int(np.argmax(totals))], n, lag)
    reach = max(1, int(lag * 0.1))
    peaks = []
    for frame in np.round(beats).astype(int):
        lo, hi = max(0, frame - reach), min(n, frame + reach + 1)
        peaks.append(lo + int(np.argmax(env[lo:hi])))
    # bỏ các beat ở đầu/cuối nằm trong đoạn chưa có (hoặc đã hết) tiếng trống
    strong = env[peaks] >= 0.2 * np.median(env[peaks])
    first, last = int(np.argmax(strong)), len(peaks) - int(np.argmax(strong[::-1]))
    times = [(p * HOP + ONSET_OFFSET) / SAMPLE_RATE for p in peaks[first:last]]
    return round(60 * frame_rate / lag, 2), [round(t, 3) for t in times]


def beat_durations(beats: List[float], count: int, beat_step: int) -> List[float]:
    """Thời lượng `count` cảnh, cắt ở mỗi `beat_step` beat; cảnh đầu chạy từ 0 tới mốc cắt đầu tiên.
    Nhạc hết beat thì các cảnh còn lại giữ nhịp trung bình."""
    if len(beats) < 2:
        raise ValueError("Không đủ beat để chia cảnh")
    cuts = list(beats[beat_step::beat_step])
    interval = float(np.median(np.diff(beats))) * beat_step
    while len(cuts) < count:
        cuts.append((cuts[-1] if cuts else 0.0) + interval)
    edges = [0.0] + cuts[:count]
    return [round(b - a, 3) for a, b in zip(edges, edges[1:])]

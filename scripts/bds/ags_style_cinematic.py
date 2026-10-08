"""
AGS (Agent Space) — Công thức Dự án Đô thị (Cinematic)
- Mốc cắt cảnh theo beat nhạc (cắt mỗi 2/4/8 beat).
- Prompt image-to-video cho AI hook (Hiệu ứng Tòa nhà rơi, Virtual Staging, Ngày sang đêm).
"""

from typing import Dict, List

HOOK_PROMPTS = {
    "falling_building": (
        "Cinematic 4K hyper-realistic footage. An empty open field in {location}. "
        "Suddenly, a luxurious modern architectural complex '{name}' falls vertically from the sky "
        "and slams firmly into the ground like a landing rocket, massive dust and shockwave billowing outwards, "
        "camera shakes violently on impact, revealing the majestic final building with glowing glass facade.",
        "Explosion Impact + Low Earth Thud + Whoosh",
    ),
    "virtual_staging": (
        "Fixed wide angle camera inside an empty, raw concrete living room. "
        "Luxury Italian furniture, leather sofa, marble dining table, chandelier and modern art fly in smoothly "
        "and assemble themselves seamlessly into a warm, perfectly lit, fully furnished apartment.",
        "Magic Swoosh + Wood Click",
    ),
    "day_to_night": (
        "Cinematic aerial drone hyperlapse orbiting {name} in {location}, "
        "transitioning smoothly from bright daytime to vibrant neon night.",
        "Cinematic Riser + Night City Ambience",
    ),
}


class AgsCinematicStyle:
    def __init__(self, bpm: float = 120.0):
        if bpm <= 0:
            raise ValueError("BPM phải > 0")
        self.bpm = bpm
        self.beat_interval = 60.0 / bpm  # giây mỗi beat

    def calculate_beat_cuts(self, total_duration: float, beat_step: int = 4) -> List[float]:
        """Mốc cắt (giây) trùng beat nhạc, vd 120 BPM + 4 beat = cắt mỗi 2.0s."""
        interval = self.beat_interval * beat_step
        cuts = []
        current = 0.0
        while current + interval <= total_duration + 1e-9:
            current += interval
            cuts.append(round(current, 3))
        return cuts

    def generate_ai_hook_prompt(self, property_name: str, location: str, hook_type: str = "falling_building") -> Dict[str, object]:
        """Prompt tiếng Anh cho công cụ AI video (Kling / Runway / Luma) + gợi ý SoundFX tìm trong CapCut."""
        if hook_type not in HOOK_PROMPTS:
            raise ValueError(f"hook_type phải là một trong: {', '.join(HOOK_PROMPTS)}")
        prompt, sound_fx = HOOK_PROMPTS[hook_type]
        return {
            "hook_type": hook_type,
            "prompt_en": prompt.format(name=property_name, location=location),
            "sound_fx": sound_fx,
            "recommended_duration_sec": 5.0,
        }

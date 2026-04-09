"""使用 ffmpeg 将导入音频转为 16-bit PCM 单声道 WAV（适合 SIP 播放）。"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

# 与常见宽带 SIP 编解码兼容；如需窄带可改为 8000
SIP_WAV_SAMPLE_RATE = 16000


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _safe_stem(name: str, max_len: int = 80) -> str:
    s = re.sub(r"[^\w\-]+", "_", name, flags=re.UNICODE).strip("_")
    return (s or "track")[:max_len]


def convert_to_playback_wav(src: Path, dest_dir: Path) -> Path:
    """
    将任意 ffmpeg 可读文件转为 16-bit PCM 单声道 WAV，写入 dest_dir。
    返回输出文件路径。
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.md5(str(src.resolve()).encode()).hexdigest()[:8]
    out = dest_dir / f"{_safe_stem(src.stem)}_{digest}.wav"
    cmd = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(src),
        "-ac",
        "1",
        "-ar",
        str(SIP_WAV_SAMPLE_RATE),
        "-sample_fmt",
        "s16",
        "-f",
        "wav",
        str(out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip() or f"exit {r.returncode}"
        raise RuntimeError(err)
    return out

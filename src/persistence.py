"""项目路径与设置 JSON 持久化。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def project_root() -> Path:
    """src 包所在仓库/安装根目录（src 的上一级）。"""
    return Path(__file__).resolve().parent.parent


def imports_dir() -> Path:
    return project_root() / "imported_tracks"


def settings_path() -> Path:
    return project_root() / "sip_player_settings.json"


@dataclass
class PersistedSettings:
    id_uri: str = "sip:1000@192.168.1.1"
    registrar: str = "sip:192.168.1.1"
    username: str = "1000"
    password: str = ""
    tracks: list[str] = field(default_factory=list)
    play_mode: int = 0


def ensure_imports_dir() -> Path:
    d = imports_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_settings() -> PersistedSettings:
    path = settings_path()
    if not path.is_file():
        return PersistedSettings()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return PersistedSettings()
    return _settings_from_dict(raw)


def _settings_from_dict(raw: dict[str, Any]) -> PersistedSettings:
    base = PersistedSettings()
    if not isinstance(raw, dict):
        return base
    tracks = raw.get("tracks", base.tracks)
    if not isinstance(tracks, list):
        tracks = base.tracks
    track_strs = [str(t) for t in tracks if t]
    pm = raw.get("play_mode", base.play_mode)
    try:
        play_mode = int(pm)
    except (TypeError, ValueError):
        play_mode = base.play_mode
    return PersistedSettings(
        id_uri=str(raw.get("id_uri", base.id_uri) or base.id_uri),
        registrar=str(raw.get("registrar", base.registrar) or base.registrar),
        username=str(raw.get("username", base.username) or base.username),
        password=str(raw.get("password", base.password) or ""),
        tracks=track_strs,
        play_mode=play_mode,
    )


def save_settings(settings: PersistedSettings) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(settings)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

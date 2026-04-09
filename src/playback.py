"""播放列表状态与 WAV 文件播放器（pjsua2 AudioMediaPlayer）。"""

from __future__ import annotations

import random
from enum import IntEnum
from typing import TYPE_CHECKING, Callable

import pjsua2 as pj

if TYPE_CHECKING:
    from src.sip_stack import SipApp


class PlayMode(IntEnum):
    """顺序 / 列表循环 / 单曲循环 / 随机。"""

    SEQUENTIAL = 0
    LOOP_LIST = 1
    LOOP_ONE = 2
    SHUFFLE = 3


class TrackAudioPlayer(pj.AudioMediaPlayer):
    """带 EOF 回调的播放器，便于在顺序/列表/随机模式下切歌。"""

    def __init__(self, on_eof: Callable[[], None]) -> None:
        pj.AudioMediaPlayer.__init__(self)
        self._on_eof = on_eof

    def onEof2(self) -> None:
        self._on_eof()


class PlaybackController:
    """维护曲目列表、播放模式、暂停状态，并管理底层 AudioMediaPlayer 生命周期。"""

    def __init__(self, app: SipApp) -> None:
        self._app = app
        self.paths: list[str] = []
        self._index = 0
        self.mode = PlayMode.SEQUENTIAL
        self.paused = False
        self._player: TrackAudioPlayer | None = None
        self._call_audios: dict[int, pj.AudioMedia] = {}

    def set_tracks(self, paths: list[str]) -> None:
        self.paths = [p for p in paths if p]
        if self._index >= len(self.paths):
            self._index = max(0, len(self.paths) - 1)
        self._reload_stream()

    def status_line(self) -> str:
        if not self.paths:
            return "无曲目（请添加 16-bit PCM 单声道 WAV）"
        name = self.paths[self._index].split("/")[-1]
        mode_s = ("顺序", "列表循环", "单曲循环", "随机")[int(self.mode)]
        ps = "暂停" if self.paused else "播放"
        return f"{ps} | {name} | 模式: {mode_s} | [{self._index + 1}/{len(self.paths)}]"

    def add_call_audio(self, session_id: int, audio: pj.AudioMedia) -> None:
        self._call_audios[session_id] = audio
        self._sync_transmit()

    def remove_call_audio(self, session_id: int) -> None:
        # PJSIP 会自动清理断开通话的 conference port，
        # 此处不能对已失效的 AudioMedia 调 stopTransmit，否则可能
        # 破坏 player 对其余通话的传输。
        self._call_audios.pop(session_id, None)

    def detach_all_call_audio(self) -> None:
        if self._player:
            for aud in self._call_audios.values():
                try:
                    self._player.stopTransmit(aud)
                except pj.Error:
                    pass
        self._call_audios.clear()

    def _eof(self) -> None:
        if self.mode == PlayMode.LOOP_ONE:
            return
        n = len(self.paths)
        if n == 0:
            return
        if self.mode == PlayMode.SEQUENTIAL and self._index >= n - 1:
            self._app.log("顺序模式：最后一首已结束")
            return
        self._advance_after_track_finished()
        self._reload_stream()

    def _advance_after_track_finished(self) -> None:
        n = len(self.paths)
        if n == 0:
            return
        if self.mode == PlayMode.SHUFFLE:
            if n == 1:
                self._index = 0
            else:
                choices = [i for i in range(n) if i != self._index]
                self._index = random.choice(choices)
            return
        if self.mode == PlayMode.LOOP_LIST:
            self._index = (self._index + 1) % n
            return
        if self.mode == PlayMode.SEQUENTIAL:
            if self._index + 1 < n:
                self._index += 1

    def next_track(self) -> None:
        n = len(self.paths)
        if n == 0:
            return
        if self.mode == PlayMode.SHUFFLE:
            self._index = random.randrange(n)
        else:
            self._index = (self._index + 1) % n
        self._reload_stream()

    def prev_track(self) -> None:
        n = len(self.paths)
        if n == 0:
            return
        self._index = (self._index - 1) % n
        self._reload_stream()

    def jump_to_track(self, index: int) -> None:
        if not self.paths or index < 0 or index >= len(self.paths):
            return
        self._index = index
        self.paused = False
        self._reload_stream()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self._sync_transmit()

    def cycle_mode(self) -> None:
        self.mode = PlayMode((int(self.mode) + 1) % 4)
        self._reload_stream()

    def _player_options(self) -> int:
        if self.mode == PlayMode.LOOP_ONE:
            return 0
        return pj.PJMEDIA_FILE_NO_LOOP

    def _dispose_player(self) -> None:
        if self._player is None:
            return
        for aud in self._call_audios.values():
            try:
                self._player.stopTransmit(aud)
            except pj.Error:
                pass
        self._player = None

    def _reload_stream(self) -> None:
        self._dispose_player()
        if not self.paths or self._index >= len(self.paths):
            self._app.notify_playback_changed()
            return
        path = self.paths[self._index]
        try:
            self._player = TrackAudioPlayer(self._eof)
            self._player.createPlayer(path, self._player_options())
        except pj.Error:
            self._player = None
            self._app.log(f"无法打开音频文件: {path}")
        self._sync_transmit()
        self._app.notify_playback_changed()

    def _sync_transmit(self) -> None:
        if self._player is None or not self._call_audios:
            return
        for aud in self._call_audios.values():
            if self.paused:
                try:
                    self._player.stopTransmit(aud)
                except pj.Error:
                    pass
            else:
                try:
                    self._player.startTransmit(aud)
                except pj.Error as e:
                    self._app.log(f"startTransmit 失败: {e}")

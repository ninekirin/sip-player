"""pjsua2 Endpoint、注册账号、来电接听与 DTMF。"""

from __future__ import annotations

import queue
import threading
from typing import Callable

import pjsua2 as pj

from src.playback import PlaybackController


class SipCall(pj.Call):
    def __init__(self, acc: SipAccount, call_id: int, app: SipApp, session_id: int) -> None:
        pj.Call.__init__(self, acc, call_id)
        self._app = app
        self.session_id = session_id

    def onCallState(self, prm: pj.OnCallStateParam) -> None:
        ci = self.getInfo()
        self._app.log(f"通话状态: {ci.stateText}")
        if ci.state == pj.PJSIP_INV_STATE_DISCONNECTED:
            self._app.on_call_disconnected(self)

    def onCallMediaState(self, prm: pj.OnCallMediaStateParam) -> None:
        ci = self.getInfo()
        for i in range(len(ci.media)):
            mi = ci.media[i]
            if mi.type == pj.PJMEDIA_TYPE_AUDIO and mi.status == pj.PJSUA_CALL_MEDIA_ACTIVE:
                aud = self.getAudioMedia(i)
                self._app.playback.add_call_audio(self.session_id, aud)
                return

    def onDtmfDigit(self, prm: pj.OnDtmfDigitParam) -> None:
        d = prm.digit
        self._app.log(f"DTMF: {d}")
        self._app.handle_dtmf(d)


class SipAccount(pj.Account):
    def __init__(self, app: SipApp) -> None:
        pj.Account.__init__(self)
        self._app = app

    def onRegState(self, prm: pj.OnRegStateParam) -> None:
        ai = self.getInfo()
        self._app.log(
            f"注册: code={ai.regStatus} {ai.regStatusText} "
            f"active={ai.regIsActive} expires={ai.regExpiresSec}s"
        )
        self._app.notify_reg_changed()

    def onIncomingCall(self, prm: pj.OnIncomingCallParam) -> None:
        sid = self._app.next_session_id()
        c = SipCall(self, prm.callId, self._app, sid)
        self._app.add_call(c)
        op = pj.CallOpParam(True)
        op.statusCode = pj.PJSIP_SC_OK
        c.answer(op)
        self._app.log(f"来电已自动接听 (会话 {sid})")


class SipApp:
    """整合 Endpoint、播放控制与 UI 通知。"""

    def __init__(self) -> None:
        self.playback = PlaybackController(self)
        self._ep = pj.Endpoint()
        self._ep.libCreate()
        self._acc: SipAccount | None = None
        self._active_calls: dict[int, SipCall] = {}
        self._next_sid = 0
        self._started = False
        self._reg_cb: Callable[[], None] | None = None
        self._playback_cb: Callable[[], None] | None = None
        self._pending_logs: queue.Queue[str] = queue.Queue()
        self._log_lock = threading.Lock()

    def set_ui_callbacks(
        self,
        reg_changed: Callable[[], None],
        playback_changed: Callable[[], None],
    ) -> None:
        self._reg_cb = reg_changed
        self._playback_cb = playback_changed

    def log(self, msg: str) -> None:
        with self._log_lock:
            self._pending_logs.put(msg)

    def drain_logs(self) -> list[str]:
        out: list[str] = []
        with self._log_lock:
            while True:
                try:
                    out.append(self._pending_logs.get_nowait())
                except queue.Empty:
                    break
        return out

    def notify_reg_changed(self) -> None:
        if self._reg_cb:
            self._reg_cb()

    def notify_playback_changed(self) -> None:
        if self._playback_cb:
            self._playback_cb()

    def start_stack(self) -> None:
        if self._started:
            return
        ep_cfg = pj.EpConfig()
        ep_cfg.uaConfig.threadCnt = 0
        ep_cfg.uaConfig.mainThreadOnly = True
        self._ep.libInit(ep_cfg)
        self._ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, pj.TransportConfig())
        self._ep.libStart()
        self._ep.audDevManager().setNullDev()
        self._started = True
        self.log("PJSIP 已启动（空音频设备，仅向对端送音）")

    def shutdown_stack(self) -> None:
        if not self._started:
            return
        self.playback.detach_all_call_audio()
        self._active_calls.clear()
        if self._acc:
            try:
                self._acc.shutdown()
            except pj.Error:
                pass
            self._acc = None
        self._ep.libDestroy()
        self._started = False

    def register_account(
        self,
        sip_id: str,
        registrar: str,
        username: str,
        password: str,
    ) -> None:
        if not self._started:
            self.start_stack()
        if self._acc:
            try:
                self._acc.shutdown()
            except pj.Error:
                pass
            self._acc = None

        cfg = pj.AccountConfig()
        cfg.idUri = sip_id
        cfg.regConfig.registrarUri = registrar
        cred = pj.AuthCredInfo("digest", "*", username, 0, password)
        cfg.sipConfig.authCreds.clear()
        cfg.sipConfig.authCreds.append(cred)

        self._acc = SipAccount(self)
        self._acc.create(cfg)
        self.log(f"正在注册 {registrar} …")

    def unregister(self) -> None:
        if self._acc:
            self._acc.setRegistration(False)
            self.log("已请求注销")

    def next_session_id(self) -> int:
        sid = self._next_sid
        self._next_sid += 1
        return sid

    def add_call(self, call: SipCall) -> None:
        self._active_calls[call.session_id] = call

    def on_call_disconnected(self, call: SipCall) -> None:
        if call.session_id in self._active_calls:
            del self._active_calls[call.session_id]
            self.playback.remove_call_audio(call.session_id)
            self.log(f"通话已结束 (会话 {call.session_id})")

    def handle_dtmf(self, digit: str) -> None:
        if digit == "1":
            self.playback.next_track()
        elif digit == "2":
            self.playback.toggle_pause()
        elif digit == "3":
            self.playback.cycle_mode()
        elif digit == "4":
            self.playback.prev_track()

    def poll(self) -> None:
        self._ep.libHandleEvents(10)

    def registration_status_text(self) -> str:
        if not self._acc or not self._acc.isValid():
            return "未注册"
        ai = self._acc.getInfo()
        if ai.regIsActive:
            return f"已注册 ({ai.regExpiresSec}s)"
        return f"未成功: {ai.regStatus} {ai.regStatusText}"

    def hangup_call(self) -> None:
        if not self._active_calls:
            self.log("当前无活跃通话")
            return
        for call in list(self._active_calls.values()):
            try:
                if call.isActive():
                    prm = pj.CallOpParam(True)
                    call.hangup(prm)
            except pj.Error:
                pass
        self.log("已发送挂断全部")

    def hangup_call_by_id(self, session_id: int) -> None:
        call = self._active_calls.get(session_id)
        if call:
            try:
                if call.isActive():
                    prm = pj.CallOpParam(True)
                    call.hangup(prm)
                    self.log(f"已挂断会话 {session_id}")
            except pj.Error as e:
                self.log(f"挂断会话 {session_id} 失败: {e}")

    def get_calls_info(self) -> list[dict]:
        result: list[dict] = []
        for sid, call in list(self._active_calls.items()):
            try:
                ci = call.getInfo()
                result.append({
                    "session_id": sid,
                    "remote_uri": ci.remoteUri,
                    "state": ci.stateText,
                    "duration": ci.connectDuration.sec,
                })
            except pj.Error:
                pass
        return result

"""界面文案国际化：默认中文 msgid，英文在 _EN 表中翻译。"""

from __future__ import annotations

import locale
import os
from typing import Final

# 中文为 gettext 风格的 msgid；切换到英文时使用下表。
_EN: Final[dict[str, str]] = {
    "SIP 播放器": "SIP Player",
    "SIP 注册": "SIP registration",
    "账号 URI (idUri)": "Account URI (idUri)",
    "注册服务器": "Registrar",
    "认证用户名": "Auth username",
    "密码": "Password",
    "注册": "Register",
    "注销": "Unregister",
    "挂断来电": "Hang up incoming",
    "会话管理": "Session manager",
    "未注册": "Not registered",
    "曲目（导入时自动转为 16-bit 单声道 WAV）": "Tracks (import converts to 16-bit mono WAV)",
    "添加文件…": "Add files…",
    "移除所选": "Remove selected",
    "上一首": "Previous",
    "下一首": "Next",
    "播放/暂停": "Play / pause",
    "切换模式": "Cycle mode",
    "来电 DTMF（IVR）": "Incoming DTMF (IVR)",
    "1=下一首  2=播放/暂停  3=循环顺序/列表循环/单曲循环/随机  4=上一首": (
        "1=next  2=play/pause  3=seq/list loop/single/shuffle  4=previous"
    ),
    "日志": "Log",
    "提示": "Notice",
    "请填写账号 URI 与注册服务器": "Please fill in account URI and registrar.",
    "错误": "Error",
    "注册异常: {e}": "Register error: {e}",
    "未找到 ffmpeg": "ffmpeg not found",
    "导入转码需要系统已安装 ffmpeg 并在 PATH 中可用。\n"
    "例如 macOS: brew install ffmpeg": (
        "Import requires ffmpeg installed and on PATH.\n"
        "e.g. macOS: brew install ffmpeg"
    ),
    "选择音频文件": "Choose audio files",
    "常见音频": "Common audio",
    "全部": "All files",
    "转码失败": "Transcode failed",
    "转码失败 {src}: {e}": "Transcode failed {src}: {e}",
    "已导入: {name}": "Imported: {name}",
    "poll 错误: {e}": "poll error: {e}",
    "远端": "Remote",
    "状态": "State",
    "时长(秒)": "Duration (s)",
    "挂断所选": "Hang up selected",
    "挂断全部": "Hang up all",
    "刷新": "Refresh",
    "界面语言": "UI language",
    "中文": "Chinese",
    "English": "English",
    "无曲目（请添加 16-bit PCM 单声道 WAV）": "No tracks (add 16-bit PCM mono WAV)",
    "顺序": "Sequential",
    "列表循环": "List loop",
    "单曲循环": "Single loop",
    "随机": "Shuffle",
    "暂停": "Paused",
    "播放": "Playing",
    "{ps} | {name} | 模式: {mode_s} | [{idx}/{total}]": "{ps} | {name} | mode: {mode_s} | [{idx}/{total}]",
    "顺序模式：最后一首已结束": "Sequential mode: last track finished",
    "无法打开音频文件: {path}": "Cannot open audio file: {path}",
    "startTransmit 失败: {e}": "startTransmit failed: {e}",
    "通话状态: {text}": "Call state: {text}",
    "注册: code={code} {text} active={active} expires={exp}s": (
        "Registration: code={code} {text} active={active} expires={exp}s"
    ),
    "来电已自动接听 (会话 {sid})": "Incoming call answered (session {sid})",
    "PJSIP 已启动（空音频设备，仅向对端送音）": (
        "PJSIP started (null audio device, transmit to peer only)"
    ),
    "正在注册 {registrar} …": "Registering {registrar} …",
    "已请求注销": "Unregister requested",
    "通话已结束 (会话 {sid})": "Call ended (session {sid})",
    "已注册 ({exp}s)": "Registered ({exp}s)",
    "未成功: {code} {text}": "Not successful: {code} {text}",
    "WAV": "WAV",
    "MP3": "MP3",
    "当前无活跃通话": "No active calls",
    "已发送挂断全部": "Hangup sent for all calls",
    "已挂断会话 {sid}": "Hung up session {sid}",
    "挂断会话 {sid} 失败: {e}": "Hangup session {sid} failed: {e}",
    "DTMF: {d}": "DTMF: {d}",
    "当前解释器未编译 Tcl/Tk（缺少 _tkinter）。\n"
    "在 macOS 上可安装 python-tk，或换用带 Tk 的 Python 再运行。": (
        "This Python build has no Tcl/Tk (_tkinter missing).\n"
        "On macOS install python-tk, or use a Python build that includes Tk."
    ),
}

_current_lang: str = "zh_CN"


def normalize_lang(code: str | None) -> str:
    if not code:
        return "zh_CN"
    c = code.strip().replace("-", "_")
    cl = c.lower()
    if cl.startswith("en"):
        return "en_US"
    if cl.startswith("zh"):
        return "zh_CN"
    return c


def detect_lang() -> str:
    env = os.environ.get("SIP_PLAYER_LANG") or os.environ.get("LANG") or ""
    if env:
        # LANG may be zh_CN.UTF-8
        part = env.split(".")[0].strip()
        if part:
            return normalize_lang(part)
    try:
        loc, _ = locale.getlocale(locale.LC_MESSAGES)
        if loc:
            return normalize_lang(loc)
    except (AttributeError, ValueError, OSError):
        pass
    return "zh_CN"


def set_language(code: str | None) -> None:
    global _current_lang
    _current_lang = normalize_lang(code) if code else detect_lang()


def get_language() -> str:
    return _current_lang


def _(message: str) -> str:
    if _current_lang.startswith("en"):
        return _EN.get(message, message)
    return message


def translate_fmt(template: str, **kwargs: object) -> str:
    """先按语言选模板再 format（模板需在 _EN 中有对应键）。"""
    t = _(template)
    return t.format(**kwargs)

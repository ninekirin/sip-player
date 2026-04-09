"""简易 Tk 界面：SIP 参数、曲目列表、日志与状态。"""

from __future__ import annotations

import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from src.audio_import import convert_to_playback_wav, ffmpeg_available
from src.i18n import _, get_language, set_language, translate_fmt
from src.persistence import (
    PersistedSettings,
    ensure_imports_dir,
    load_settings,
    save_settings,
)
from src.playback import PlayMode
from src.sip_stack import SipApp


class MainWindow:
    def __init__(self) -> None:
        self.app = SipApp()
        self.root = tk.Tk()
        self.root.minsize(520, 480)

        self._last_save_time = time.monotonic()
        self.var_ui_locale = tk.StringVar(value=get_language())

        self._build_form()
        self._restore_settings()
        self.app.set_ui_callbacks(
            reg_changed=self._refresh_reg_label,
            playback_changed=self._refresh_playback_label,
        )

    def _audio_filetypes(self) -> list[tuple[str, str]]:
        return [
            (_("常见音频"), "*.wav *.mp3 *.m4a *.flac *.ogg *.aac *.wma"),
            (_("WAV"), "*.wav"),
            (_("MP3"), "*.mp3"),
            (_("全部"), "*.*"),
        ]

    def _reapply_i18n(self) -> None:
        self.root.title(_("SIP 播放器"))
        self._lf_reg.config(text=_("SIP 注册"))
        self._lf_tracks.config(text=_("曲目（导入时自动转为 16-bit 单声道 WAV）"))
        self._lf_ivr.config(text=_("来电 DTMF（IVR）"))
        self._lf_log.config(text=_("日志"))
        self._lbl_lang.config(text=_("界面语言"))
        self._lbl_id_uri.config(text=_("账号 URI (idUri)"))
        self._lbl_registrar.config(text=_("注册服务器"))
        self._lbl_user.config(text=_("认证用户名"))
        self._lbl_pass.config(text=_("密码"))
        self._btn_register.config(text=_("注册"))
        self._btn_unregister.config(text=_("注销"))
        self._btn_hangup.config(text=_("挂断来电"))
        self._btn_sessions.config(text=_("会话管理"))
        self._btn_add.config(text=_("添加文件…"))
        self._btn_remove.config(text=_("移除所选"))
        self._btn_prev.config(text=_("上一首"))
        self._btn_next.config(text=_("下一首"))
        self._btn_pause.config(text=_("播放/暂停"))
        self._btn_mode.config(text=_("切换模式"))
        self._lbl_ivr_hint.config(
            text=_(
                "1=下一首  2=播放/暂停  3=循环顺序/列表循环/单曲循环/随机  4=上一首"
            ),
        )
        self._refresh_reg_label()
        self._refresh_playback_label()

    def _on_ui_locale(self, _event: tk.Event | None = None) -> None:
        code = self.var_ui_locale.get().strip()
        set_language(code)
        self._reapply_i18n()
        try:
            self._save_settings()
        except OSError:
            pass

    def _build_form(self) -> None:
        pad = {"padx": 6, "pady": 4}
        self._lf_reg = ttk.LabelFrame(self.root, text=_("SIP 注册"))
        self._lf_reg.pack(fill=tk.X, **pad)
        f = self._lf_reg

        lang_row = ttk.Frame(f)
        lang_row.grid(row=0, column=0, columnspan=2, sticky=tk.W, **pad)
        self._lbl_lang = ttk.Label(lang_row, text=_("界面语言"))
        self._lbl_lang.pack(side=tk.LEFT, padx=(0, 8))
        self._cb_locale = ttk.Combobox(
            lang_row,
            textvariable=self.var_ui_locale,
            values=("zh_CN", "en_US"),
            state="readonly",
            width=10,
        )
        self._cb_locale.pack(side=tk.LEFT)
        self._cb_locale.bind("<<ComboboxSelected>>", self._on_ui_locale)

        self._lbl_id_uri = ttk.Label(f, text=_("账号 URI (idUri)"))
        self._lbl_id_uri.grid(row=1, column=0, sticky=tk.W, **pad)
        self.var_id_uri = tk.StringVar(value="sip:1000@192.168.1.1")
        ttk.Entry(f, textvariable=self.var_id_uri, width=42).grid(row=1, column=1, **pad)

        self._lbl_registrar = ttk.Label(f, text=_("注册服务器"))
        self._lbl_registrar.grid(row=2, column=0, sticky=tk.W, **pad)
        self.var_registrar = tk.StringVar(value="sip:192.168.1.1")
        ttk.Entry(f, textvariable=self.var_registrar, width=42).grid(row=2, column=1, **pad)

        self._lbl_user = ttk.Label(f, text=_("认证用户名"))
        self._lbl_user.grid(row=3, column=0, sticky=tk.W, **pad)
        self.var_user = tk.StringVar(value="1000")
        ttk.Entry(f, textvariable=self.var_user, width=42).grid(row=3, column=1, **pad)

        self._lbl_pass = ttk.Label(f, text=_("密码"))
        self._lbl_pass.grid(row=4, column=0, sticky=tk.W, **pad)
        self.var_pass = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_pass, width=42, show="*").grid(row=4, column=1, **pad)

        bf = ttk.Frame(f)
        bf.grid(row=5, column=0, columnspan=2, **pad)
        self._btn_register = ttk.Button(bf, text=_("注册"), command=self._on_register)
        self._btn_register.pack(side=tk.LEFT, padx=4)
        self._btn_unregister = ttk.Button(bf, text=_("注销"), command=self._on_unregister)
        self._btn_unregister.pack(side=tk.LEFT, padx=4)
        self._btn_hangup = ttk.Button(bf, text=_("挂断来电"), command=self._on_hangup)
        self._btn_hangup.pack(side=tk.LEFT, padx=4)
        self._btn_sessions = ttk.Button(bf, text=_("会话管理"), command=self._open_session_manager)
        self._btn_sessions.pack(side=tk.LEFT, padx=4)

        self.lbl_reg = ttk.Label(f, text=_("未注册"))
        self.lbl_reg.grid(row=6, column=0, columnspan=2, sticky=tk.W, **pad)

        self._lf_tracks = ttk.LabelFrame(
            self.root,
            text=_("曲目（导入时自动转为 16-bit 单声道 WAV）"),
        )
        m = self._lf_tracks
        m.pack(fill=tk.BOTH, expand=True, **pad)

        row = ttk.Frame(m)
        row.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        left = ttk.Frame(row)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.list_tracks = tk.Listbox(left, height=8, selectmode=tk.EXTENDED)
        sb = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.list_tracks.yview)
        self.list_tracks.config(yscrollcommand=sb.set)
        self.list_tracks.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.list_tracks.bind("<Double-1>", self._on_track_double_click)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        mf = ttk.Frame(row)
        mf.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        self._btn_add = ttk.Button(mf, text=_("添加文件…"), command=self._add_files)
        self._btn_add.pack(fill=tk.X, pady=2)
        self._btn_remove = ttk.Button(mf, text=_("移除所选"), command=self._remove_selected)
        self._btn_remove.pack(fill=tk.X, pady=2)
        self._btn_prev = ttk.Button(mf, text=_("上一首"), command=self._prev)
        self._btn_prev.pack(fill=tk.X, pady=2)
        self._btn_next = ttk.Button(mf, text=_("下一首"), command=self._next)
        self._btn_next.pack(fill=tk.X, pady=2)
        self._btn_pause = ttk.Button(mf, text=_("播放/暂停"), command=self._toggle_pause)
        self._btn_pause.pack(fill=tk.X, pady=2)
        self._btn_mode = ttk.Button(mf, text=_("切换模式"), command=self._cycle_mode)
        self._btn_mode.pack(fill=tk.X, pady=2)

        self.lbl_play = ttk.Label(self.root, text="")
        self.lbl_play.pack(fill=tk.X, **pad)

        self._lf_ivr = ttk.LabelFrame(self.root, text=_("来电 DTMF（IVR）"))
        ivr = self._lf_ivr
        ivr.pack(fill=tk.X, **pad)
        self._lbl_ivr_hint = ttk.Label(
            ivr,
            text=_(
                "1=下一首  2=播放/暂停  3=循环顺序/列表循环/单曲循环/随机  4=上一首"
            ),
            wraplength=500,
        )
        self._lbl_ivr_hint.pack(anchor=tk.W, **pad)

        self._lf_log = ttk.LabelFrame(self.root, text=_("日志"))
        logf = self._lf_log
        logf.pack(fill=tk.BOTH, expand=True, **pad)
        self.txt_log = scrolledtext.ScrolledText(logf, height=10, state=tk.DISABLED)
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.root.title(_("SIP 播放器"))
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _append_log(self, msg: str) -> None:
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def _on_register(self) -> None:
        sid = self.var_id_uri.get().strip()
        reg = self.var_registrar.get().strip()
        user = self.var_user.get().strip()
        pwd = self.var_pass.get()
        if not sid or not reg:
            messagebox.showwarning(_("提示"), _("请填写账号 URI 与注册服务器"))
            return
        try:
            self.app.register_account(sid, reg, user or sid.split(":")[1].split("@")[0], pwd)
        except Exception as e:
            messagebox.showerror(_("错误"), str(e))
            self._append_log(translate_fmt("注册异常: {e}", e=e))

    def _on_unregister(self) -> None:
        try:
            self.app.unregister()
        except Exception as e:
            messagebox.showerror(_("错误"), str(e))

    def _on_hangup(self) -> None:
        try:
            self.app.hangup_call()
        except Exception as e:
            messagebox.showerror(_("错误"), str(e))

    def _on_track_double_click(self, event: tk.Event) -> None:
        sel = self.list_tracks.curselection()
        if sel:
            self.app.playback.jump_to_track(sel[0])

    def _open_session_manager(self) -> None:
        SessionManagerDialog(self.root, self.app)

    def _sync_track_list_to_controller(self) -> None:
        paths = [self.list_tracks.get(i) for i in range(self.list_tracks.size())]
        self.app.playback.set_tracks(paths)

    def _restore_settings(self) -> None:
        ensure_imports_dir()
        s = load_settings()
        self.var_ui_locale.set(s.ui_locale)
        set_language(s.ui_locale)
        self._reapply_i18n()
        self.var_id_uri.set(s.id_uri)
        self.var_registrar.set(s.registrar)
        self.var_user.set(s.username)
        self.var_pass.set(s.password)
        for t in s.tracks:
            if Path(t).is_file():
                self.list_tracks.insert(tk.END, t)
        self.app.playback.mode = PlayMode(int(s.play_mode) % 4)

    def _save_settings(self) -> None:
        tracks = [self.list_tracks.get(i) for i in range(self.list_tracks.size())]
        save_settings(
            PersistedSettings(
                id_uri=self.var_id_uri.get().strip(),
                registrar=self.var_registrar.get().strip(),
                username=self.var_user.get().strip(),
                password=self.var_pass.get(),
                tracks=tracks,
                play_mode=int(self.app.playback.mode),
                ui_locale=self.var_ui_locale.get().strip() or "zh_CN",
            )
        )

    def _add_files(self) -> None:
        if not ffmpeg_available():
            messagebox.showerror(
                _("未找到 ffmpeg"),
                _(
                    "导入转码需要系统已安装 ffmpeg 并在 PATH 中可用。\n"
                    "例如 macOS: brew install ffmpeg"
                ),
            )
            return
        dest_dir = ensure_imports_dir()
        files = filedialog.askopenfilenames(
            title=_("选择音频文件"),
            filetypes=self._audio_filetypes(),
        )
        for f in files:
            src = Path(f)
            try:
                out = convert_to_playback_wav(src, dest_dir)
            except Exception as e:
                messagebox.showerror(_("转码失败"), f"{src.name}\n{e}")
                self._append_log(translate_fmt("转码失败 {src}: {e}", src=src, e=e))
                continue
            self.list_tracks.insert(tk.END, str(out))
            self._append_log(translate_fmt("已导入: {name}", name=out.name))
        self._sync_track_list_to_controller()
        self._save_settings()

    def _remove_selected(self) -> None:
        sel = list(self.list_tracks.curselection())
        for i in reversed(sel):
            self.list_tracks.delete(i)
        self._sync_track_list_to_controller()
        self._save_settings()

    def _prev(self) -> None:
        self.app.playback.prev_track()

    def _next(self) -> None:
        self.app.playback.next_track()

    def _toggle_pause(self) -> None:
        self.app.playback.toggle_pause()

    def _cycle_mode(self) -> None:
        self.app.playback.cycle_mode()
        self._save_settings()

    def _refresh_reg_label(self) -> None:
        self.lbl_reg.config(text=self.app.registration_status_text())

    def _refresh_playback_label(self) -> None:
        self.lbl_play.config(text=self.app.playback.status_line())

    def _poll(self) -> None:
        try:
            self.app.poll()
            for line in self.app.drain_logs():
                self._append_log(line)
        except Exception as e:
            self._append_log(translate_fmt("poll 错误: {e}", e=e))
        self._refresh_reg_label()
        self._refresh_playback_label()
        now = time.monotonic()
        if now - self._last_save_time >= 30:
            self._last_save_time = now
            try:
                self._save_settings()
            except OSError:
                pass
        self.root.after(40, self._poll)

    def _on_close(self) -> None:
        try:
            self._save_settings()
        except OSError:
            pass
        try:
            self.app.shutdown_stack()
        except Exception:
            pass
        self.root.destroy()

    def run(self) -> None:
        self.app.start_stack()
        self._sync_track_list_to_controller()
        self._poll()
        self.root.mainloop()


class SessionManagerDialog:
    """管理所有活跃 SIP 会话的弹窗。"""

    def __init__(self, parent: tk.Tk, app: SipApp) -> None:
        self._app = app
        self._win = tk.Toplevel(parent)
        self._win.title(_("会话管理"))
        self._win.minsize(420, 260)
        self._win.transient(parent)

        self._tree = ttk.Treeview(
            self._win,
            columns=("remote", "state", "duration"),
            show="headings",
            height=8,
        )
        self._tree.heading("remote", text=_("远端"))
        self._tree.heading("state", text=_("状态"))
        self._tree.heading("duration", text=_("时长(秒)"))
        self._tree.column("remote", width=220)
        self._tree.column("state", width=100)
        self._tree.column("duration", width=80)
        self._tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        bf = ttk.Frame(self._win)
        bf.pack(fill=tk.X, padx=6, pady=(0, 6))
        ttk.Button(bf, text=_("挂断所选"), command=self._hangup_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text=_("挂断全部"), command=self._hangup_all).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text=_("刷新"), command=self._refresh).pack(side=tk.LEFT, padx=4)

        self._refresh()
        self._poll_id: str | None = self._win.after(1000, self._auto_refresh)
        self._win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _refresh(self) -> None:
        prev_sel = set(self._tree.selection())
        for item in self._tree.get_children():
            self._tree.delete(item)
        for info in self._app.get_calls_info():
            iid = str(info["session_id"])
            self._tree.insert(
                "",
                tk.END,
                iid=iid,
                values=(info["remote_uri"], info["state"], info["duration"]),
            )
            if iid in prev_sel:
                self._tree.selection_add(iid)

    def _auto_refresh(self) -> None:
        self._refresh()
        self._poll_id = self._win.after(1000, self._auto_refresh)

    def _hangup_selected(self) -> None:
        for item in self._tree.selection():
            self._app.hangup_call_by_id(int(item))
        self._win.after(500, self._refresh)

    def _hangup_all(self) -> None:
        self._app.hangup_call()
        self._win.after(500, self._refresh)

    def _on_close(self) -> None:
        if self._poll_id:
            self._win.after_cancel(self._poll_id)
        self._win.destroy()


def run_ui() -> None:
    MainWindow().run()

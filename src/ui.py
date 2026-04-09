"""简易 Tk 界面：SIP 参数、曲目列表、日志与状态。"""

from __future__ import annotations

import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from src.audio_import import convert_to_playback_wav, ffmpeg_available
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
        self.root.title("SIP Player")
        self.root.minsize(520, 480)

        self._last_save_time = time.monotonic()

        self._build_form()
        self._restore_settings()
        self.app.set_ui_callbacks(
            reg_changed=self._refresh_reg_label,
            playback_changed=self._refresh_playback_label,
        )

    def _build_form(self) -> None:
        pad = {"padx": 6, "pady": 4}
        f = ttk.LabelFrame(self.root, text="SIP 注册")
        f.pack(fill=tk.X, **pad)

        ttk.Label(f, text="账号 URI (idUri)").grid(row=0, column=0, sticky=tk.W, **pad)
        self.var_id_uri = tk.StringVar(value="sip:1000@192.168.1.1")
        ttk.Entry(f, textvariable=self.var_id_uri, width=42).grid(row=0, column=1, **pad)

        ttk.Label(f, text="注册服务器").grid(row=1, column=0, sticky=tk.W, **pad)
        self.var_registrar = tk.StringVar(value="sip:192.168.1.1")
        ttk.Entry(f, textvariable=self.var_registrar, width=42).grid(row=1, column=1, **pad)

        ttk.Label(f, text="认证用户名").grid(row=2, column=0, sticky=tk.W, **pad)
        self.var_user = tk.StringVar(value="1000")
        ttk.Entry(f, textvariable=self.var_user, width=42).grid(row=2, column=1, **pad)

        ttk.Label(f, text="密码").grid(row=3, column=0, sticky=tk.W, **pad)
        self.var_pass = tk.StringVar()
        ttk.Entry(f, textvariable=self.var_pass, width=42, show="*").grid(row=3, column=1, **pad)

        bf = ttk.Frame(f)
        bf.grid(row=4, column=0, columnspan=2, **pad)
        ttk.Button(bf, text="注册", command=self._on_register).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="注销", command=self._on_unregister).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="挂断来电", command=self._on_hangup).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="会话管理", command=self._open_session_manager).pack(side=tk.LEFT, padx=4)

        self.lbl_reg = ttk.Label(f, text="未注册")
        self.lbl_reg.grid(row=5, column=0, columnspan=2, sticky=tk.W, **pad)

        m = ttk.LabelFrame(self.root, text="曲目（导入时自动转为 16-bit 单声道 WAV）")
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
        ttk.Button(mf, text="添加文件…", command=self._add_files).pack(fill=tk.X, pady=2)
        ttk.Button(mf, text="移除所选", command=self._remove_selected).pack(fill=tk.X, pady=2)
        ttk.Button(mf, text="上一首", command=self._prev).pack(fill=tk.X, pady=2)
        ttk.Button(mf, text="下一首", command=self._next).pack(fill=tk.X, pady=2)
        ttk.Button(mf, text="播放/暂停", command=self._toggle_pause).pack(fill=tk.X, pady=2)
        ttk.Button(mf, text="切换模式", command=self._cycle_mode).pack(fill=tk.X, pady=2)

        self.lbl_play = ttk.Label(self.root, text="")
        self.lbl_play.pack(fill=tk.X, **pad)

        ivr = ttk.LabelFrame(self.root, text="来电 DTMF（IVR）")
        ivr.pack(fill=tk.X, **pad)
        ttk.Label(
            ivr,
            text="1=下一首  2=播放/暂停  3=循环顺序/列表循环/单曲循环/随机  4=上一首",
            wraplength=500,
        ).pack(anchor=tk.W, **pad)

        logf = ttk.LabelFrame(self.root, text="日志")
        logf.pack(fill=tk.BOTH, expand=True, **pad)
        self.txt_log = scrolledtext.ScrolledText(logf, height=10, state=tk.DISABLED)
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

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
            messagebox.showwarning("提示", "请填写账号 URI 与注册服务器")
            return
        try:
            self.app.register_account(sid, reg, user or sid.split(":")[1].split("@")[0], pwd)
        except Exception as e:
            messagebox.showerror("错误", str(e))
            self._append_log(f"注册异常: {e}")

    def _on_unregister(self) -> None:
        try:
            self.app.unregister()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def _on_hangup(self) -> None:
        try:
            self.app.hangup_call()
        except Exception as e:
            messagebox.showerror("错误", str(e))

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
        self.var_id_uri.set(s.id_uri)
        self.var_registrar.set(s.registrar)
        self.var_user.set(s.username)
        self.var_pass.set(s.password)
        for t in s.tracks:
            if Path(t).is_file():
                self.list_tracks.insert(tk.END, t)
        self.app.playback.mode = PlayMode(int(s.play_mode) % 4)
        # 曲目同步在 start_stack() 之后执行（createPlayer 需要库已初始化）

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
            )
        )

    def _add_files(self) -> None:
        if not ffmpeg_available():
            messagebox.showerror(
                "未找到 ffmpeg",
                "导入转码需要系统已安装 ffmpeg 并在 PATH 中可用。\n"
                "例如 macOS: brew install ffmpeg",
            )
            return
        dest_dir = ensure_imports_dir()
        files = filedialog.askopenfilenames(
            title="选择音频文件",
            filetypes=[
                ("常见音频", "*.wav *.mp3 *.m4a *.flac *.ogg *.aac *.wma"),
                ("WAV", "*.wav"),
                ("MP3", "*.mp3"),
                ("全部", "*.*"),
            ],
        )
        for f in files:
            src = Path(f)
            try:
                out = convert_to_playback_wav(src, dest_dir)
            except Exception as e:
                messagebox.showerror("转码失败", f"{src.name}\n{e}")
                self._append_log(f"转码失败 {src}: {e}")
                continue
            self.list_tracks.insert(tk.END, str(out))
            self._append_log(f"已导入: {out.name}")
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
            self._append_log(f"poll 错误: {e}")
        self._refresh_reg_label()
        self._refresh_playback_label()
        now = time.monotonic()
        if now - self._last_save_time >= 30:
            self._last_save_time = now
            try:
                self._save_settings()
            except Exception:
                pass
        self.root.after(40, self._poll)

    def _on_close(self) -> None:
        try:
            self._save_settings()
        except Exception:
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
        self._win.title("会话管理")
        self._win.minsize(420, 260)
        self._win.transient(parent)

        self._tree = ttk.Treeview(
            self._win,
            columns=("remote", "state", "duration"),
            show="headings",
            height=8,
        )
        self._tree.heading("remote", text="远端")
        self._tree.heading("state", text="状态")
        self._tree.heading("duration", text="时长(秒)")
        self._tree.column("remote", width=220)
        self._tree.column("state", width=100)
        self._tree.column("duration", width=80)
        self._tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        bf = ttk.Frame(self._win)
        bf.pack(fill=tk.X, padx=6, pady=(0, 6))
        ttk.Button(bf, text="挂断所选", command=self._hangup_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="挂断全部", command=self._hangup_all).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="刷新", command=self._refresh).pack(side=tk.LEFT, padx=4)

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

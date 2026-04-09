"""python -m src"""

import sys

from src.i18n import _, detect_lang, set_language
from src.persistence import load_settings


def main() -> None:
    try:
        import tkinter  # noqa: F401
    except ImportError as e:
        set_language(detect_lang())
        print(
            _(
                "当前解释器未编译 Tcl/Tk（缺少 _tkinter）。\n"
                "在 macOS 上可安装 python-tk，或换用带 Tk 的 Python 再运行。"
            ),
            file=sys.stderr,
        )
        print(e, file=sys.stderr)
        sys.exit(1)
    s = load_settings()
    set_language(s.ui_locale or detect_lang())
    from src.ui import run_ui

    run_ui()


if __name__ == "__main__":
    main()

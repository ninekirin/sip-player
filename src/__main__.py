"""python -m src"""

import sys


def main() -> None:
    try:
        import tkinter  # noqa: F401
    except ImportError as e:
        print(
            "当前解释器未编译 Tcl/Tk（缺少 _tkinter）。"
            "在 macOS 上可安装 python-tk，或换用带 Tk 的 Python 再运行。",
            file=sys.stderr,
        )
        print(e, file=sys.stderr)
        sys.exit(1)
    from src.ui import run_ui

    run_ui()


if __name__ == "__main__":
    main()

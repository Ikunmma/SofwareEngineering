"""一箭又一箭小游戏入口。"""

import tkinter as tk


WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720


def create_window() -> tk.Tk:
    """创建并配置游戏主窗口。"""
    root = tk.Tk()
    root.title("一箭又一箭")
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    root.resizable(False, False)
    root.configure(bg="#f4f7fb")
    return root


def main() -> None:
    """启动图形界面。"""
    root = create_window()
    root.mainloop()


if __name__ == "__main__":
    main()

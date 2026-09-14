"""一箭又一箭小游戏入口。"""

import tkinter as tk
from collections.abc import Callable


WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720

BACKGROUND = "#F3F6FC"
CARD = "#FFFFFF"
TEXT_PRIMARY = "#17233C"
TEXT_SECONDARY = "#63708A"
ACCENT = "#5B67F1"
ACCENT_DARK = "#454FD2"
ACCENT_SOFT = "#E9EBFF"
MINT = "#45C7A0"

FONT_FAMILY = "Microsoft YaHei UI"


class ArrowEscapeApp:
    """管理游戏窗口与页面切换。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.current_screen = ""
        self.start_button: tk.Button | None = None
        self.show_start_screen()

    def clear_screen(self) -> None:
        """清除当前页面的所有控件。"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def make_button(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        *,
        width: int = 16,
    ) -> tk.Button:
        """创建全局风格一致的主按钮。"""
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            height=2,
            font=(FONT_FAMILY, 14, "bold"),
            fg="white",
            bg=ACCENT,
            activeforeground="white",
            activebackground=ACCENT_DARK,
            relief="flat",
            bd=0,
            cursor="hand2",
        )

    def show_start_screen(self) -> None:
        """显示游戏标题、规则和开始按钮。"""
        self.clear_screen()
        self.current_screen = "start"

        canvas = tk.Canvas(
            self.root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=BACKGROUND,
            highlightthickness=0,
        )
        canvas.pack(fill="both", expand=True)

        # 柔和的背景装饰，让界面有层次但不影响阅读。
        canvas.create_oval(-120, -150, 300, 270, fill="#E4E7FF", outline="")
        canvas.create_oval(760, 525, 1080, 845, fill="#DDF7EF", outline="")
        canvas.create_rectangle(66, 60, 894, 660, fill=CARD, outline="")

        canvas.create_text(
            120,
            126,
            text="一 箭 又 一 箭",
            anchor="w",
            fill=TEXT_PRIMARY,
            font=(FONT_FAMILY, 34, "bold"),
        )
        canvas.create_text(
            122,
            184,
            text="看清方向 · 找准出路 · 清空棋盘",
            anchor="w",
            fill=TEXT_SECONDARY,
            font=(FONT_FAMILY, 14),
        )

        self._draw_rule_card(canvas, 120, 248, "1", "点击箭头", "选择你想要移出棋盘的箭头")
        self._draw_rule_card(canvas, 120, 344, "2", "检查前方", "前方没有其他箭头时才能飞出")
        self._draw_rule_card(canvas, 120, 440, "3", "小心碰撞", "被阻挡会消耗一次失误机会")

        # 右侧的原创箭头图形全部由 Canvas 绘制。
        canvas.create_oval(594, 178, 820, 404, fill=ACCENT_SOFT, outline="")
        canvas.create_oval(646, 230, 768, 352, fill=CARD, outline="#D6DAFA", width=3)
        canvas.create_text(
            707,
            291,
            text="↑  →\n\n←  ↓",
            fill=ACCENT,
            font=("Segoe UI Symbol", 26, "bold"),
            justify="center",
        )
        canvas.create_text(
            707,
            442,
            text="清除所有箭头即可过关",
            fill=TEXT_SECONDARY,
            font=(FONT_FAMILY, 12),
        )

        button_host = tk.Frame(canvas, bg=CARD)
        canvas.create_window(690, 525, window=button_host)
        self.start_button = self.make_button(
            button_host,
            "开始游戏  →",
            self.show_game_placeholder,
            width=15,
        )
        self.start_button.pack()

        canvas.create_text(
            480,
            628,
            text="Python + Tkinter  ·  原创练习项目",
            fill="#98A2B7",
            font=(FONT_FAMILY, 10),
        )

    @staticmethod
    def _draw_rule_card(
        canvas: tk.Canvas,
        x: int,
        y: int,
        number: str,
        title: str,
        description: str,
    ) -> None:
        """在开始页绘制一条玩法说明。"""
        canvas.create_oval(x, y, x + 44, y + 44, fill=ACCENT_SOFT, outline="")
        canvas.create_text(
            x + 22,
            y + 22,
            text=number,
            fill=ACCENT,
            font=(FONT_FAMILY, 13, "bold"),
        )
        canvas.create_text(
            x + 62,
            y + 7,
            text=title,
            anchor="nw",
            fill=TEXT_PRIMARY,
            font=(FONT_FAMILY, 13, "bold"),
        )
        canvas.create_text(
            x + 62,
            y + 34,
            text=description,
            anchor="nw",
            fill=TEXT_SECONDARY,
            font=(FONT_FAMILY, 10),
        )

    def show_game_placeholder(self) -> None:
        """验证开始按钮的页面切换，棋盘将在下一步实现。"""
        self.clear_screen()
        self.current_screen = "game"

        frame = tk.Frame(self.root, bg=BACKGROUND)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text="已进入游戏",
            font=(FONT_FAMILY, 28, "bold"),
            fg=TEXT_PRIMARY,
            bg=BACKGROUND,
        ).pack(pady=(230, 18))
        tk.Label(
            frame,
            text="棋盘与箭头将在下一个功能中加入",
            font=(FONT_FAMILY, 13),
            fg=TEXT_SECONDARY,
            bg=BACKGROUND,
        ).pack(pady=(0, 30))
        self.make_button(
            frame,
            "返回开始界面",
            self.show_start_screen,
            width=16,
        ).pack()


def create_window() -> tk.Tk:
    """创建并配置游戏主窗口。"""
    root = tk.Tk()
    root.title("一箭又一箭")
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    root.resizable(False, False)
    root.configure(bg=BACKGROUND)
    return root


def main() -> None:
    """启动图形界面。"""
    root = create_window()
    ArrowEscapeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

"""一箭又一箭小游戏入口。"""

import tkinter as tk
from collections.abc import Callable

from game_logic import DIRECTION_VECTORS, ArrowBoard
from levels import DIRECTION_SYMBOLS, LEVELS


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

DIRECTION_COLORS = {
    "up": ("#E9EBFF", "#5662E9"),
    "down": ("#E3F7F0", "#22A981"),
    "left": ("#FFF0E7", "#E77A3C"),
    "right": ("#FBE8F0", "#D9598C"),
}

DIRECTION_NAMES = {
    "up": "上",
    "down": "下",
    "left": "左",
    "right": "右",
}

FONT_FAMILY = "Microsoft YaHei UI"

BOARD_ROWS = 6
BOARD_COLS = 6
CELL_SIZE = 72
BOARD_PADDING = 20
BOARD_PIXEL_SIZE = BOARD_COLS * CELL_SIZE + BOARD_PADDING * 2
FLIGHT_STEP = 20
FLIGHT_DELAY_MS = 14
FLIGHT_STEPS = (BOARD_PIXEL_SIZE + CELL_SIZE) // FLIGHT_STEP + 1
COLLISION_DELAY_MS = 45
COLLISION_OFFSETS = (-8, 8, -7, 7, -4, 4, 0)
COLLISION_BACKGROUND = "#FFE4E4"
COLLISION_COLOR = "#D83B3B"
MAX_MISTAKES = 3


class ArrowEscapeApp:
    """管理游戏窗口与页面切换。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.current_screen = ""
        self.start_button: tk.Button | None = None
        self.board_canvas: tk.Canvas | None = None
        self.feedback_label: tk.Label | None = None
        self.arrow_count_label: tk.Label | None = None
        self.mistakes_label: tk.Label | None = None
        self.retry_button: tk.Button | None = None
        self.next_level_button: tk.Button | None = None
        self.replay_all_button: tk.Button | None = None
        self.current_level_index = 0
        self.game = ArrowBoard(LEVELS[self.current_level_index].board)
        self.selected_cell: tuple[int, int] | None = None
        self.mistakes_remaining = MAX_MISTAKES
        self.animating = False
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
        if self.animating:
            self._show_feedback("请等待动画结束后再操作", "warning")
            return
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
            self.start_new_game,
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

    def show_game_screen(self) -> None:
        """显示游戏状态栏、棋盘和操作区。"""
        self.clear_screen()
        self.current_screen = "game"

        page = tk.Frame(self.root, bg=BACKGROUND)
        page.pack(fill="both", expand=True)

        header = tk.Frame(page, bg=BACKGROUND, height=90)
        header.pack(fill="x", padx=58, pady=(30, 10))
        header.pack_propagate(False)

        tk.Label(
            header,
            text="一箭又一箭",
            font=(FONT_FAMILY, 24, "bold"),
            fg=TEXT_PRIMARY,
            bg=BACKGROUND,
        ).pack(side="left", anchor="center")

        tk.Label(
            header,
            text=f"第 {self.current_level_index + 1} 关  ·  {LEVELS[self.current_level_index].name}",
            font=(FONT_FAMILY, 14, "bold"),
            fg=ACCENT,
            bg=ACCENT_SOFT,
            padx=22,
            pady=10,
        ).pack(side="right", anchor="center")

        content = tk.Frame(page, bg=BACKGROUND)
        content.pack(fill="both", expand=True, padx=58, pady=(0, 45))

        board_panel = tk.Frame(content, bg=CARD, padx=24, pady=24)
        board_panel.pack(side="left", fill="both", expand=True)

        self.board_canvas = tk.Canvas(
            board_panel,
            width=BOARD_PIXEL_SIZE,
            height=BOARD_PIXEL_SIZE,
            bg="#F8FAFE",
            highlightthickness=0,
            cursor="hand2",
        )
        self.board_canvas.pack(expand=True)
        self.board_canvas.bind("<Button-1>", self.on_board_click)
        self.draw_board()

        sidebar = tk.Frame(content, width=240, bg=BACKGROUND)
        sidebar.pack(side="right", fill="y", padx=(24, 0))
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="游戏状态",
            font=(FONT_FAMILY, 16, "bold"),
            fg=TEXT_PRIMARY,
            bg=BACKGROUND,
            anchor="w",
        ).pack(fill="x", pady=(8, 14))

        self.arrow_count_label = self._make_status_card(
            sidebar,
            "剩余箭头",
            str(self.game.remaining_arrows()),
            ACCENT,
        )
        self.mistakes_label = self._make_status_card(
            sidebar,
            "剩余失误",
            str(self.mistakes_remaining),
            MINT,
        )

        tip = tk.Frame(sidebar, bg="#FFF8E8", padx=18, pady=16)
        tip.pack(fill="x", pady=(8, 24))
        tk.Label(
            tip,
            text="玩法提示",
            font=(FONT_FAMILY, 11, "bold"),
            fg="#9A6A16",
            bg="#FFF8E8",
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            tip,
            text="点击前方无阻挡的箭头\n就能让它飞出棋盘。",
            font=(FONT_FAMILY, 10),
            fg="#8A744D",
            bg="#FFF8E8",
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(8, 0))

        self.feedback_label = tk.Label(
            sidebar,
            text="请点击一个箭头",
            font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY,
            bg=BACKGROUND,
            justify="center",
            wraplength=210,
        )
        self.feedback_label.pack(fill="x", pady=(0, 18))

        self.make_button(
            sidebar,
            "重新开始",
            self.restart_board,
            width=14,
        ).pack(fill="x", pady=(0, 12))

        tk.Button(
            sidebar,
            text="返回主页",
            command=self.show_start_screen,
            font=(FONT_FAMILY, 11),
            fg=TEXT_SECONDARY,
            bg=BACKGROUND,
            activeforeground=ACCENT,
            activebackground=BACKGROUND,
            relief="flat",
            bd=0,
            cursor="hand2",
        ).pack()

    def start_new_game(self) -> None:
        """从开始界面进入一个全新的游戏。"""
        self.current_level_index = 0
        self.game = ArrowBoard(LEVELS[self.current_level_index].board)
        self.selected_cell = None
        self.mistakes_remaining = MAX_MISTAKES
        self.show_game_screen()

    def load_level(self, level_index: int) -> None:
        """按索引加载关卡并恢复该关的初始状态。"""
        if not 0 <= level_index < len(LEVELS):
            raise IndexError("关卡索引越界")
        if self.animating:
            raise RuntimeError("动画进行中不能切换关卡")

        self.current_level_index = level_index
        self.game = ArrowBoard(LEVELS[level_index].board)
        self.selected_cell = None
        self.mistakes_remaining = MAX_MISTAKES
        if self.current_screen == "game":
            self.show_game_screen()

    def show_level_clear(self) -> None:
        """显示当前关卡的通关结果。"""
        self.clear_screen()
        self.current_screen = "level_clear"
        is_last_level = self.current_level_index == len(LEVELS) - 1

        canvas = tk.Canvas(
            self.root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=BACKGROUND,
            highlightthickness=0,
        )
        canvas.pack(fill="both", expand=True)
        canvas.create_oval(-130, -120, 250, 260, fill="#DDF7EF", outline="")
        canvas.create_oval(750, 510, 1100, 860, fill=ACCENT_SOFT, outline="")
        canvas.create_rectangle(230, 105, 730, 615, fill=CARD, outline="")
        canvas.create_oval(405, 155, 555, 305, fill="#DDF7EF", outline="")
        canvas.create_text(
            480,
            230,
            text="✓",
            fill=MINT,
            font=("Segoe UI Symbol", 52, "bold"),
        )
        canvas.create_text(
            480,
            344,
            text=f"第 {self.current_level_index + 1} 关通关！",
            fill=TEXT_PRIMARY,
            font=(FONT_FAMILY, 27, "bold"),
        )
        canvas.create_text(
            480,
            394,
            text=f"你已清空“{LEVELS[self.current_level_index].name}”的所有箭头",
            fill=TEXT_SECONDARY,
            font=(FONT_FAMILY, 11),
        )

        button_host = tk.Frame(canvas, bg=CARD)
        canvas.create_window(480, 480, window=button_host)
        if is_last_level:
            button_text = "返回主页"
            button_command = self.show_start_screen
        else:
            button_text = "下一关  →"
            button_command = self.advance_to_next_level
        self.next_level_button = self.make_button(
            button_host,
            button_text,
            button_command,
            width=14,
        )
        self.next_level_button.pack()

    def advance_to_next_level(self) -> None:
        """加载下一关并返回游戏界面。"""
        next_index = self.current_level_index + 1
        if next_index >= len(LEVELS):
            self.show_start_screen()
            return
        self.load_level(next_index)
        self.show_game_screen()

    def show_all_clear(self) -> None:
        """显示全部关卡完成后的最终结果。"""
        self.clear_screen()
        self.current_screen = "all_clear"

        canvas = tk.Canvas(
            self.root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=BACKGROUND,
            highlightthickness=0,
        )
        canvas.pack(fill="both", expand=True)
        canvas.create_oval(-130, 480, 270, 880, fill="#DDF7EF", outline="")
        canvas.create_oval(740, -180, 1110, 190, fill="#FFF0CF", outline="")
        canvas.create_rectangle(210, 80, 750, 640, fill=CARD, outline="")

        canvas.create_text(
            480,
            170,
            text="★  ★  ★",
            fill="#F2B84B",
            font=("Segoe UI Symbol", 34, "bold"),
        )
        canvas.create_text(
            480,
            270,
            text="全部通关！",
            fill=TEXT_PRIMARY,
            font=(FONT_FAMILY, 32, "bold"),
        )
        canvas.create_text(
            480,
            325,
            text=f"恭喜你完成了全部 {len(LEVELS)} 个关卡",
            fill=TEXT_SECONDARY,
            font=(FONT_FAMILY, 13),
        )
        canvas.create_text(
            480,
            370,
            text="每一支箭都找到了自己的出路",
            fill=MINT,
            font=(FONT_FAMILY, 11, "bold"),
        )

        button_host = tk.Frame(canvas, bg=CARD)
        canvas.create_window(480, 470, window=button_host)
        self.replay_all_button = self.make_button(
            button_host,
            "再玩一次",
            self.start_new_game,
            width=14,
        )
        self.replay_all_button.pack()
        tk.Button(
            button_host,
            text="返回主页",
            command=self.show_start_screen,
            font=(FONT_FAMILY, 11),
            fg=TEXT_SECONDARY,
            bg=CARD,
            activeforeground=ACCENT,
            activebackground=CARD,
            relief="flat",
            bd=0,
            cursor="hand2",
        ).pack(pady=(14, 0))

    def show_game_over(self) -> None:
        """显示失误机会耗尽后的失败界面。"""
        self.clear_screen()
        self.current_screen = "game_over"

        canvas = tk.Canvas(
            self.root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=BACKGROUND,
            highlightthickness=0,
        )
        canvas.pack(fill="both", expand=True)
        canvas.create_oval(-120, 500, 260, 880, fill="#FFE8E8", outline="")
        canvas.create_oval(760, -170, 1110, 180, fill=ACCENT_SOFT, outline="")
        canvas.create_rectangle(230, 105, 730, 615, fill=CARD, outline="")
        canvas.create_oval(405, 160, 555, 310, fill="#FFE8E8", outline="")
        canvas.create_text(
            480,
            235,
            text="×",
            fill=COLLISION_COLOR,
            font=(FONT_FAMILY, 54, "bold"),
        )
        canvas.create_text(
            480,
            355,
            text="本关挑战失败",
            fill=TEXT_PRIMARY,
            font=(FONT_FAMILY, 26, "bold"),
        )
        canvas.create_text(
            480,
            402,
            text="失误机会已耗尽，观察箭头前方后再试一次吧",
            fill=TEXT_SECONDARY,
            font=(FONT_FAMILY, 11),
        )

        button_host = tk.Frame(canvas, bg=CARD)
        canvas.create_window(480, 485, window=button_host)
        self.retry_button = self.make_button(
            button_host,
            "重新挑战",
            self.retry_after_failure,
            width=14,
        )
        self.retry_button.pack()
        tk.Button(
            button_host,
            text="返回主页",
            command=self.show_start_screen,
            font=(FONT_FAMILY, 11),
            fg=TEXT_SECONDARY,
            bg=CARD,
            activeforeground=ACCENT,
            activebackground=CARD,
            relief="flat",
            bd=0,
            cursor="hand2",
        ).pack(pady=(14, 0))

    def retry_after_failure(self) -> None:
        """从失败界面恢复本关的完整初始状态。"""
        self.game.restart()
        self.selected_cell = None
        self.mistakes_remaining = MAX_MISTAKES
        self.show_game_screen()

    @staticmethod
    def _make_status_card(
        parent: tk.Misc,
        title: str,
        value: str,
        color: str,
    ) -> tk.Label:
        """创建一张棋盘侧边的状态卡片。"""
        card = tk.Frame(parent, bg=CARD, padx=18, pady=14)
        card.pack(fill="x", pady=(0, 12))
        tk.Label(
            card,
            text=title,
            font=(FONT_FAMILY, 10),
            fg=TEXT_SECONDARY,
            bg=CARD,
            anchor="w",
        ).pack(side="left")
        value_label = tk.Label(
            card,
            text=value,
            font=(FONT_FAMILY, 20, "bold"),
            fg=color,
            bg=CARD,
        )
        value_label.pack(side="right")
        return value_label

    def draw_board(self) -> None:
        """绘制 6×6 网格与当前关卡中的所有箭头。"""
        if self.board_canvas is None:
            return

        self.board_canvas.delete("all")
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                x1 = BOARD_PADDING + col * CELL_SIZE
                y1 = BOARD_PADDING + row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                fill = "#F4F6FF" if (row + col) % 2 == 0 else "#FFFFFF"
                self.board_canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=fill,
                    outline="#DDE2F1",
                    width=1,
                    tags=("cell", f"cell-{row}-{col}"),
                )

                direction = self.game.board[row][col]
                if direction is not None:
                    self._draw_arrow(row, col, direction)

    def _draw_arrow(self, row: int, col: int, direction: str) -> None:
        """在指定单元格中绘制带柔和色底的方向箭头。"""
        if self.board_canvas is None:
            return

        center_x = BOARD_PADDING + col * CELL_SIZE + CELL_SIZE / 2
        center_y = BOARD_PADDING + row * CELL_SIZE + CELL_SIZE / 2
        background_color, arrow_color = DIRECTION_COLORS[direction]
        tag = f"arrow-{row}-{col}"

        radius = 25
        is_selected = self.selected_cell == (row, col)
        self.board_canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill=background_color,
            outline=ACCENT if is_selected else "",
            width=3 if is_selected else 0,
            tags=("arrow", tag, f"arrow-bg-{row}-{col}"),
        )
        self.board_canvas.create_text(
            center_x,
            center_y - 1,
            text=DIRECTION_SYMBOLS[direction],
            fill=arrow_color,
            font=("Segoe UI Symbol", 28, "bold"),
            tags=("arrow", tag, f"arrow-symbol-{row}-{col}"),
        )

    @staticmethod
    def canvas_to_cell(x: int, y: int) -> tuple[int, int] | None:
        """把 Canvas 坐标转换为棋盘行列，边框外返回 None。"""
        board_right = BOARD_PADDING + BOARD_COLS * CELL_SIZE
        board_bottom = BOARD_PADDING + BOARD_ROWS * CELL_SIZE
        if not (BOARD_PADDING <= x < board_right):
            return None
        if not (BOARD_PADDING <= y < board_bottom):
            return None

        col = (x - BOARD_PADDING) // CELL_SIZE
        row = (y - BOARD_PADDING) // CELL_SIZE
        return int(row), int(col)

    def on_board_click(self, event: tk.Event) -> None:
        """处理鼠标点击，高亮选中的箭头并显示方向。"""
        if self.animating:
            self._show_feedback("请等待动画结束后再点击", "warning")
            return

        cell = self.canvas_to_cell(event.x, event.y)
        if cell is None:
            self._show_feedback("请点击棋盘内的箭头", "warning")
            return

        row, col = cell
        direction = self.game.board[row][col]
        if direction is None:
            self.selected_cell = None
            self.draw_board()
            self._show_feedback("这个格子里没有箭头", "warning")
            return

        self.selected_cell = cell
        if self.game.is_blocked(row, col):
            self.mistakes_remaining -= 1
            self._update_mistakes()
            self.draw_board()
            self.animating = True
            self._show_feedback(
                f"碰撞！{DIRECTION_NAMES[direction]}箭头前方有阻挡",
                "warning",
            )
            self._animate_collision(row, col)
            return

        self.draw_board()
        self.animating = True
        self._show_feedback(
            f"{DIRECTION_NAMES[direction]}箭头正在飞出棋盘……",
            "success",
        )
        self._animate_arrow_out(row, col, direction)

    def _animate_collision(
        self,
        row: int,
        col: int,
        step: int = 0,
        previous_offset: int = 0,
    ) -> None:
        """让被阻挡的箭头变红并围绕原位置水平晃动。"""
        if self.board_canvas is None or not self.board_canvas.winfo_exists():
            self.animating = False
            return

        arrow_tag = f"arrow-{row}-{col}"
        background_tag = f"arrow-bg-{row}-{col}"
        symbol_tag = f"arrow-symbol-{row}-{col}"
        target_offset = COLLISION_OFFSETS[step]
        self.board_canvas.move(arrow_tag, target_offset - previous_offset, 0)
        self.board_canvas.itemconfigure(
            background_tag,
            fill=COLLISION_BACKGROUND,
            outline=COLLISION_COLOR,
            width=3,
        )
        self.board_canvas.itemconfigure(symbol_tag, fill=COLLISION_COLOR)

        if step + 1 >= len(COLLISION_OFFSETS):
            self.root.after(
                COLLISION_DELAY_MS,
                lambda: self._complete_collision(row, col),
            )
            return

        self.root.after(
            COLLISION_DELAY_MS,
            lambda: self._animate_collision(
                row,
                col,
                step + 1,
                target_offset,
            ),
        )

    def _complete_collision(self, row: int, col: int) -> None:
        """恢复碰撞箭头的颜色和位置，保持棋盘数据不变。"""
        self.selected_cell = None
        self.animating = False
        if self.mistakes_remaining <= 0:
            self.show_game_over()
            return
        self.draw_board()
        self._show_feedback(
            f"第 {row + 1} 行第 {col + 1} 列的箭头未能飞出",
            "warning",
        )

    def _animate_arrow_out(
        self,
        row: int,
        col: int,
        direction: str,
        step: int = 0,
    ) -> None:
        """沿箭头方向逐帧移动 Canvas 图形。"""
        if self.board_canvas is None or not self.board_canvas.winfo_exists():
            self.animating = False
            return

        row_step, col_step = DIRECTION_VECTORS[direction]
        arrow_tag = f"arrow-{row}-{col}"
        self.board_canvas.move(
            arrow_tag,
            col_step * FLIGHT_STEP,
            row_step * FLIGHT_STEP,
        )

        if step + 1 >= FLIGHT_STEPS:
            self.root.after(
                FLIGHT_DELAY_MS,
                lambda: self._complete_arrow_flight(row, col, direction),
            )
            return

        self.root.after(
            FLIGHT_DELAY_MS,
            lambda: self._animate_arrow_out(row, col, direction, step + 1),
        )

    def _complete_arrow_flight(self, row: int, col: int, direction: str) -> None:
        """动画结束后更新棋盘数据和界面状态。"""
        self.game.remove_arrow(row, col)
        self.selected_cell = None
        self.animating = False
        self.draw_board()
        self._update_arrow_count()
        if self.game.remaining_arrows() == 0:
            if self.current_level_index == len(LEVELS) - 1:
                self.show_all_clear()
            else:
                self.show_level_clear()
        else:
            self._show_feedback(
                f"第 {row + 1} 行第 {col + 1} 列的{DIRECTION_NAMES[direction]}箭头已飞出",
                "success",
            )

    def _show_feedback(self, message: str, kind: str) -> None:
        """更新棋盘右侧的操作反馈文字。"""
        if self.feedback_label is None:
            return
        color = MINT if kind == "success" else "#D58A22"
        self.feedback_label.config(text=message, fg=color)

    def _update_arrow_count(self) -> None:
        """使侧边栏数字与当前棋盘同步。"""
        if self.arrow_count_label is not None:
            self.arrow_count_label.config(text=str(self.game.remaining_arrows()))

    def _update_mistakes(self) -> None:
        """使侧边栏失误数字与当前状态同步。"""
        if self.mistakes_label is not None:
            self.mistakes_label.config(text=str(self.mistakes_remaining))

    def restart_board(self) -> None:
        """将当前棋盘重新绘制为初始状态。"""
        if self.animating:
            self._show_feedback("请等待动画结束后再重新开始", "warning")
            return
        self.game.restart()
        self.selected_cell = None
        self.mistakes_remaining = MAX_MISTAKES
        self.draw_board()
        self._update_arrow_count()
        self._update_mistakes()
        self._show_feedback("棋盘已恢复，请重新选择箭头", "success")


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

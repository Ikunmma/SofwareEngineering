"""“一箭又一箭”Pygame 图形界面。"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path

import pygame

from game_logic import DIRECTION_VECTORS, ArrowBoard
from levels import DOWN, LEFT, LEVELS, RIGHT, UP


WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 720
FPS = 60
MAX_MISTAKES = 3

BACKGROUND_TOP = (239, 244, 255)
BACKGROUND_BOTTOM = (220, 230, 250)
NAVY = (29, 42, 74)
MUTED = (104, 119, 151)
WHITE = (255, 255, 255)
BLUE = (72, 105, 225)
BLUE_SOFT = (229, 235, 255)
GREEN = (51, 181, 122)
GREEN_SOFT = (226, 248, 237)
RED = (229, 78, 85)
RED_SOFT = (255, 229, 231)
YELLOW = (246, 180, 63)
YELLOW_SOFT = (255, 246, 218)
GRID = (218, 226, 244)
SHADOW = (78, 95, 139, 35)

ASSET_DIR = Path(__file__).resolve().parent / "assets" / "kenney_ui"
BOARD_ROWS = 6
BOARD_COLS = 6
CELL_SIZE = 72
BOARD_LEFT = 94
BOARD_TOP = 180
BOARD_SIZE = CELL_SIZE * BOARD_COLS

FLIGHT_SPEED = 790.0
COLLISION_DURATION = 0.48

DIRECTION_NAMES = {UP: "上", DOWN: "下", LEFT: "左", RIGHT: "右"}
DIRECTION_COLORS = {
    UP: ((229, 235, 255), BLUE, "Blue", "n"),
    DOWN: ((226, 248, 237), GREEN, "Green", "s"),
    LEFT: ((255, 246, 218), (218, 145, 28), "Yellow", "w"),
    RIGHT: ((255, 229, 231), RED, "Red", "e"),
}


def _rounded_panel(size: tuple[int, int], color: tuple[int, ...], radius: int = 24) -> pygame.Surface:
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surface, color, surface.get_rect(), border_radius=radius)
    return surface


@dataclass
class Button:
    """带 Kenney 纹理、悬停和按压效果的按钮。"""

    rect: pygame.Rect
    text: str
    color: str = "Blue"
    enabled: bool = True

    def contains(self, position: tuple[int, int]) -> bool:
        return self.enabled and self.rect.collidepoint(position)

    def draw(self, app: "ArrowEscapeApp", mouse: tuple[int, int]) -> None:
        hovered = self.contains(mouse)
        target = self.rect.move(0, 3 if hovered else 0)
        shadow = pygame.Surface((target.width, target.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (42, 55, 96, 45), shadow.get_rect(), border_radius=14)
        app.screen.blit(shadow, target.move(0, 5))

        texture = pygame.transform.smoothscale(
            app.assets[f"button_{self.color.lower()}"], target.size
        )
        if not self.enabled:
            texture = texture.copy()
            texture.fill((155, 160, 174, 170), special_flags=pygame.BLEND_RGBA_MULT)
        app.screen.blit(texture, target)
        app.draw_text(
            self.text, target.centerx, target.centery - 2, 20, WHITE,
            center=True, bold=True,
        )


class ArrowEscapeApp:
    """管理页面、游戏状态、动画和绘制。"""

    def __init__(self, *, create_display: bool = True) -> None:
        pygame.init()
        pygame.font.init()
        flags = 0 if create_display else pygame.HIDDEN
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        pygame.display.set_caption("一箭又一箭 · Arrow Escape")
        self.clock = pygame.time.Clock()
        self.running = False
        self.current_screen = "start"
        self.current_level_index = 0
        self.game = ArrowBoard(LEVELS[0].board)
        self.mistakes_remaining = MAX_MISTAKES
        self.selected_cell: tuple[int, int] | None = None
        self.animating = False
        self.animation: dict[str, object] | None = None
        self.feedback = "点击前方没有阻挡的箭头"
        self.feedback_kind = "normal"
        self.assets = self._load_assets()
        self._font_cache: dict[tuple[int, bool, bool], pygame.font.Font] = {}
        self.background = self._make_background()
        self.start_button = Button(pygame.Rect(128, 545, 230, 64), "开始闯关", "Blue")
        self.restart_button = Button(pygame.Rect(795, 485, 190, 58), "重新开始", "Blue")
        self.home_button = Button(pygame.Rect(795, 558, 190, 58), "返回主页", "Grey")
        self.next_button = Button(pygame.Rect(423, 490, 234, 64), "下一关", "Green")
        self.retry_button = Button(pygame.Rect(423, 490, 234, 64), "重新挑战", "Red")
        self.replay_button = Button(pygame.Rect(423, 500, 234, 64), "再玩一次", "Green")
        self.particles = self._make_particles()

    def _load_assets(self) -> dict[str, pygame.Surface]:
        assets: dict[str, pygame.Surface] = {}
        for color in ("Blue", "Green", "Red", "Yellow", "Grey"):
            key = color.lower()
            assets[f"button_{key}"] = pygame.image.load(
                ASSET_DIR / color / "button_rectangle_depth_gradient.png"
            ).convert_alpha()
            for compass in ("n", "s", "w", "e"):
                assets[f"arrow_{key}_{compass}"] = pygame.image.load(
                    ASSET_DIR / color / f"arrow_basic_{compass}.png"
                ).convert_alpha()
            assets[f"star_{key}"] = pygame.image.load(
                ASSET_DIR / color / "star.png"
            ).convert_alpha()
        assets["check"] = pygame.image.load(
            ASSET_DIR / "Green" / "icon_checkmark.png"
        ).convert_alpha()
        assets["cross"] = pygame.image.load(
            ASSET_DIR / "Red" / "icon_cross.png"
        ).convert_alpha()
        return assets

    @staticmethod
    def _make_background() -> pygame.Surface:
        surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        for y in range(WINDOW_HEIGHT):
            ratio = y / (WINDOW_HEIGHT - 1)
            color = tuple(
                int(top + (bottom - top) * ratio)
                for top, bottom in zip(BACKGROUND_TOP, BACKGROUND_BOTTOM)
            )
            pygame.draw.line(surface, color, (0, y), (WINDOW_WIDTH, y))
        glow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(glow, (130, 151, 246, 38), (70, 90), 245)
        pygame.draw.circle(glow, (63, 200, 153, 28), (1010, 650), 275)
        pygame.draw.circle(glow, (255, 196, 78, 22), (930, 80), 180)
        surface.blit(glow, (0, 0))
        return surface

    @staticmethod
    def _make_particles() -> list[tuple[int, int, int, tuple[int, int, int]]]:
        rng = random.Random(27)
        colors = (BLUE, GREEN, RED, YELLOW)
        return [
            (rng.randrange(35, WINDOW_WIDTH - 35), rng.randrange(35, WINDOW_HEIGHT - 35),
             rng.randrange(3, 8), rng.choice(colors))
            for _ in range(44)
        ]

    def font(self, size: int, *, bold: bool = False, display: bool = False) -> pygame.font.Font:
        key = (size, bold, display)
        if key not in self._font_cache:
            if display:
                font = pygame.font.Font(ASSET_DIR / "Kenney Future.ttf", size)
            else:
                font = pygame.font.SysFont("Microsoft YaHei UI", size, bold=bold)
            self._font_cache[key] = font
        return self._font_cache[key]

    def draw_text(
        self, text: str, x: int, y: int, size: int,
        color: tuple[int, int, int] = NAVY, *, center: bool = False,
        bold: bool = False, display: bool = False,
    ) -> pygame.Rect:
        image = self.font(size, bold=bold, display=display).render(text, True, color)
        rect = image.get_rect(center=(x, y)) if center else image.get_rect(topleft=(x, y))
        self.screen.blit(image, rect)
        return rect

    def draw_panel(self, rect: pygame.Rect, *, color: tuple[int, int, int] = WHITE, radius: int = 24) -> None:
        self.screen.blit(_rounded_panel(rect.size, SHADOW, radius), rect.move(0, 8))
        self.screen.blit(_rounded_panel(rect.size, color, radius), rect)

    def run(self) -> None:
        self.running = True
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = event.pos
        if self.current_screen == "start" and self.start_button.contains(pos):
            self.start_new_game()
        elif self.current_screen == "game":
            if self.animating:
                self.set_feedback("动画进行中，请稍等", "warning")
            elif self.restart_button.contains(pos):
                self.restart_board()
            elif self.home_button.contains(pos):
                self.show_start_screen()
            else:
                self.on_board_click_pos(pos)
        elif self.current_screen == "level_clear" and self.next_button.contains(pos):
            self.advance_to_next_level()
        elif self.current_screen == "game_over" and self.retry_button.contains(pos):
            self.retry_after_failure()
        elif self.current_screen == "all_clear" and self.replay_button.contains(pos):
            self.start_new_game()

    def update(self, dt: float) -> None:
        if not self.animation:
            return
        self.animation["elapsed"] = float(self.animation["elapsed"]) + dt
        kind = self.animation["kind"]
        if kind == "collision" and float(self.animation["elapsed"]) >= COLLISION_DURATION:
            self._complete_collision()
        elif kind == "flight":
            row = int(self.animation["row"])
            col = int(self.animation["col"])
            direction = str(self.animation["direction"])
            elapsed = float(self.animation["elapsed"])
            row_step, col_step = DIRECTION_VECTORS[direction]
            start_x, start_y = self.cell_center(row, col)
            x = start_x + col_step * FLIGHT_SPEED * elapsed
            y = start_y + row_step * FLIGHT_SPEED * elapsed
            if x < -80 or x > WINDOW_WIDTH + 80 or y < -80 or y > WINDOW_HEIGHT + 80:
                self._complete_arrow_flight(row, col, direction)

    def show_start_screen(self) -> None:
        if not self.animating:
            self.current_screen = "start"

    def start_new_game(self) -> None:
        self.current_level_index = 0
        self.game = ArrowBoard(LEVELS[0].board)
        self.mistakes_remaining = MAX_MISTAKES
        self.selected_cell = None
        self.animating = False
        self.animation = None
        self.current_screen = "game"
        self.set_feedback("观察方向，找到第一支能飞出的箭", "normal")

    def load_level(self, level_index: int) -> None:
        if not 0 <= level_index < len(LEVELS):
            raise IndexError("关卡索引越界")
        if self.animating:
            raise RuntimeError("动画进行中不能切换关卡")
        self.current_level_index = level_index
        self.game = ArrowBoard(LEVELS[level_index].board)
        self.mistakes_remaining = MAX_MISTAKES
        self.selected_cell = None
        self.animation = None
        self.set_feedback("新关卡已加载，先观察再行动", "normal")

    def advance_to_next_level(self) -> None:
        next_index = self.current_level_index + 1
        if next_index >= len(LEVELS):
            self.show_all_clear()
            return
        self.load_level(next_index)
        self.current_screen = "game"

    def retry_after_failure(self) -> None:
        self.animating = False
        self.animation = None
        self.game.restart()
        self.mistakes_remaining = MAX_MISTAKES
        self.selected_cell = None
        self.current_screen = "game"
        self.set_feedback("再试一次，这次先检查箭头前方", "normal")

    def restart_board(self) -> None:
        if self.animating:
            self.set_feedback("请等待动画结束后再重新开始", "warning")
            return
        self.game.restart()
        self.mistakes_remaining = MAX_MISTAKES
        self.selected_cell = None
        self.set_feedback("棋盘和失误次数已恢复", "success")

    def show_level_clear(self) -> None:
        self.current_screen = "level_clear"

    def show_game_over(self) -> None:
        self.current_screen = "game_over"

    def show_all_clear(self) -> None:
        self.current_screen = "all_clear"

    @staticmethod
    def cell_center(row: int, col: int) -> tuple[float, float]:
        return (BOARD_LEFT + col * CELL_SIZE + CELL_SIZE / 2,
                BOARD_TOP + row * CELL_SIZE + CELL_SIZE / 2)

    @staticmethod
    def canvas_to_cell(x: int, y: int) -> tuple[int, int] | None:
        if not (BOARD_LEFT <= x < BOARD_LEFT + BOARD_SIZE):
            return None
        if not (BOARD_TOP <= y < BOARD_TOP + BOARD_SIZE):
            return None
        return (y - BOARD_TOP) // CELL_SIZE, (x - BOARD_LEFT) // CELL_SIZE

    def on_board_click_pos(self, position: tuple[int, int]) -> None:
        if self.animating:
            self.set_feedback("动画进行中，请稍等", "warning")
            return
        cell = self.canvas_to_cell(*position)
        if cell is None:
            return
        row, col = cell
        direction = self.game.board[row][col]
        if direction is None:
            self.selected_cell = None
            self.set_feedback("这里是空格，换一支箭试试", "warning")
            return
        self.selected_cell = cell
        if self.game.is_blocked(row, col):
            self.mistakes_remaining -= 1
            self.animating = True
            self.animation = {"kind": "collision", "row": row, "col": col, "elapsed": 0.0}
            self.set_feedback(f"碰撞！{DIRECTION_NAMES[direction]}箭头前方有阻挡", "danger")
        else:
            self.animating = True
            self.animation = {
                "kind": "flight", "row": row, "col": col,
                "direction": direction, "elapsed": 0.0,
            }
            self.set_feedback(f"{DIRECTION_NAMES[direction]}箭头正在飞出棋盘", "success")

    def _complete_collision(self) -> None:
        self.animating = False
        self.animation = None
        self.selected_cell = None
        if self.mistakes_remaining <= 0:
            self.show_game_over()
        else:
            self.set_feedback("箭头没有消失，失误机会 -1", "danger")

    def _complete_arrow_flight(self, row: int, col: int, direction: str) -> None:
        self.game.remove_arrow(row, col)
        self.animating = False
        self.animation = None
        self.selected_cell = None
        if self.game.remaining_arrows() == 0:
            if self.current_level_index == len(LEVELS) - 1:
                self.show_all_clear()
            else:
                self.show_level_clear()
        else:
            self.set_feedback(
                f"成功！第 {row + 1} 行第 {col + 1} 列箭头已飞出",
                "success",
            )

    def set_feedback(self, message: str, kind: str) -> None:
        self.feedback = message
        self.feedback_kind = kind

    def draw(self) -> None:
        self.screen.blit(self.background, (0, 0))
        if self.current_screen == "start":
            self.draw_start_screen()
        elif self.current_screen == "game":
            self.draw_game_screen()
        elif self.current_screen in {"level_clear", "game_over", "all_clear"}:
            self.draw_result_screen(self.current_screen)

    def draw_brand(self, x: int = 60, y: int = 38) -> None:
        pygame.draw.circle(self.screen, BLUE, (x + 20, y + 20), 20)
        arrow = pygame.transform.smoothscale(self.assets["arrow_blue_e"], (28, 28))
        self.screen.blit(arrow, arrow.get_rect(center=(x + 20, y + 20)))
        self.draw_text("ARROW ESCAPE", x + 52, y + 7, 18, NAVY, display=True)
        self.draw_text("一箭又一箭", x + 53, y + 31, 12, MUTED, bold=True)

    def draw_start_screen(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.draw_brand()
        self.draw_text("方向决定出路", 82, 145, 18, BLUE, bold=True)
        self.draw_text("一 箭 又 一 箭", 80, 190, 42, NAVY, bold=True)
        self.draw_text("观察路径，按正确顺序清空整张棋盘", 82, 258, 18, MUTED)

        rules = (
            ("01", "点击箭头", "选择一支你想移出棋盘的箭"),
            ("02", "检查前方", "同一行或列不能有其他箭头"),
            ("03", "避免碰撞", "碰撞三次，本关挑战失败"),
        )
        for index, (number, title, note) in enumerate(rules):
            y = 325 + index * 68
            pygame.draw.circle(self.screen, BLUE_SOFT, (102, y + 20), 20)
            self.draw_text(number, 102, y + 20, 13, BLUE, center=True, display=True)
            self.draw_text(title, 136, y + 2, 17, NAVY, bold=True)
            self.draw_text(note, 136, y + 29, 13, MUTED)
        self.start_button.draw(self, mouse)
        self.draw_text("3 个原创关卡  ·  鼠标点击操作", 144, 627, 12, MUTED)

        hero = pygame.Rect(555, 112, 440, 520)
        self.draw_panel(hero, radius=34)
        self.draw_text("LEVEL 01", 600, 154, 14, BLUE, display=True)
        self.draw_text("找出第一条安全路线", 600, 183, 20, NAVY, bold=True)
        pygame.draw.rect(self.screen, (245, 248, 255), (597, 235, 356, 300), border_radius=24)
        for row in range(4):
            for col in range(4):
                cell = pygame.Rect(621 + col * 76, 259 + row * 62, 58, 52)
                pygame.draw.rect(self.screen, WHITE, cell, border_radius=14)
        hero_arrows = ((0, 1, UP), (0, 3, RIGHT), (1, 0, LEFT), (1, 2, DOWN),
                       (2, 1, RIGHT), (2, 3, UP), (3, 0, DOWN), (3, 2, LEFT))
        for row, col, direction in hero_arrows:
            self.draw_arrow(direction, (650 + col * 76, 285 + row * 62), 38)
        pygame.draw.rect(self.screen, GREEN_SOFT, (633, 560, 282, 38), border_radius=19)
        pygame.draw.circle(self.screen, GREEN, (657, 579), 7)
        self.draw_text("准备好了吗？让箭头出发！", 675, 567, 14, (41, 132, 91), bold=True)

    def draw_game_screen(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.draw_brand(62, 27)
        self.draw_text(
            f"第 {self.current_level_index + 1} 关 · {LEVELS[self.current_level_index].name}",
            820, 35, 18, NAVY, bold=True,
        )
        for index in range(len(LEVELS)):
            pygame.draw.circle(
                self.screen, BLUE if index <= self.current_level_index else GRID,
                (822 + index * 30, 72), 5,
            )

        self.draw_panel(pygame.Rect(58, 135, 504, 526), color=(28, 38, 68), radius=28)
        self.draw_text("选择一支箭", 94, 153, 15, (177, 190, 221), bold=True)
        self.draw_text("DOTTED ARROW BOARD", 344, 155, 10, (95, 116, 165), display=True)
        self.draw_board()

        self.draw_panel(pygame.Rect(590, 135, 432, 526), radius=28)
        self.draw_text("本关进度", 630, 170, 24, NAVY, bold=True)
        self.draw_text("每一步都要看清箭头前方", 630, 205, 14, MUTED)
        self.draw_stat_card(pygame.Rect(630, 250, 158, 112), "剩余箭头", str(self.game.remaining_arrows()), BLUE)
        self.draw_stat_card(pygame.Rect(806, 250, 176, 112), "剩余失误", str(self.mistakes_remaining), GREEN if self.mistakes_remaining > 1 else RED)

        feedback_colors = {
            "normal": (BLUE_SOFT, BLUE), "success": (GREEN_SOFT, GREEN),
            "warning": (YELLOW_SOFT, (194, 126, 21)), "danger": (RED_SOFT, RED),
        }
        box_color, text_color = feedback_colors.get(self.feedback_kind, feedback_colors["normal"])
        pygame.draw.rect(self.screen, box_color, (630, 390, 352, 68), border_radius=16)
        pygame.draw.circle(self.screen, text_color, (655, 424), 7)
        self.draw_text(self.feedback, 674, 411, 13, text_color, bold=True)
        self.restart_button.enabled = not self.animating
        self.home_button.enabled = not self.animating
        self.restart_button.draw(self, mouse)
        self.home_button.draw(self, mouse)

    def draw_stat_card(self, rect: pygame.Rect, label: str, value: str, accent: tuple[int, int, int]) -> None:
        pygame.draw.rect(self.screen, (246, 248, 253), rect, border_radius=18)
        pygame.draw.rect(self.screen, accent, (rect.x, rect.y, 6, rect.height), border_radius=3)
        self.draw_text(label, rect.x + 24, rect.y + 18, 14, MUTED, bold=True)
        self.draw_text(value, rect.x + 24, rect.y + 46, 38, accent, display=True)

    def draw_board(self) -> None:
        pygame.draw.rect(
            self.screen, (19, 27, 52),
            (BOARD_LEFT - 10, BOARD_TOP - 10, BOARD_SIZE + 20, BOARD_SIZE + 20),
            border_radius=22,
        )
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                cell = pygame.Rect(
                    BOARD_LEFT + col * CELL_SIZE + 4,
                    BOARD_TOP + row * CELL_SIZE + 4,
                    CELL_SIZE - 8, CELL_SIZE - 8,
                )
                pygame.draw.rect(self.screen, (27, 38, 68), cell, border_radius=15)
                pygame.draw.rect(self.screen, (40, 53, 88), cell, width=1, border_radius=15)
                direction = self.game.board[row][col]
                if direction is None:
                    pygame.draw.circle(self.screen, (78, 96, 139), cell.center, 3)
                    pygame.draw.circle(self.screen, (123, 147, 205), cell.center, 1)
                    continue
                if self.animation and self.animation["kind"] == "flight" and (row, col) == (
                    self.animation["row"], self.animation["col"]
                ):
                    continue
                center = self.cell_center(row, col)
                if self.animation and self.animation["kind"] == "collision" and (row, col) == (
                    self.animation["row"], self.animation["col"]
                ):
                    elapsed = float(self.animation["elapsed"])
                    offset = int(math.sin(elapsed * 72) * 8 * (1 - elapsed / COLLISION_DURATION))
                    center = (center[0] + offset, center[1])
                    self.draw_arrow(direction, center, 48, collision=True)
                else:
                    self.draw_arrow(direction, center, 48)
        if self.animation and self.animation["kind"] == "flight":
            row, col = int(self.animation["row"]), int(self.animation["col"])
            direction = str(self.animation["direction"])
            row_step, col_step = DIRECTION_VECTORS[direction]
            elapsed = float(self.animation["elapsed"])
            x, y = self.cell_center(row, col)
            self.draw_arrow(
                direction,
                (x + col_step * FLIGHT_SPEED * elapsed, y + row_step * FLIGHT_SPEED * elapsed),
                48,
            )

    def draw_arrow(
        self, direction: str, center: tuple[float, float], size: int, *, collision: bool = False,
    ) -> None:
        soft, accent, color_name, compass = DIRECTION_COLORS[direction]
        if collision:
            soft, accent, color_name = RED_SOFT, RED, "Red"
        glow = pygame.Surface((size + 16, size + 16), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*accent, 45), glow.get_rect().center, size // 2 + 7)
        self.screen.blit(glow, glow.get_rect(center=(int(center[0]), int(center[1]))))
        pygame.draw.circle(self.screen, (12, 18, 38), (int(center[0]), int(center[1] + 3)), size // 2)
        pygame.draw.circle(self.screen, soft, (int(center[0]), int(center[1])), size // 2)
        pygame.draw.circle(self.screen, accent, (int(center[0]), int(center[1])), size // 2, 2)
        image = pygame.transform.smoothscale(
            self.assets[f"arrow_{color_name.lower()}_{compass}"], (size - 16, size - 16)
        )
        self.screen.blit(image, image.get_rect(center=(int(center[0]), int(center[1]))))

    def draw_result_screen(self, kind: str) -> None:
        mouse = pygame.mouse.get_pos()
        self.draw_brand()
        for x, y, radius, color in self.particles:
            pygame.draw.circle(self.screen, color, (x, y), radius)
        self.draw_panel(pygame.Rect(290, 100, 500, 540), radius=34)

        if kind == "game_over":
            circle_color, accent, icon_key = RED_SOFT, RED, "cross"
            eyebrow, title = "TRY AGAIN", "本关挑战失败"
            note = "失误机会已经耗尽，观察路线后再试一次"
            button = self.retry_button
        elif kind == "all_clear":
            circle_color, accent, icon_key = YELLOW_SOFT, YELLOW, "star_yellow"
            eyebrow, title = "ALL CLEAR", "全部通关！"
            note = f"太棒了！你已完成全部 {len(LEVELS)} 个原创关卡"
            button = self.replay_button
        else:
            circle_color, accent, icon_key = GREEN_SOFT, GREEN, "check"
            eyebrow, title = "LEVEL CLEAR", f"第 {self.current_level_index + 1} 关通关！"
            note = f"你已清空“{LEVELS[self.current_level_index].name}”的所有箭头"
            button = self.next_button

        pygame.draw.circle(self.screen, circle_color, (540, 233), 78)
        if icon_key == "check":
            pygame.draw.line(self.screen, accent, (505, 233), (529, 256), 14)
            pygame.draw.line(self.screen, accent, (529, 256), (575, 207), 14)
            pygame.draw.circle(self.screen, accent, (505, 233), 7)
            pygame.draw.circle(self.screen, accent, (575, 207), 7)
        elif icon_key == "cross":
            pygame.draw.line(self.screen, accent, (512, 205), (568, 261), 14)
            pygame.draw.line(self.screen, accent, (568, 205), (512, 261), 14)
            for point in ((512, 205), (568, 261), (568, 205), (512, 261)):
                pygame.draw.circle(self.screen, accent, point, 7)
        else:
            icon = pygame.transform.smoothscale(self.assets[icon_key], (72, 68))
            self.screen.blit(icon, icon.get_rect(center=(540, 229)))
        self.draw_text(eyebrow, 540, 340, 15, accent, center=True, display=True)
        self.draw_text(title, 540, 390, 31, NAVY, center=True, bold=True)
        self.draw_text(note, 540, 442, 14, MUTED, center=True)
        button.draw(self, mouse)
        self.draw_text("继续保持，下一支箭也会找到出口", 540, 590, 12, MUTED, center=True)


def main() -> None:
    ArrowEscapeApp().run()


if __name__ == "__main__":
    main()

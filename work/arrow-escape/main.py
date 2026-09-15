"""“一箭又一箭”Pygame 图形界面。"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path

import pygame

from game_logic import DIRECTION_VECTORS, ArrowBoard
from levels import DOWN, LEFT, LEVELS, RIGHT, UP


WINDOW_WIDTH = 600
WINDOW_HEIGHT = 820
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
BOARD_LEFT = 84
BOARD_TOP = 190
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
        self.help_visible = False
        self.feedback = "点击前方没有阻挡的箭头"
        self.feedback_kind = "normal"
        self.assets = self._load_assets()
        self._font_cache: dict[tuple[int, bool, bool], pygame.font.Font] = {}
        self.background = self._make_background()
        self.home_background = self._make_home_background()
        self.start_button = Button(pygame.Rect(170, 610, 260, 66), "开始游戏", "Blue")
        self.help_button = Button(pygame.Rect(170, 692, 260, 60), "玩法说明", "Green")
        self.help_close_rect = pygame.Rect(468, 178, 48, 48)
        self.restart_button = Button(pygame.Rect(26, 48, 100, 52), "重开", "Green")
        self.home_button = Button(pygame.Rect(474, 48, 100, 52), "主页", "Grey")
        self.next_button = Button(pygame.Rect(180, 620, 240, 64), "下一关", "Green")
        self.retry_button = Button(pygame.Rect(180, 620, 240, 64), "重新挑战", "Red")
        self.replay_button = Button(pygame.Rect(180, 620, 240, 64), "再玩一次", "Green")
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
    def _make_home_background() -> pygame.Surface:
        """创建干净柔和的首页渐变背景。"""
        surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        top, bottom = (242, 248, 255), (219, 235, 253)
        for y in range(WINDOW_HEIGHT):
            ratio = y / (WINDOW_HEIGHT - 1)
            color = tuple(int(a + (b - a) * ratio) for a, b in zip(top, bottom))
            pygame.draw.line(surface, color, (0, y), (WINDOW_WIDTH, y))
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
        if self.current_screen == "start":
            if self.help_visible:
                if self.help_close_rect.collidepoint(pos):
                    self.help_visible = False
                return
            if self.start_button.contains(pos):
                self.start_new_game()
            elif self.help_button.contains(pos):
                self.help_visible = True
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
            self.help_visible = False

    def start_new_game(self) -> None:
        self.current_level_index = 0
        self.game = ArrowBoard(LEVELS[0].board)
        self.mistakes_remaining = MAX_MISTAKES
        self.selected_cell = None
        self.animating = False
        self.animation = None
        self.help_visible = False
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

    def draw_arrow_pattern(self) -> None:
        """绘制类似手机小游戏首页的浅色方向纹理。"""
        self.screen.fill((202, 241, 241))
        pattern = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        for row, y in enumerate(range(-25, WINDOW_HEIGHT, 105)):
            for col, x in enumerate(range(15, WINDOW_WIDTH, 112)):
                direction = UP if (row + col) % 2 == 0 else DOWN
                row_step, col_step = DIRECTION_VECTORS[direction]
                dx, dy = col_step, row_step
                head = (x + dx * 28, y + dy * 28)
                tail = (x - dx * 22, y - dy * 22)
                pygame.draw.line(pattern, (83, 190, 204, 28), tail, head, 17)
                perp = (-dy, dx)
                pygame.draw.polygon(pattern, (83, 190, 204, 28), (
                    (head[0] + dx * 12, head[1] + dy * 12),
                    (head[0] - dx * 15 + perp[0] * 18, head[1] - dy * 15 + perp[1] * 18),
                    (head[0] - dx * 15 - perp[0] * 18, head[1] - dy * 15 - perp[1] * 18),
                ))
        self.screen.blit(pattern, (0, 0))

    def draw_outlined_text(
        self, text: str, x: int, y: int, size: int, color: tuple[int, int, int],
        *, center: bool = True,
    ) -> None:
        font = self.font(size, bold=True)
        for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)):
            outline = font.render(text, True, WHITE)
            rect = outline.get_rect(center=(x + ox, y + oy)) if center else outline.get_rect(topleft=(x + ox, y + oy))
            self.screen.blit(outline, rect)
        image = font.render(text, True, color)
        rect = image.get_rect(center=(x, y)) if center else image.get_rect(topleft=(x, y))
        self.screen.blit(image, rect)

    def draw_color_title(self) -> None:
        chars = (("一", RED), ("箭", YELLOW), ("又", (234, 139, 44)),
                 ("一", BLUE), ("箭", GREEN))
        widths = [self.font(48, bold=True).size(char)[0] for char, _ in chars]
        x = (WINDOW_WIDTH - sum(widths) - 8 * (len(chars) - 1)) // 2
        for (char, color), width in zip(chars, widths):
            self.draw_outlined_text(char, x, 96, 48, color, center=False)
            x += width + 8

    def draw_animated_arrow(self) -> None:
        """绘制会上下浮动、轻轻摆动和眨眼的原创箭头角色。"""
        elapsed = pygame.time.get_ticks() / 1000.0
        bob = int(math.sin(elapsed * 2.2) * 10)
        angle = math.sin(elapsed * 1.5) * 3.0
        blink = int(elapsed * 5) % 19 == 18

        shadow = pygame.Surface((260, 80), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (45, 73, 128, 38), (28, 27, 204, 28))
        self.screen.blit(shadow, shadow.get_rect(center=(300, 501)))

        mascot = pygame.Surface((310, 250), pygame.SRCALPHA)
        outline = ((36, 94), (178, 94), (178, 48), (280, 125),
                   (178, 202), (178, 156), (36, 156))
        body = ((47, 101), (184, 101), (184, 64), (264, 125),
                (184, 186), (184, 149), (47, 149))
        pygame.draw.polygon(mascot, (39, 71, 160), outline)
        pygame.draw.polygon(mascot, (62, 164, 239), body)
        pygame.draw.polygon(mascot, (104, 205, 255), (
            (58, 106), (177, 106), (177, 77), (244, 126),
            (177, 126), (177, 120), (58, 120),
        ))

        for eye_x in (119, 158):
            if blink:
                pygame.draw.line(mascot, (35, 43, 65), (eye_x - 11, 125), (eye_x + 11, 125), 5)
            else:
                pygame.draw.ellipse(mascot, WHITE, (eye_x - 15, 107, 30, 38))
                pygame.draw.ellipse(mascot, (35, 43, 65), (eye_x - 5, 119, 11, 17))
                pygame.draw.circle(mascot, WHITE, (eye_x - 1, 121), 3)
        pygame.draw.arc(
            mascot, (35, 67, 116), (126, 132, 28, 23),
            math.pi + 0.2, math.tau - 0.2, 4,
        )
        pygame.draw.circle(mascot, (250, 125, 157, 150), (91, 143), 9)
        pygame.draw.circle(mascot, (250, 125, 157, 150), (188, 143), 9)

        rotated = pygame.transform.rotozoom(mascot, angle, 1.0)
        self.screen.blit(rotated, rotated.get_rect(center=(300, 360 + bob)))

    def draw_help_modal(self) -> None:
        """绘制玩法说明弹窗。"""
        veil = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        veil.fill((25, 38, 72, 145))
        self.screen.blit(veil, (0, 0))
        panel_rect = pygame.Rect(65, 155, 470, 510)
        self.draw_panel(panel_rect, radius=30)
        self.draw_text("玩法说明", 300, 205, 28, NAVY, center=True, bold=True)
        self.draw_text("HOW TO PLAY", 300, 242, 11, BLUE, center=True, display=True)

        rules = (
            ("1", BLUE, "选择箭头", "用鼠标点击棋盘中的任意箭头"),
            ("2", GREEN, "检查路径", "前进方向直到边界之间不能有其他箭头"),
            ("3", YELLOW, "清空棋盘", "无阻挡时箭头飞出，清空全部箭头即可过关"),
            ("!", RED, "注意碰撞", "被阻挡会消耗一次机会，三次失误则挑战失败"),
        )
        for index, (number, color, title, note) in enumerate(rules):
            y = 293 + index * 78
            pygame.draw.circle(self.screen, color, (112, y + 21), 21)
            self.draw_text(number, 112, y + 21, 16, WHITE, center=True, bold=True)
            self.draw_text(title, 151, y + 2, 17, NAVY, bold=True)
            self.draw_text(note, 151, y + 31, 12, MUTED)

        pygame.draw.circle(self.screen, (238, 242, 250), self.help_close_rect.center, 22)
        pygame.draw.line(self.screen, MUTED, (482, 192), (502, 212), 4)
        pygame.draw.line(self.screen, MUTED, (502, 192), (482, 212), 4)
        self.draw_text("点击右上角关闭", 300, 626, 12, MUTED, center=True)

    def draw_mascot(self) -> None:
        """用原创几何图形绘制带表情的双向箭头吉祥物。"""
        left = ((338, 315), (270, 315), (270, 282), (190, 350),
                (270, 418), (270, 385), (338, 385))
        right = ((262, 325), (330, 325), (330, 292), (410, 360),
                 (330, 428), (330, 395), (262, 395))
        for points, dark, light in ((left, (39, 79, 157), (65, 190, 231)),
                                    (right, (43, 82, 170), (47, 153, 224))):
            pygame.draw.polygon(self.screen, dark, points)
            inner = tuple((300 + (x - 300) * 0.92, 355 + (y - 355) * 0.92) for x, y in points)
            pygame.draw.polygon(self.screen, light, inner)
        for eye_x, pupil_x in ((280, 286), (327, 320)):
            pygame.draw.ellipse(self.screen, WHITE, (eye_x - 24, 326, 48, 65))
            pygame.draw.ellipse(self.screen, (42, 43, 55), (pupil_x - 9, 349, 18, 27))
            pygame.draw.circle(self.screen, WHITE, (pupil_x - 3, 354), 4)
        pygame.draw.line(self.screen, (56, 49, 57), (252, 321), (286, 330), 9)
        pygame.draw.line(self.screen, (56, 49, 57), (315, 328), (349, 314), 9)

    @staticmethod
    def draw_gear(surface: pygame.Surface, center: tuple[int, int]) -> None:
        """绘制不依赖特殊字体的设置齿轮。"""
        x, y = center
        color = (69, 74, 81)
        for angle in range(0, 360, 45):
            radians = math.radians(angle)
            dx, dy = math.cos(radians), math.sin(radians)
            start = (x + int(dx * 16), y + int(dy * 16))
            end = (x + int(dx * 25), y + int(dy * 25))
            pygame.draw.line(surface, color, start, end, 9)
        pygame.draw.circle(surface, color, center, 20)
        pygame.draw.circle(surface, WHITE, center, 8)

    def draw_start_screen(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.screen.blit(self.home_background, (0, 0))
        self.draw_color_title()
        self.draw_animated_arrow()
        self.start_button.draw(self, mouse)
        pygame.draw.polygon(self.screen, WHITE, ((199, 629), (199, 657), (220, 643)))
        self.help_button.draw(self, mouse)
        if self.help_visible:
            self.draw_help_modal()

    @staticmethod
    def draw_heart(surface: pygame.Surface, center: tuple[int, int], color: tuple[int, int, int]) -> None:
        x, y = center
        pygame.draw.circle(surface, color, (x - 9, y - 5), 10)
        pygame.draw.circle(surface, color, (x + 9, y - 5), 10)
        pygame.draw.polygon(surface, color, ((x - 18, y), (x + 18, y), (x, y + 23)))

    def draw_game_screen(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.screen.fill((61, 64, 89))
        pygame.draw.line(self.screen, (126, 135, 168), (0, 145), (WINDOW_WIDTH, 145), 2)
        self.restart_button.enabled = not self.animating
        self.home_button.enabled = not self.animating
        self.restart_button.draw(self, mouse)
        self.home_button.draw(self, mouse)
        self.draw_text(f"关卡 {self.current_level_index + 1}", 300, 24, 28, WHITE, center=True, bold=True)
        heart_x = 270
        for index in range(MAX_MISTAKES):
            color = (255, 81, 88) if index < self.mistakes_remaining else (93, 95, 119)
            self.draw_heart(self.screen, (heart_x + index * 30, 77), color)
        self.draw_text(
            f"剩余箭头  {self.game.remaining_arrows()}", 300, 116, 15,
            (216, 221, 238), center=True, bold=True,
        )
        self.draw_board()

        feedback_colors = {
            "normal": (135, 201, 239), "success": (103, 224, 168),
            "warning": (255, 204, 90), "danger": (255, 116, 124),
        }
        pygame.draw.line(self.screen, (126, 135, 168), (0, 660), (WINDOW_WIDTH, 660), 2)
        self.draw_text(
            self.feedback, 300, 690, 14,
            feedback_colors.get(self.feedback_kind, (216, 221, 238)), center=True, bold=True,
        )
        self.draw_text("提示", 84, 752, 16, WHITE, center=True, bold=True)
        pygame.draw.circle(self.screen, (255, 193, 55), (84, 720), 22)
        self.draw_text("?", 84, 718, 25, WHITE, center=True, bold=True)
        self.draw_text("观察同行同列", 300, 742, 13, (180, 188, 216), center=True)
        self.draw_text("基础模式", 516, 752, 16, WHITE, center=True, bold=True)
        pygame.draw.rect(self.screen, (45, 184, 189), (494, 699, 44, 44), width=4, border_radius=8)
        self.draw_text("#", 516, 719, 24, (74, 229, 213), center=True, bold=True)

    def draw_board(self) -> None:
        pygame.draw.rect(
            self.screen, (53, 56, 81),
            (BOARD_LEFT - 10, BOARD_TOP - 10, BOARD_SIZE + 20, BOARD_SIZE + 20),
            border_radius=16,
        )
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                cell = pygame.Rect(
                    BOARD_LEFT + col * CELL_SIZE + 4,
                    BOARD_TOP + row * CELL_SIZE + 4,
                    CELL_SIZE - 8, CELL_SIZE - 8,
                )
                direction = self.game.board[row][col]
                if direction is None:
                    pygame.draw.circle(self.screen, (91, 96, 126), cell.center, 3)
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
        _soft, accent, color_name, compass = DIRECTION_COLORS[direction]
        if collision:
            accent = RED
        x, y = int(center[0]), int(center[1])
        tile_size = size + 8
        tile = pygame.Surface((tile_size + 12, tile_size + 12), pygame.SRCALPHA)
        tile_rect = pygame.Rect(6, 6, tile_size, tile_size)
        pygame.draw.rect(tile, (*accent, 38), tile_rect, border_radius=14)
        pygame.draw.rect(tile, (*accent, 205), tile_rect, width=2, border_radius=14)
        pygame.draw.rect(tile, (*accent, 32), tile_rect.inflate(8, 8), width=4, border_radius=18)
        image = pygame.transform.smoothscale(
            self.assets[f"arrow_{color_name.lower()}_{compass}"],
            (size - 8, size - 8),
        )
        if collision:
            image = image.copy()
            image.fill((255, 82, 88, 255), special_flags=pygame.BLEND_RGBA_MULT)
        tile.blit(image, image.get_rect(center=tile.get_rect().center))
        self.screen.blit(tile, tile.get_rect(center=(x, y)))

    def draw_result_screen(self, kind: str) -> None:
        mouse = pygame.mouse.get_pos()
        self.draw_arrow_pattern()
        for x, y, radius, color in self.particles:
            pygame.draw.circle(self.screen, color, (x, y), radius)
        self.draw_panel(pygame.Rect(70, 125, 460, 610), radius=34)

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

        pygame.draw.circle(self.screen, circle_color, (300, 275), 78)
        if icon_key == "check":
            pygame.draw.line(self.screen, accent, (265, 275), (289, 298), 14)
            pygame.draw.line(self.screen, accent, (289, 298), (335, 249), 14)
            pygame.draw.circle(self.screen, accent, (265, 275), 7)
            pygame.draw.circle(self.screen, accent, (335, 249), 7)
        elif icon_key == "cross":
            pygame.draw.line(self.screen, accent, (272, 247), (328, 303), 14)
            pygame.draw.line(self.screen, accent, (328, 247), (272, 303), 14)
            for point in ((272, 247), (328, 303), (328, 247), (272, 303)):
                pygame.draw.circle(self.screen, accent, point, 7)
        else:
            icon = pygame.transform.smoothscale(self.assets[icon_key], (72, 68))
            self.screen.blit(icon, icon.get_rect(center=(300, 271)))
        self.draw_text(eyebrow, 300, 385, 15, accent, center=True, display=True)
        self.draw_text(title, 300, 435, 31, NAVY, center=True, bold=True)
        self.draw_text(note, 300, 487, 14, MUTED, center=True)
        button.draw(self, mouse)
        self.draw_text("继续保持，下一支箭也会找到出口", 300, 705, 12, MUTED, center=True)


def main() -> None:
    ArrowEscapeApp().run()


if __name__ == "__main__":
    main()

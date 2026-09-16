"""“一箭又一箭”Pygame 图形界面。"""

from __future__ import annotations

import math
import random
import json
from dataclasses import dataclass
from pathlib import Path

import pygame

from advanced_levels import ADVANCED_LEVELS
from advanced_logic import AdvancedBoard
from game_logic import DIRECTION_VECTORS, ArrowBoard
from levels import DOWN, LEFT, LEVELS, RIGHT, UP


WINDOW_WIDTH = 600
WINDOW_HEIGHT = 820
FPS = 60
MAX_MISTAKES = 3
MAX_HINTS = 3
STARTING_SCORE = 0
ARROW_SCORE = 100
COLLISION_PENALTY = 100
HINT_PENALTY = 50

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
SAVE_FILE = Path(__file__).resolve().parent / "save_data.json"
SAVE_VERSION = 1
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

ADVANCED_COLORS = {
    "purple": (176, 139, 255), "mint": (92, 216, 189),
    "yellow": (255, 199, 49), "blue": (91, 181, 239),
    "green": (126, 199, 49), "pink": (238, 128, 209),
    "orange": (244, 166, 98), "lavender": (148, 142, 236),
    "coral": (239, 126, 126), "cyan": (84, 207, 211),
    "lime": (108, 217, 139),
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

    def __init__(self, *, create_display: bool = True,
                 save_path: str | Path | None = None) -> None:
        pygame.init()
        pygame.font.init()
        flags = 0 if create_display else pygame.HIDDEN
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        pygame.display.set_caption("一箭又一箭 · Arrow Escape")
        self.clock = pygame.time.Clock()
        self.running = False
        self.current_screen = "start"
        self.selected_mode = "basic"
        self.selected_level_index = 0
        self.current_level_index = 0
        self.game = ArrowBoard(LEVELS[0].board)
        self.mistakes_remaining = MAX_MISTAKES
        self.elapsed_time = 0.0
        self.level_score = STARTING_SCORE
        self.total_score = 0
        self.earned_stars = 0
        self.par_time = 50.0
        self.level_scored = False
        self.hints_remaining = MAX_HINTS
        self.level_records: dict[str, dict[int, int]] = {"basic": {}, "advanced": {}}
        self.save_path = Path(save_path) if save_path is not None else SAVE_FILE
        self.load_progress()
        self.selected_cell: tuple[int, int] | None = None
        self.animating = False
        self.animation: dict[str, object] | None = None
        self.help_visible = False
        self.hint_cell: tuple[int, int] | None = None
        self.hint_arrow_id: int | None = None
        self.feedback = "点击前方没有阻挡的箭头"
        self.feedback_kind = "normal"
        self.assets = self._load_assets()
        self._font_cache: dict[tuple[int, bool, bool], pygame.font.Font] = {}
        self.background = self._make_background()
        self.home_background = self._make_home_background()
        self.start_button = Button(pygame.Rect(170, 610, 260, 66), "开始游戏", "Blue")
        self.help_button = Button(pygame.Rect(170, 692, 260, 60), "玩法说明", "Green")
        self.help_close_rect = pygame.Rect(468, 178, 48, 48)
        self.level_mode_basic_rect = pygame.Rect(105, 112, 190, 48)
        self.level_mode_advanced_rect = pygame.Rect(305, 112, 190, 48)
        self.level_node_centers = ((300, 660), (145, 555), (385, 465), (185, 350), (390, 235))
        self.level_card_rects = tuple(
            pygame.Rect(x - 58, y - 43, 116, 86) for x, y in self.level_node_centers
        )
        self.level_back_button = Button(pygame.Rect(24, 38, 105, 48), "返回", "Grey")
        self.hint_rect = pygame.Rect(36, 684, 98, 88)
        self.restart_button = Button(pygame.Rect(26, 48, 100, 52), "重开", "Green")
        self.home_button = Button(pygame.Rect(474, 48, 100, 52), "选关", "Grey")
        self.next_button = Button(pygame.Rect(88, 620, 200, 60), "下一关", "Green")
        self.retry_button = Button(pygame.Rect(88, 620, 200, 60), "重新挑战", "Red")
        self.replay_button = Button(pygame.Rect(88, 620, 200, 60), "再玩一次", "Green")
        self.result_back_button = Button(pygame.Rect(312, 620, 200, 60), "返回选关", "Grey")
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

    def draw_wrapped_text(
        self, text: str, rect: pygame.Rect, size: int,
        color: tuple[int, int, int], *, line_gap: int = 10,
    ) -> None:
        """按像素宽度自动换行，适合显示连续的中文说明文字。"""
        font = self.font(size)
        lines: list[str] = []
        line = ""
        for char in text:
            candidate = line + char
            if line and font.size(candidate)[0] > rect.width:
                lines.append(line)
                line = char
            else:
                line = candidate
        if line:
            lines.append(line)
        y = rect.y
        for line in lines:
            image = font.render(line, True, color)
            self.screen.blit(image, image.get_rect(midtop=(rect.centerx, y)))
            y += font.get_linesize() + line_gap

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
                self.current_screen = "level_select"
            elif self.help_button.contains(pos):
                self.help_visible = True
        elif self.current_screen == "level_select":
            if self.level_back_button.contains(pos):
                self.show_start_screen()
            elif self.level_mode_basic_rect.collidepoint(pos):
                self.selected_mode = "basic"
                self.selected_level_index = 0
                self.save_progress()
            elif self.level_mode_advanced_rect.collidepoint(pos):
                self.selected_mode = "advanced"
                self.selected_level_index = 0
                self.save_progress()
            else:
                for index, rect in enumerate(self.level_card_rects):
                    if rect.collidepoint(pos):
                        self.selected_level_index = index
                        self.start_new_game()
                        break
        elif self.current_screen == "game":
            if self.animating:
                self.set_feedback("动画进行中，请稍等", "warning")
            elif self.restart_button.contains(pos):
                self.restart_board()
            elif self.home_button.contains(pos):
                self.show_level_select()
            elif self.hint_rect.collidepoint(pos):
                self.show_hint()
            else:
                self.on_board_click_pos(pos)
        elif self.current_screen in {"level_clear", "game_over", "all_clear"}:
            if self.result_back_button.contains(pos):
                self.show_level_select()
            elif self.current_screen == "level_clear" and self.next_button.contains(pos):
                self.advance_to_next_level()
            elif self.current_screen == "game_over" and self.retry_button.contains(pos):
                self.retry_after_failure()
            elif self.current_screen == "all_clear" and self.replay_button.contains(pos):
                self.start_new_game()

    def update(self, dt: float) -> None:
        if self.current_screen == "game":
            self.elapsed_time += max(0.0, dt)
        if not self.animation:
            return
        self.animation["elapsed"] = float(self.animation["elapsed"]) + dt
        kind = self.animation["kind"]
        if kind == "collision" and float(self.animation["elapsed"]) >= COLLISION_DURATION:
            self._complete_collision()
        elif kind == "flight":
            direction = str(self.animation["direction"])
            elapsed = float(self.animation["elapsed"])
            row_step, col_step = DIRECTION_VECTORS[direction]
            if "arrow_id" in self.animation:
                arrow_id = int(self.animation["arrow_id"])
                tail_x, tail_y = self.advanced_flight_points(arrow_id, elapsed * FLIGHT_SPEED)[0]
                if tail_x < -80 or tail_x > WINDOW_WIDTH + 80 or tail_y < -80 or tail_y > WINDOW_HEIGHT + 80:
                    self._complete_advanced_flight(arrow_id)
                return
            else:
                row = int(self.animation["row"])
                col = int(self.animation["col"])
                start_x, start_y = self.cell_center(row, col)
            x = start_x + col_step * FLIGHT_SPEED * elapsed
            y = start_y + row_step * FLIGHT_SPEED * elapsed
            if x < -80 or x > WINDOW_WIDTH + 80 or y < -80 or y > WINDOW_HEIGHT + 80:
                if "arrow_id" in self.animation:
                    self._complete_advanced_flight(arrow_id)
                else:
                    self._complete_arrow_flight(row, col, direction)

    def show_start_screen(self) -> None:
        if not self.animating:
            self.current_screen = "start"
            self.help_visible = False

    def show_level_select(self) -> None:
        """返回当前模式的关卡地图。"""
        if not self.animating:
            self.current_screen = "level_select"
            self.help_visible = False

    def start_new_game(self) -> None:
        self.current_level_index = self.selected_level_index
        levels = self.levels_for_mode()
        if self.selected_mode == "advanced":
            self.game = AdvancedBoard(levels[self.current_level_index])
        else:
            self.game = ArrowBoard(levels[self.current_level_index].board)
        self.reset_level_stats()
        self.selected_cell = None
        self.hint_cell = None
        self.hint_arrow_id = None
        self.animating = False
        self.animation = None
        self.help_visible = False
        self.current_screen = "game"
        self.set_feedback("观察方向，找到第一支能飞出的箭", "normal")
        self.save_progress()

    def load_level(self, level_index: int) -> None:
        levels = self.levels_for_mode()
        if not 0 <= level_index < len(levels):
            raise IndexError("关卡索引越界")
        if self.animating:
            raise RuntimeError("动画进行中不能切换关卡")
        self.current_level_index = level_index
        self.selected_level_index = level_index
        if self.selected_mode == "advanced":
            self.game = AdvancedBoard(levels[level_index])
        else:
            self.game = ArrowBoard(levels[level_index].board)
        self.reset_level_stats()
        self.selected_cell = None
        self.hint_cell = None
        self.hint_arrow_id = None
        self.animation = None
        self.set_feedback("新关卡已加载，先观察再行动", "normal")

    def advance_to_next_level(self) -> None:
        next_index = self.current_level_index + 1
        if next_index >= len(self.levels_for_mode()):
            self.show_all_clear()
            return
        self.load_level(next_index)
        self.current_screen = "game"

    def levels_for_mode(self):
        """返回当前模式对应的关卡集合。"""
        return ADVANCED_LEVELS if self.selected_mode == "advanced" else LEVELS

    def load_progress(self) -> bool:
        """读取本地 JSON 存档；数据缺失或损坏时保留默认进度。"""
        try:
            data = json.loads(self.save_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("version") != SAVE_VERSION:
                return False

            mode = data.get("selected_mode")
            if mode in {"basic", "advanced"}:
                self.selected_mode = mode

            level = data.get("selected_level", 0)
            level_count = len(ADVANCED_LEVELS if self.selected_mode == "advanced" else LEVELS)
            if isinstance(level, int) and not isinstance(level, bool):
                self.selected_level_index = min(max(level, 0), level_count - 1)

            score = data.get("total_score", 0)
            if isinstance(score, int) and not isinstance(score, bool):
                self.total_score = max(0, score)

            raw_records = data.get("level_records", {})
            if isinstance(raw_records, dict):
                for record_mode, level_count in (
                    ("basic", len(LEVELS)), ("advanced", len(ADVANCED_LEVELS))
                ):
                    raw_mode = raw_records.get(record_mode, {})
                    if not isinstance(raw_mode, dict):
                        continue
                    cleaned: dict[int, int] = {}
                    for raw_index, raw_stars in raw_mode.items():
                        try:
                            index = int(raw_index)
                        except (TypeError, ValueError):
                            continue
                        if (0 <= index < level_count and isinstance(raw_stars, int)
                                and not isinstance(raw_stars, bool) and 1 <= raw_stars <= 3):
                            cleaned[index] = raw_stars
                    self.level_records[record_mode] = cleaned
            return True
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            return False

    def save_progress(self) -> bool:
        """原子写入累计分数、最佳星级和上次选择，失败时不中断游戏。"""
        data = {
            "version": SAVE_VERSION,
            "selected_mode": self.selected_mode,
            "selected_level": self.selected_level_index,
            "total_score": self.total_score,
            "level_records": {
                mode: {str(index): stars for index, stars in records.items()}
                for mode, records in self.level_records.items()
            },
        }
        temporary = self.save_path.with_suffix(self.save_path.suffix + ".tmp")
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            temporary.replace(self.save_path)
            return True
        except (OSError, UnicodeError, TypeError, ValueError):
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            return False

    def reset_level_stats(self) -> None:
        """重置本关计时、分数和星级。"""
        self.mistakes_remaining = MAX_MISTAKES
        self.elapsed_time = 0.0
        self.level_score = STARTING_SCORE
        self.earned_stars = 0
        self.level_scored = False
        self.hints_remaining = MAX_HINTS
        seconds_per_arrow = 4.0 if self.selected_mode == "advanced" else 2.0
        self.par_time = max(30.0, self.game.remaining_arrows() * seconds_per_arrow)

    @staticmethod
    def format_time(seconds: float) -> str:
        total_seconds = max(0, int(seconds))
        return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"

    def finish_level_stats(self) -> None:
        """结算时间奖励、剩余机会奖励和星级，仅执行一次。"""
        if self.level_scored:
            return
        time_bonus = max(0, int(self.par_time - self.elapsed_time) * 5)
        mistake_bonus = self.mistakes_remaining * 100
        self.level_score += time_bonus + mistake_bonus
        if self.mistakes_remaining == MAX_MISTAKES and self.elapsed_time <= self.par_time:
            self.earned_stars = 3
        elif self.mistakes_remaining >= 1 and self.elapsed_time <= self.par_time * 1.5:
            self.earned_stars = 2
        else:
            self.earned_stars = 1
        self.total_score += self.level_score
        records = self.level_records[self.selected_mode]
        records[self.current_level_index] = max(
            records.get(self.current_level_index, 0), self.earned_stars
        )
        self.level_scored = True
        self.save_progress()

    def retry_after_failure(self) -> None:
        self.animating = False
        self.animation = None
        self.game.restart()
        self.reset_level_stats()
        self.selected_cell = None
        self.hint_cell = None
        self.hint_arrow_id = None
        self.current_screen = "game"
        self.set_feedback("再试一次，这次先检查箭头前方", "normal")

    def restart_board(self) -> None:
        if self.animating:
            self.set_feedback("请等待动画结束后再重新开始", "warning")
            return
        self.game.restart()
        self.reset_level_stats()
        self.selected_cell = None
        self.hint_cell = None
        self.hint_arrow_id = None
        self.set_feedback("棋盘和失误次数已恢复", "success")

    def show_level_clear(self) -> None:
        self.current_screen = "level_clear"

    def show_game_over(self) -> None:
        self.current_screen = "game_over"

    def show_all_clear(self) -> None:
        self.current_screen = "all_clear"

    def board_geometry(self) -> tuple[int, int, int, int, int]:
        """根据关卡行列数返回左、上、格宽、棋盘宽和棋盘高。"""
        if self.selected_mode == "advanced":
            cell_size = min(500 // self.game.cols, 480 // self.game.rows)
            width, height = self.game.cols * cell_size, self.game.rows * cell_size
            return (WINDOW_WIDTH - width) // 2, 160 + (480 - height) // 2, cell_size, width, height
        cell_size = min(82, 432 // max(self.game.rows, self.game.cols))
        width = self.game.cols * cell_size
        height = self.game.rows * cell_size
        left = (WINDOW_WIDTH - width) // 2
        top = 180 + (432 - height) // 2
        return left, top, cell_size, width, height

    def cell_center(self, row: int, col: int) -> tuple[float, float]:
        left, top, cell_size, _width, _height = self.board_geometry()
        return (left + col * cell_size + cell_size / 2,
                top + row * cell_size + cell_size / 2)

    def canvas_to_cell(self, x: int, y: int) -> tuple[int, int] | None:
        left, top, cell_size, width, height = self.board_geometry()
        if not (left <= x < left + width):
            return None
        if not (top <= y < top + height):
            return None
        return (y - top) // cell_size, (x - left) // cell_size

    def show_hint(self) -> None:
        """高亮并说明一个当前可以安全消除的箭头。"""
        if self.animating:
            return
        if self.hints_remaining <= 0:
            self.set_feedback("本关提示次数已经用完", "warning")
            return
        if self.selected_mode == "advanced":
            choices = self.game.removable_arrows()
            if not choices:
                self.set_feedback("当前没有可直接飞出的折线箭头", "danger")
                return
            self.hint_arrow_id = choices[0]
            self.hint_cell = None
            path = self.game.path(self.hint_arrow_id)
            row, col = path.cells[-1]
            self.set_feedback(f"提示：点击高亮折线，端点在第 {row + 1} 行第 {col + 1} 列", "success")
        else:
            choices = self.game.removable_arrows()
            if not choices:
                self.set_feedback("当前没有可直接飞出的箭头", "danger")
                return
            self.hint_cell = choices[0]
            self.hint_arrow_id = None
            row, col = self.hint_cell
            self.set_feedback(f"提示：点击第 {row + 1} 行第 {col + 1} 列的高亮箭头", "success")
        self.hints_remaining -= 1
        self.level_score = max(0, self.level_score - HINT_PENALTY)

    def on_board_click_pos(self, position: tuple[int, int]) -> None:
        if self.animating:
            self.set_feedback("动画进行中，请稍等", "warning")
            return
        cell = self.canvas_to_cell(*position)
        if cell is None:
            return
        row, col = cell
        if self.selected_mode == "advanced":
            self._on_advanced_click(row, col)
            return
        direction = self.game.board[row][col]
        if direction is None:
            self.selected_cell = None
            self.set_feedback("这里是空格，换一支箭试试", "warning")
            return
        self.selected_cell = cell
        self.hint_cell = None
        if self.game.is_blocked(row, col):
            self.mistakes_remaining -= 1
            self.level_score = max(0, self.level_score - COLLISION_PENALTY)
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

    def _on_advanced_click(self, row: int, col: int) -> None:
        arrow_id = self.game.arrow_at(row, col)
        if arrow_id is None:
            self.set_feedback("这里没有折线箭头", "warning")
            return
        path = self.game.path(arrow_id)
        self.hint_arrow_id = None
        if self.game.is_blocked(arrow_id):
            self.mistakes_remaining -= 1
            self.level_score = max(0, self.level_score - COLLISION_PENALTY)
            self.animating = True
            self.animation = {
                "kind": "collision", "arrow_id": arrow_id,
                "direction": path.direction, "elapsed": 0.0,
            }
            self.set_feedback("碰撞！这条折线的出口方向仍有阻挡", "danger")
        else:
            self.animating = True
            self.animation = {
                "kind": "flight", "arrow_id": arrow_id,
                "direction": path.direction, "elapsed": 0.0,
            }
            self.set_feedback("折线箭头正在飞出棋盘", "success")

    def _complete_collision(self) -> None:
        self.animating = False
        self.animation = None
        self.selected_cell = None
        if self.mistakes_remaining <= 0:
            self.show_game_over()
        else:
            self.set_feedback("箭头没有消失，失误机会 -1", "danger")

    def _complete_arrow_flight(self, row: int, col: int, direction: str) -> None:
        if self.game.remove_arrow(row, col):
            self.level_score += ARROW_SCORE
        self.animating = False
        self.animation = None
        self.selected_cell = None
        if self.game.remaining_arrows() == 0:
            self.finish_level_stats()
            if self.current_level_index == len(LEVELS) - 1:
                self.show_all_clear()
            else:
                self.show_level_clear()
        else:
            self.set_feedback(
                f"成功！第 {row + 1} 行第 {col + 1} 列箭头已飞出",
                "success",
            )

    def _complete_advanced_flight(self, arrow_id: int) -> None:
        if self.game.remove_arrow(arrow_id):
            self.level_score += ARROW_SCORE
        self.animating = False
        self.animation = None
        self.hint_arrow_id = None
        if self.game.remaining_arrows() == 0:
            self.finish_level_stats()
            if self.current_level_index == len(ADVANCED_LEVELS) - 1:
                self.show_all_clear()
            else:
                self.show_level_clear()
        else:
            self.set_feedback("成功！整条折线箭头已经飞出", "success")

    def set_feedback(self, message: str, kind: str) -> None:
        self.feedback = message
        self.feedback_kind = kind

    def draw(self) -> None:
        self.screen.blit(self.background, (0, 0))
        if self.current_screen == "start":
            self.draw_start_screen()
        elif self.current_screen == "level_select":
            self.draw_level_select_screen()
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
        panel_rect = pygame.Rect(65, 170, 470, 440)
        self.draw_panel(panel_rect, radius=30)
        self.draw_text("玩法说明", 300, 222, 28, NAVY, center=True, bold=True)
        self.draw_text("HOW TO PLAY", 300, 257, 11, BLUE, center=True, display=True)
        paragraph = (
            "观察棋盘中箭头指向的方向。点击一支箭头后，如果它前方直到边界都没有"
            "其他箭头，它就会沿路线飞出；如果前方被挡住，箭头会晃动并消耗一次"
            "失误机会。清空棋盘即可通过当前关卡，三次失误后可以重新挑战。基础模式"
            "使用单格箭头，进阶模式使用整条彩色折线，游戏中的提示按钮可以告诉你下一步。"
        )
        self.draw_wrapped_text(paragraph, pygame.Rect(105, 302, 390, 220), 15, MUTED, line_gap=11)

        pygame.draw.circle(self.screen, (238, 242, 250), self.help_close_rect.center, 22)
        pygame.draw.line(self.screen, MUTED, (482, 192), (502, 212), 4)
        pygame.draw.line(self.screen, MUTED, (502, 192), (482, 212), 4)
        self.draw_text("点击右上角关闭", 300, 565, 12, MUTED, center=True)

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
        self.start_button.text = "开始游戏"
        self.start_button.draw(self, mouse)
        pygame.draw.polygon(self.screen, WHITE, ((199, 629), (199, 657), (220, 643)))
        self.help_button.draw(self, mouse)
        if self.help_visible:
            self.draw_help_modal()

    def draw_level_select_screen(self) -> None:
        """绘制一条由下向上的冒险路线式关卡地图。"""
        mouse = pygame.mouse.get_pos()
        self.screen.blit(self.home_background, (0, 0))
        # 原创的远山、云朵和路线，营造地图感。
        scenery = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        for x, y, radius in ((70, 245, 95), (535, 310, 120), (80, 610, 115), (540, 650, 130)):
            pygame.draw.circle(scenery, (106, 145, 206, 22), (x, y), radius)
        pygame.draw.polygon(scenery, (73, 114, 177, 25), ((0, 530), (125, 390), (245, 560), (360, 405), (600, 590), (600, 820), (0, 820)))
        self.screen.blit(scenery, (0, 0))
        self.draw_text("冒险地图", 300, 55, 32, NAVY, center=True, bold=True)
        self.draw_text("选择模式，沿着路线挑战关卡", 300, 84, 13, MUTED, center=True)

        pygame.draw.rect(self.screen, (218, 228, 244), (103, 108, 394, 56), border_radius=28)
        selected = self.level_mode_basic_rect if self.selected_mode == "basic" else self.level_mode_advanced_rect
        pygame.draw.rect(self.screen, BLUE, selected, border_radius=22)
        self.draw_text(
            "基础模式", self.level_mode_basic_rect.centerx, self.level_mode_basic_rect.centery,
            16, WHITE if self.selected_mode == "basic" else MUTED, center=True, bold=True,
        )
        self.draw_text(
            "进阶模式", self.level_mode_advanced_rect.centerx, self.level_mode_advanced_rect.centery,
            16, WHITE if self.selected_mode == "advanced" else MUTED, center=True, bold=True,
        )

        levels = self.levels_for_mode()
        accents = (BLUE, GREEN, YELLOW, RED, (151, 102, 220))
        route_points = [self.level_node_centers[index] for index in range(len(levels))]
        if len(route_points) > 1:
            pygame.draw.lines(self.screen, (135, 156, 196), False, route_points, 7)
            pygame.draw.lines(self.screen, WHITE, False, route_points, 3)
        for index, (level, rect) in enumerate(zip(levels, self.level_card_rects)):
            hovered = rect.collidepoint(mouse)
            x, y = self.level_node_centers[index]
            accent = accents[index]
            best_stars = self.level_records[self.selected_mode].get(index, 0)
            radius = 38 if hovered else 34
            pygame.draw.circle(self.screen, (69, 82, 120, 40), (x + 3, y + 6), radius + 7)
            pygame.draw.circle(self.screen, WHITE, (x, y), radius + 7)
            pygame.draw.circle(self.screen, accent, (x, y), radius)
            if best_stars:
                pygame.draw.circle(self.screen, YELLOW, (x, y), radius + 8, width=4)
            self.draw_text(str(index + 1), x, y - 2, 24, WHITE, center=True, bold=True)
            label = pygame.Rect(x - 72, y + 41, 144, 33)
            pygame.draw.rect(self.screen, WHITE, label, border_radius=12)
            pygame.draw.rect(self.screen, (*accent,), label, width=2, border_radius=12)
            self.draw_text(f"第 {index + 1} 关 · {level.name}", x, y + 57, 13, NAVY, center=True, bold=True)
            if best_stars:
                # 绿色勾表示已通关，金色小牌显示本次运行中的最好星级。
                badge_center = (x + 31, y - 29)
                pygame.draw.circle(self.screen, WHITE, badge_center, 15)
                pygame.draw.circle(self.screen, GREEN, badge_center, 12)
                pygame.draw.line(self.screen, WHITE, (x + 25, y - 29), (x + 29, y - 24), 3)
                pygame.draw.line(self.screen, WHITE, (x + 29, y - 24), (x + 37, y - 34), 3)
                star_badge = pygame.Rect(x - 38, y - 53, 64, 23)
                pygame.draw.rect(self.screen, (255, 247, 211), star_badge, border_radius=11)
                pygame.draw.rect(self.screen, YELLOW, star_badge, width=2, border_radius=11)
                star = pygame.transform.smoothscale(self.assets["star_yellow"], (17, 16))
                self.screen.blit(star, (star_badge.x + 9, star_badge.y + 3))
                self.draw_text(f"× {best_stars}", star_badge.x + 31, star_badge.y + 3, 12, NAVY, bold=True)

        self.level_back_button.draw(self, mouse)

    @staticmethod
    def draw_heart(surface: pygame.Surface, center: tuple[int, int], color: tuple[int, int, int]) -> None:
        x, y = center
        pygame.draw.circle(surface, color, (x - 9, y - 5), 10)
        pygame.draw.circle(surface, color, (x + 9, y - 5), 10)
        pygame.draw.polygon(surface, color, ((x - 18, y), (x + 18, y), (x, y + 23)))

    def draw_game_screen(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.screen.fill((61, 64, 89))
        glow = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow, (82, 110, 190, 28), (20, 300), 230)
        pygame.draw.circle(glow, (50, 201, 177, 18), (590, 560), 240)
        self.screen.blit(glow, (0, 0))
        pygame.draw.line(self.screen, (126, 135, 168), (0, 145), (WINDOW_WIDTH, 145), 2)
        self.restart_button.enabled = not self.animating
        self.home_button.enabled = not self.animating
        self.restart_button.draw(self, mouse)
        self.home_button.draw(self, mouse)
        self.draw_text(f"关卡 {self.current_level_index + 1}", 300, 20, 27, WHITE, center=True, bold=True)
        level_name = (ADVANCED_LEVELS if self.selected_mode == "advanced" else LEVELS)[self.current_level_index].name
        self.draw_text(level_name, 300, 50, 12, (180, 190, 220), center=True, bold=True)
        heart_x = 270
        for index in range(MAX_MISTAKES):
            color = (255, 81, 88) if index < self.mistakes_remaining else (93, 95, 119)
            self.draw_heart(self.screen, (heart_x + index * 30, 77), color)
        status_color = (216, 221, 238)
        self.draw_text(f"时间 {self.format_time(self.elapsed_time)}", 174, 116, 13,
                       status_color, center=True, bold=True)
        self.draw_text(f"箭头 {self.game.remaining_arrows()}", 300, 116, 13,
                       status_color, center=True, bold=True)
        self.draw_text(f"得分 {self.level_score}", 430, 116, 13,
                       status_color, center=True, bold=True)
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
        self.draw_text(f"提示 ×{self.hints_remaining}", 84, 752, 16, WHITE, center=True, bold=True)
        if self.hints_remaining <= 0:
            hint_color = (103, 106, 126)
        else:
            hint_color = (255, 211, 75) if self.hint_rect.collidepoint(mouse) else (255, 193, 55)
        pygame.draw.circle(self.screen, hint_color, (84, 720), 24)
        self.draw_text("?", 84, 718, 25, WHITE, center=True, bold=True)
        helper_text = "点击整条彩色折线" if self.selected_mode == "advanced" else "观察同行同列"
        self.draw_text(helper_text, 300, 742, 13, (180, 188, 216), center=True)
        mode_name = "进阶模式" if self.selected_mode == "advanced" else "基础模式"
        self.draw_text(mode_name, 516, 752, 16, WHITE, center=True, bold=True)
        pygame.draw.rect(self.screen, (45, 184, 189), (494, 699, 44, 44), width=4, border_radius=8)
        self.draw_text("#", 516, 719, 24, (74, 229, 213), center=True, bold=True)

    def draw_board(self) -> None:
        left, top, cell_size, width, height = self.board_geometry()
        pygame.draw.rect(
            self.screen, (53, 56, 81),
            (left - 10, top - 10, width + 20, height + 20),
            border_radius=16,
        )
        for row in range(self.game.rows if self.selected_mode == "basic" else 0):
            for col in range(self.game.cols):
                pygame.draw.circle(
                    self.screen, (91, 96, 126),
                    tuple(map(int, self.cell_center(row, col))), 3,
                )

        if self.selected_mode == "advanced":
            self.draw_advanced_board(cell_size)
            return

        arrow_size = min(52, int(cell_size * 0.68))
        for row in range(self.game.rows):
            for col in range(self.game.cols):
                direction = self.game.board[row][col]
                if direction is None:
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
                    self.draw_arrow(direction, center, arrow_size, collision=True)
                else:
                    self.draw_arrow(direction, center, arrow_size)
                if self.hint_cell == (row, col):
                    pulse = 4 + int((math.sin(pygame.time.get_ticks() / 180) + 1) * 2)
                    pygame.draw.circle(
                        self.screen, (255, 231, 108), tuple(map(int, center)),
                        arrow_size // 2 + 11 + pulse, width=3,
                    )
        if self.animation and self.animation["kind"] == "flight":
            row, col = int(self.animation["row"]), int(self.animation["col"])
            direction = str(self.animation["direction"])
            row_step, col_step = DIRECTION_VECTORS[direction]
            elapsed = float(self.animation["elapsed"])
            x, y = self.cell_center(row, col)
            self.draw_arrow(
                direction,
                (x + col_step * FLIGHT_SPEED * elapsed, y + row_step * FLIGHT_SPEED * elapsed),
                arrow_size,
            )

    def advanced_flight_points(self, arrow_id: int, travel: float) -> list[tuple[float, float]]:
        """尾巴沿原折线前进，头部沿出口延伸，整条线长度保持不变。"""
        path = self.game.path(arrow_id)
        points = [self.cell_center(r, c) for r, c in path.cells]
        cell_size = self.board_geometry()[2]
        length = (len(points) - 1) * cell_size
        dr, dc = DIRECTION_VECTORS[path.direction]
        hx, hy = points[-1]
        if travel >= length:
            tail = (hx + dc * (travel - length), hy + dr * (travel - length))
            return [tail, (hx + dc * travel, hy + dr * travel)]
        segment = int(travel // cell_size)
        fraction = (travel % cell_size) / cell_size
        a, b = points[segment:segment + 2]
        tail = (a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction)
        return [tail, *points[segment + 1:], (hx + dc * travel, hy + dr * travel)]

    def draw_advanced_board(self, cell_size: int) -> None:
        """绘制进阶模式的多格折线箭头。"""
        for arrow_id in sorted(self.game.active_ids):
            offset = (0.0, 0.0)
            collision = False
            if self.animation and self.animation.get("arrow_id") == arrow_id:
                elapsed = float(self.animation["elapsed"])
                if self.animation["kind"] == "flight":
                    pass  # 飞出位置由 advanced_flight_points 沿折线计算。
                else:
                    shake = math.sin(elapsed * 72) * 8 * (1 - elapsed / COLLISION_DURATION)
                    offset = (shake, 0.0)
                    collision = True
            self.draw_advanced_path(
                arrow_id, cell_size, offset=offset, collision=collision,
                hinted=self.hint_arrow_id == arrow_id,
            )

    def draw_advanced_path(
        self, arrow_id: int, cell_size: int, *, offset: tuple[float, float],
        collision: bool, hinted: bool,
    ) -> None:
        path = self.game.path(arrow_id)
        color = RED if collision else ADVANCED_COLORS[path.color]
        points = [
            (int(self.cell_center(row, col)[0] + offset[0]),
             int(self.cell_center(row, col)[1] + offset[1]))
            for row, col in path.cells
        ]
        if self.animation and self.animation.get("arrow_id") == arrow_id and self.animation["kind"] == "flight":
            points = [tuple(map(round, p)) for p in self.advanced_flight_points(
                arrow_id, float(self.animation["elapsed"]) * FLIGHT_SPEED)]
        width = max(4, cell_size // 6)
        if hinted:
            pygame.draw.lines(self.screen, (255, 239, 156), False, points, width + 4)
        if len(points) > 1:
            pygame.draw.lines(self.screen, color, False, points, width)
        for point in points[:-1]:
            pygame.draw.circle(self.screen, color, point, width // 2)

        row_step, col_step = DIRECTION_VECTORS[path.direction]
        dx, dy = col_step, row_step
        head_x, head_y = points[-1]
        tip = (head_x + dx * cell_size // 3, head_y + dy * cell_size // 3)
        base = (head_x - dx * cell_size // 8, head_y - dy * cell_size // 8)
        perp = (-dy, dx)
        arrowhead = (
            tip,
            (base[0] + perp[0] * cell_size // 5, base[1] + perp[1] * cell_size // 5),
            (base[0] - perp[0] * cell_size // 5, base[1] - perp[1] * cell_size // 5),
        )
        pygame.draw.polygon(self.screen, (34, 35, 55), tuple((x + 2, y + 3) for x, y in arrowhead))
        pygame.draw.polygon(self.screen, color, arrowhead)
        if hinted:
            pulse = 8 + int((math.sin(pygame.time.get_ticks() / 180) + 1) * 3)
            pygame.draw.circle(self.screen, (255, 232, 103), (head_x, head_y), pulse, width=3)

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
            level_count = len(ADVANCED_LEVELS) if self.selected_mode == "advanced" else len(LEVELS)
            note = f"太棒了！你已完成全部 {level_count} 个原创关卡"
            button = self.replay_button
        else:
            circle_color, accent, icon_key = GREEN_SOFT, GREEN, "check"
            eyebrow, title = "LEVEL CLEAR", f"第 {self.current_level_index + 1} 关通关！"
            levels = ADVANCED_LEVELS if self.selected_mode == "advanced" else LEVELS
            note = f"你已清空“{levels[self.current_level_index].name}”的所有箭头"
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
        if kind != "game_over":
            for index in range(3):
                key = "star_yellow" if index < self.earned_stars else "star_grey"
                star = pygame.transform.smoothscale(self.assets[key], (48, 45))
                self.screen.blit(star, star.get_rect(center=(250 + index * 50, 540)))
        else:
            self.draw_text("本次未获得星星", 300, 540, 14, RED, center=True, bold=True)
        self.draw_text(
            f"用时 {self.format_time(self.elapsed_time)}   ·   本关 {self.level_score} 分   ·   累计 {self.total_score} 分",
            300, 585, 13, NAVY, center=True, bold=True,
        )
        button.draw(self, mouse)
        self.result_back_button.draw(self, mouse)
        self.draw_text("继续保持，下一支箭也会找到出口", 300, 705, 12, MUTED, center=True)


def main() -> None:
    ArrowEscapeApp().run()


if __name__ == "__main__":
    main()

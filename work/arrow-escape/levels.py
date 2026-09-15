"""原创关卡数据与方向定义。"""

from dataclasses import dataclass

UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"

DIRECTIONS = (UP, DOWN, LEFT, RIGHT)

DIRECTION_SYMBOLS = {
    UP: "↑",
    DOWN: "↓",
    LEFT: "←",
    RIGHT: "→",
}

BoardData = tuple[tuple[str | None, ...], ...]


@dataclass(frozen=True)
class Level:
    """一个不可变的关卡定义。"""

    name: str
    board: BoardData


# 每个元素对应一个单元格，None 表示空格。
LEVEL_1: BoardData = (
    (None, None, UP, None, UP, None),
    (None, UP, LEFT, None, None, None),
    (None, LEFT, DOWN, LEFT, None, None),
    (RIGHT, None, None, None, UP, UP),
    (None, None, None, LEFT, None, LEFT),
    (None, None, None, None, RIGHT, None),
)

LEVEL_2: BoardData = (
    (None, LEFT, None, LEFT, RIGHT, None),
    (UP, LEFT, RIGHT, None, None, None),
    (UP, None, None, DOWN, None, LEFT),
    (RIGHT, RIGHT, None, None, RIGHT, None),
    (None, None, None, RIGHT, None, RIGHT),
    (None, UP, None, DOWN, RIGHT, None),
)

LEVEL_3: BoardData = (
    (None, None, LEFT, None, RIGHT, UP),
    (LEFT, LEFT, None, None, None, UP),
    (None, None, LEFT, RIGHT, RIGHT, None),
    (None, DOWN, LEFT, RIGHT, None, None),
    (LEFT, None, None, LEFT, UP, UP),
    (DOWN, None, RIGHT, DOWN, DOWN, UP),
)

LEVELS = (
    Level("初识方向", LEVEL_1),
    Level("交错路线", LEVEL_2),
    Level("箭阵迷踪", LEVEL_3),
)

# 保留这个名称供已有测试与外部代码使用。
STARTER_BOARD = LEVEL_1


def copy_board(board: BoardData) -> list[list[str | None]]:
    """返回可独立修改的关卡二维列表。"""
    return [list(row) for row in board]

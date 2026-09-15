"""原创关卡数据与方向定义。"""

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

# 第一个展示棋盘。每个元素对应一个单元格，None 表示空格。
STARTER_BOARD = (
    (None, LEFT, None, DOWN, None, RIGHT),
    (RIGHT, None, UP, None, RIGHT, None),
    (None, None, None, None, None, LEFT),
    (None, DOWN, None, RIGHT, None, None),
    (LEFT, None, None, UP, None, None),
    (None, UP, None, None, RIGHT, None),
)


def copy_board(board: tuple[tuple[str | None, ...], ...]) -> list[list[str | None]]:
    """返回可独立修改的关卡二维列表。"""
    return [list(row) for row in board]

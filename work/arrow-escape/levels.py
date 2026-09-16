"""原创关卡数据与方向定义。"""

from dataclasses import dataclass
from random import Random

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


def make_dense_board(rows: int, cols: int, seed: int) -> BoardData:
    """随机剥离可见边缘格，并记录出射方向，得到可解的满格箭阵。

    每一步随机挑选能从剩余格子中直接离开的方向，所以记录的
    选择顺序可用于通关；固定种子使重新开始时布局保持一致。
    """
    rng = Random(seed)
    board = [[None for _ in range(cols)] for _ in range(rows)]
    remaining = {(r, c) for r in range(rows) for c in range(cols)}
    vectors = {UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}
    while remaining:
        choices = []
        for row, col in sorted(remaining):
            for direction, (dr, dc) in vectors.items():
                r, c = row + dr, col + dc
                while 0 <= r < rows and 0 <= c < cols and (r, c) not in remaining:
                    r, c = r + dr, c + dc
                if not (0 <= r < rows and 0 <= c < cols):
                    choices.append((row, col, direction))
        row, col, direction = rng.choice(choices)
        board[row][col] = direction
        remaining.remove((row, col))
    return tuple(tuple(row) for row in board)


# 三关依次为 5×5、6×6、7×7，均采用高密度满格布局。
LEVEL_1: BoardData = make_dense_board(5, 5, 3)
LEVEL_2: BoardData = make_dense_board(6, 6, 7)
LEVEL_3: BoardData = make_dense_board(7, 7, 11)
LEVEL_4: BoardData = make_dense_board(8, 8, 17)
LEVEL_5: BoardData = make_dense_board(9, 9, 23)

LEVELS = (
    Level("初识方向", LEVEL_1),
    Level("交错路线", LEVEL_2),
    Level("箭阵迷踪", LEVEL_3),
    Level("四向风暴", LEVEL_4),
    Level("终极箭阵", LEVEL_5),
)

# 保留这个名称供已有测试与外部代码使用。
STARTER_BOARD = LEVEL_1


def copy_board(board: BoardData) -> list[list[str | None]]:
    """返回可独立修改的关卡二维列表。"""
    return [list(row) for row in board]

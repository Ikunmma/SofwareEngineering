"""棋盘状态、路径检测和自动求解逻辑。"""

from collections.abc import Sequence

from levels import DIRECTIONS, DOWN, LEFT, RIGHT, UP


DIRECTION_VECTORS = {
    UP: (-1, 0),
    DOWN: (1, 0),
    LEFT: (0, -1),
    RIGHT: (0, 1),
}


class ArrowBoard:
    """保存棋盘状态并处理箭头的路径判定。"""

    def __init__(self, initial_board: Sequence[Sequence[str | None]]) -> None:
        self._initial_board = tuple(tuple(row) for row in initial_board)
        self._validate_board()
        self.board: list[list[str | None]] = []
        self.restart()

    @property
    def rows(self) -> int:
        """棋盘行数。"""
        return len(self._initial_board)

    @property
    def cols(self) -> int:
        """棋盘列数。"""
        return len(self._initial_board[0])

    def _validate_board(self) -> None:
        """检查关卡是否为非空矩形且方向值合法。"""
        if not self._initial_board or not self._initial_board[0]:
            raise ValueError("棋盘不能为空")

        expected_cols = len(self._initial_board[0])
        for row in self._initial_board:
            if len(row) != expected_cols:
                raise ValueError("棋盘每一行的列数必须相同")
            for cell in row:
                if cell is not None and cell not in DIRECTIONS:
                    raise ValueError(f"不支持的箭头方向: {cell}")

    def _check_position(self, row: int, col: int) -> None:
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise IndexError("棋盘坐标越界")

    def is_blocked(self, row: int, col: int) -> bool:
        """判断指定箭头与它前方边界之间是否有其他箭头。"""
        self._check_position(row, col)
        direction = self.board[row][col]
        if direction is None:
            raise ValueError("指定位置没有箭头")

        row_step, col_step = DIRECTION_VECTORS[direction]
        check_row = row + row_step
        check_col = col + col_step

        while 0 <= check_row < self.rows and 0 <= check_col < self.cols:
            if self.board[check_row][check_col] is not None:
                return True
            check_row += row_step
            check_col += col_step
        return False

    def remove_arrow(self, row: int, col: int) -> bool:
        """无阻挡时移除箭头并返回 True，其他情况返回 False。"""
        self._check_position(row, col)
        if self.board[row][col] is None or self.is_blocked(row, col):
            return False
        self.board[row][col] = None
        return True

    def remaining_arrows(self) -> int:
        """返回当前棋盘中的箭头数量。"""
        return sum(cell is not None for row in self.board for cell in row)

    def restart(self) -> None:
        """使用初始数据的深拷贝恢复棋盘。"""
        self.board = [list(row) for row in self._initial_board]

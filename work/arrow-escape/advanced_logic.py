"""进阶模式的多格折线箭头逻辑。"""

from advanced_levels import ADVANCED_LEVELS, AdvancedLevel, PathData
from game_logic import DIRECTION_VECTORS


class AdvancedBoard:
    """保存折线箭头，并检测箭头端点前方是否存在其他路线。"""

    def __init__(self, level: AdvancedLevel) -> None:
        self.level = level
        self.rows = level.rows
        self.cols = level.cols
        self.paths = level.paths
        self._validate()
        self.active_ids: set[int] = set()
        self.restart()

    def _validate(self) -> None:
        occupied: set[tuple[int, int]] = set()
        for path in self.paths:
            if len(path.cells) < 2:
                raise ValueError("进阶箭头至少需要两个格子")
            for first, second in zip(path.cells, path.cells[1:]):
                distance = abs(first[0] - second[0]) + abs(first[1] - second[1])
                if distance != 1:
                    raise ValueError("折线路径必须由相邻格子连续组成")
            expected_step = DIRECTION_VECTORS[path.direction]
            actual_step = (
                path.cells[-1][0] - path.cells[-2][0],
                path.cells[-1][1] - path.cells[-2][1],
            )
            if actual_step != expected_step:
                raise ValueError("箭头方向必须与折线路径末端一致")
            for row, col in path.cells:
                if not (0 <= row < self.rows and 0 <= col < self.cols):
                    raise ValueError("折线箭头坐标越界")
                if (row, col) in occupied:
                    raise ValueError(f"折线箭头发生重叠: {(row, col)}")
                occupied.add((row, col))

    def restart(self) -> None:
        self.active_ids = set(range(len(self.paths)))

    def remaining_arrows(self) -> int:
        return len(self.active_ids)

    def path(self, arrow_id: int) -> PathData:
        if arrow_id not in self.active_ids:
            raise ValueError("箭头已经被消除")
        return self.paths[arrow_id]

    def arrow_at(self, row: int, col: int) -> int | None:
        for arrow_id in self.active_ids:
            if (row, col) in self.paths[arrow_id].cells:
                return arrow_id
        return None

    def _other_occupied(self, arrow_id: int) -> set[tuple[int, int]]:
        return {
            cell
            for other_id in self.active_ids
            if other_id != arrow_id
            for cell in self.paths[other_id].cells
        }

    def is_blocked(self, arrow_id: int) -> bool:
        path = self.path(arrow_id)
        row_step, col_step = DIRECTION_VECTORS[path.direction]
        occupied = self._other_occupied(arrow_id) | set(path.cells[:-1])
        row, col = path.cells[-1]
        row += row_step
        col += col_step
        while 0 <= row < self.rows and 0 <= col < self.cols:
            if (row, col) in occupied:
                return True
            row += row_step
            col += col_step
        return False

    def removable_arrows(self) -> list[int]:
        return [arrow_id for arrow_id in sorted(self.active_ids) if not self.is_blocked(arrow_id)]

    def remove_arrow(self, arrow_id: int) -> bool:
        if arrow_id not in self.active_ids or self.is_blocked(arrow_id):
            return False
        self.active_ids.remove(arrow_id)
        return True


def solve_advanced(
    level: AdvancedLevel, active_ids: set[int] | frozenset[int] | None = None,
) -> list[int] | None:
    """返回进阶关卡或其当前剩余局面的一条完整消除顺序。"""
    failed: set[frozenset[int]] = set()

    def search(active: frozenset[int]) -> tuple[int, ...] | None:
        if not active:
            return ()
        if active in failed:
            return None
        board = AdvancedBoard(level)
        board.active_ids = set(active)
        for arrow_id in board.removable_arrows():
            result = search(active - {arrow_id})
            if result is not None:
                return (arrow_id,) + result
        failed.add(active)
        return None

    initial = frozenset(range(len(level.paths))) if active_ids is None else frozenset(active_ids)
    if not initial.issubset(range(len(level.paths))):
        raise ValueError("剩余箭头编号越界")
    solution = search(initial)
    return None if solution is None else list(solution)


def validate_advanced_levels() -> None:
    for level in ADVANCED_LEVELS:
        if solve_advanced(level) is None:
            raise ValueError(f"进阶关卡不可解: {level.name}")

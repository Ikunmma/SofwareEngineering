"""进阶模式的原创高密度折线箭头关卡。"""

from dataclasses import dataclass
from random import Random

from levels import DOWN, LEFT, RIGHT, UP


Cell = tuple[int, int]


@dataclass(frozen=True)
class PathData:
    """一条从尾部到箭头端点排列的折线路径。"""

    cells: tuple[Cell, ...]
    direction: str
    color: str


@dataclass(frozen=True)
class AdvancedLevel:
    name: str
    rows: int
    cols: int
    paths: tuple[PathData, ...]


COLORS = (
    "purple", "mint", "yellow", "blue", "green", "pink",
    "orange", "lavender", "coral", "cyan", "lime",
)


VECTORS = {UP: (-1, 0), DOWN: (1, 0), LEFT: (0, -1), RIGHT: (0, 1)}


def make_dense_advanced_level(
    name: str,
    rows: int,
    cols: int,
    seed: int,
    *,
    color_offset: int = 0,
) -> AdvancedLevel:
    """逆序放置随机游走折线；逆序消除即为一条已知可行解。

    新路线的头部射线必须不碰已有路线，身体从头部向后随机生长。
    有限次候选中选覆盖最多的一张，避免死循环和规则模板拼贴。
    """
    best: list[PathData] = []
    best_coverage = 0
    for attempt in range(48):
        rng = Random(seed * 101 + attempt)
        free = {(r, c) for r in range(rows) for c in range(cols)}
        paths: list[PathData] = []
        while free:
            candidates = []
            for r, c in sorted(free):
                for direction, (dr, dc) in VECTORS.items():
                    if (r - dr, c - dc) not in free:
                        continue
                    rr, cc = r + dr, c + dc
                    while 0 <= rr < rows and 0 <= cc < cols and (rr, cc) in free:
                        rr, cc = rr + dr, cc + dc
                    if not (0 <= rr < rows and 0 <= cc < cols):
                        candidates.append((r, c, direction))
            if not candidates:
                break
            r, c, direction = rng.choice(candidates)
            dr, dc = VECTORS[direction]
            cells = [(r, c), (r - dr, c - dc)]
            used = set(cells)
            # 混合短箭头、中等折线和跨区域长线。
            target = rng.choice((3, 5, 8, 12, 18, 26, 34))
            previous = (-dr, -dc)
            while len(cells) < target:
                r, c = cells[-1]
                options = [(vr, vc) for vr, vc in VECTORS.values()
                           if (r + vr, c + vc) in free - used]
                if not options:
                    break
                step = previous if previous in options and rng.random() < 0.62 else rng.choice(options)
                cells.append((r + step[0], c + step[1]))
                used.add(cells[-1])
                previous = step
            free.difference_update(used)
            paths.append(PathData(tuple(reversed(cells)), direction,
                                  COLORS[(rng.randrange(len(COLORS)) + color_offset) % len(COLORS)]))
        coverage = rows * cols - len(free)
        if coverage > best_coverage:
            best, best_coverage = paths, coverage
    return AdvancedLevel(name, rows, cols, tuple(best))


ADVANCED_LEVEL_1 = make_dense_advanced_level(
    "折线初探", 16, 12, 3, color_offset=1
)
ADVANCED_LEVEL_2 = make_dense_advanced_level(
    "回路交错", 18, 14, 7, color_offset=4
)
ADVANCED_LEVEL_3 = make_dense_advanced_level(
    "霓虹迷阵", 20, 16, 11, color_offset=7
)


ADVANCED_LEVELS = (ADVANCED_LEVEL_1, ADVANCED_LEVEL_2, ADVANCED_LEVEL_3)

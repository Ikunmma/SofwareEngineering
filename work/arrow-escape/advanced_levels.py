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


def exit_ray(head: Cell, direction: str, rows: int, cols: int) -> set[Cell]:
    """头部前方到边界的格子，自身身体也不应进入这条射线。"""
    r, c = head
    dr, dc = VECTORS[direction]
    ray = set()
    r, c = r + dr, c + dc
    while 0 <= r < rows and 0 <= c < cols:
        ray.add((r, c))
        r, c = r + dr, c + dc
    return ray


def fill_gaps(paths: list[PathData], rows: int, cols: int, rng: Random) -> list[PathData]:
    """延长尾部、插入随机弯路，填空时保留逆序通关证明。

    第 i 条路径新增的格子不能进入 i 及以后路径的出口射线。
    因此后加入的箭头先退出时，不会被新填入的身体挡住。
    """
    free = {(r, c) for r in range(rows) for c in range(cols)}
    free.difference_update(cell for p in paths for cell in p.cells)
    forbidden = [set() for _ in paths]
    rays: set[Cell] = set()
    for i in reversed(range(len(paths))):
        rays = rays | exit_ray(paths[i].cells[-1], paths[i].direction, rows, cols)
        forbidden[i] = rays
    changed = True
    while changed:
        changed = False
        order = list(range(len(paths)))
        rng.shuffle(order)
        for i in order:
            path = paths[i]
            allowed = free - forbidden[i]
            cells = list(path.cells)
            r, c = cells[0]
            tails = [(r + dr, c + dc) for dr, dc in VECTORS.values()
                     if (r + dr, c + dc) in allowed]
            if tails:
                cell = rng.choice(tails)
                cells.insert(0, cell)
                free.remove(cell)
                changed = True
            else:
                detours = []
                # 不改最后一段，以保留箭头方向。
                for j in range(len(cells) - 2):
                    a, b = cells[j:j + 2]
                    dr, dc = b[0] - a[0], b[1] - a[1]
                    for vr, vc in ((-dc, dr), (dc, -dr)):
                        x, y = (a[0] + vr, a[1] + vc), (b[0] + vr, b[1] + vc)
                        if x in allowed and y in allowed:
                            detours.append((j, x, y))
                if detours:
                    j, x, y = rng.choice(detours)
                    cells[j + 1:j + 1] = [x, y]
                    free.difference_update((x, y))
                    changed = True
            paths[i] = PathData(tuple(cells), path.direction, path.color)
    return paths


def make_dense_advanced_level(
    name: str,
    rows: int,
    cols: int,
    seed: int,
    *,
    color_offset: int = 0,
    attempts: int = 48,
) -> AdvancedLevel:
    """逆序放置随机游走折线；逆序消除即为一条已知可行解。

    新路线的头部射线必须不碰已有路线，身体从头部向后随机生长。
    有限次候选中选覆盖最多的一张，避免死循环和规则模板拼贴。
    """
    best: list[PathData] = []
    best_coverage = 0
    for attempt in range(attempts):
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
            ray = exit_ray((r, c), direction, rows, cols)
            cells = [(r, c), (r - dr, c - dc)]
            used = set(cells)
            # 混合短箭头、中等折线和跨区域长线。
            target = rng.choice((3, 5, 8, 12, 18, 26, 34))
            previous = (-dr, -dc)
            while len(cells) < target:
                r, c = cells[-1]
                options = [(vr, vc) for vr, vc in VECTORS.values()
                           if (r + vr, c + vc) in free - used - ray]
                if not options:
                    break
                step = previous if previous in options and rng.random() < 0.62 else rng.choice(options)
                cells.append((r + step[0], c + step[1]))
                used.add(cells[-1])
                previous = step
            free.difference_update(used)
            paths.append(PathData(tuple(reversed(cells)), direction,
                                  COLORS[(rng.randrange(len(COLORS)) + color_offset) % len(COLORS)]))
        paths = fill_gaps(paths, rows, cols, rng)
        coverage = sum(len(p.cells) for p in paths)
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
ADVANCED_LEVEL_4 = make_dense_advanced_level(
    "幻彩回廊", 22, 18, 17, color_offset=2, attempts=32
)
ADVANCED_LEVEL_5 = make_dense_advanced_level(
    "终极迷宫", 24, 20, 23, color_offset=5, attempts=32
)


ADVANCED_LEVELS = (
    ADVANCED_LEVEL_1, ADVANCED_LEVEL_2, ADVANCED_LEVEL_3,
    ADVANCED_LEVEL_4, ADVANCED_LEVEL_5,
)

"""进阶折线模式测试。"""

import sys
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from advanced_levels import ADVANCED_LEVELS, AdvancedLevel, PathData, exit_ray, make_dense_advanced_level  # noqa: E402
from advanced_logic import AdvancedBoard, solve_advanced  # noqa: E402


class AdvancedBoardTest(unittest.TestCase):
    def test_all_advanced_levels_have_executable_solution(self) -> None:
        for level in ADVANCED_LEVELS:
            solution = solve_advanced(level)
            self.assertIsNotNone(solution, level.name)
            board = AdvancedBoard(level)
            for arrow_id in solution or []:
                self.assertFalse(board.is_blocked(arrow_id))
                self.assertTrue(board.remove_arrow(arrow_id))
            self.assertEqual(board.remaining_arrows(), 0)

    def test_arrow_can_be_selected_from_any_path_cell(self) -> None:
        board = AdvancedBoard(ADVANCED_LEVELS[0])
        first_path = board.path(0)
        for row, col in first_path.cells:
            self.assertEqual(board.arrow_at(row, col), 0)

    def test_restart_restores_all_paths(self) -> None:
        board = AdvancedBoard(ADVANCED_LEVELS[0])
        arrow_id = board.removable_arrows()[0]
        self.assertTrue(board.remove_arrow(arrow_id))
        board.restart()
        self.assertEqual(board.remaining_arrows(), len(ADVANCED_LEVELS[0].paths))

    def test_level_grids_increase(self) -> None:
        sizes = [(level.rows, level.cols) for level in ADVANCED_LEVELS]
        self.assertEqual(sizes, sorted(sizes))
        self.assertEqual(len(set(sizes)), len(sizes))

    def test_random_levels_are_dense_and_have_varied_paths(self) -> None:
        for level in ADVANCED_LEVELS:
            occupied = {cell for path in level.paths for cell in path.cells}
            self.assertGreaterEqual(len(occupied) / (level.rows * level.cols), 0.97, level.name)
            self.assertGreaterEqual(len({len(p.cells) for p in level.paths}), 5)
            self.assertGreaterEqual(max(len(p.cells) for p in level.paths), 18)
            self.assertEqual(len({p.direction for p in level.paths}), 4)

    def test_generated_paths_never_block_their_own_exit(self) -> None:
        for level in ADVANCED_LEVELS:
            for path in level.paths:
                self.assertFalse(set(path.cells) & exit_ray(path.cells[-1], path.direction, level.rows, level.cols))

    def test_self_crossing_exit_is_blocked(self) -> None:
        path = PathData(((0, 1), (0, 0), (1, 0), (2, 0), (2, 1), (1, 1)), "up", "mint")
        board = AdvancedBoard(AdvancedLevel("self", 3, 3, (path,)))
        self.assertTrue(board.is_blocked(0))
        self.assertFalse(board.remove_arrow(0))

    def test_generator_reproduces_seed_and_reverse_order_is_a_solution(self) -> None:
        for seed in (3, 7, 11):
            level = make_dense_advanced_level("test", 16, 12, seed)
            self.assertEqual(level, make_dense_advanced_level("test", 16, 12, seed))
            board = AdvancedBoard(level)
            for arrow_id in reversed(range(len(level.paths))):
                self.assertTrue(board.remove_arrow(arrow_id))
            self.assertEqual(board.remaining_arrows(), 0)

    def test_solver_accepts_partially_cleared_advanced_board(self) -> None:
        level = ADVANCED_LEVELS[0]
        board = AdvancedBoard(level)
        first = board.removable_arrows()[0]
        self.assertTrue(board.remove_arrow(first))
        solution = solve_advanced(level, board.active_ids)
        self.assertIsNotNone(solution)
        self.assertEqual(len(solution), board.remaining_arrows())
        for arrow_id in solution:
            self.assertTrue(board.remove_arrow(arrow_id))
        self.assertEqual(board.remaining_arrows(), 0)


if __name__ == "__main__":
    unittest.main()

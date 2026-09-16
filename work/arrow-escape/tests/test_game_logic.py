"""路径检测与箭头消除的自动化测试。"""

import sys
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from game_logic import ArrowBoard, solve  # noqa: E402
from levels import DOWN, LEFT, LEVELS, RIGHT, STARTER_BOARD, UP  # noqa: E402


class ArrowBoardTest(unittest.TestCase):
    def test_all_four_directions_detect_distant_blocker(self) -> None:
        cases = (
            (UP, (0, 1)),
            (DOWN, (2, 1)),
            (LEFT, (1, 0)),
            (RIGHT, (1, 2)),
        )
        for direction, blocker_position in cases:
            with self.subTest(direction=direction):
                board_data = [[None] * 3 for _ in range(3)]
                board_data[1][1] = direction
                blocker_row, blocker_col = blocker_position
                board_data[blocker_row][blocker_col] = RIGHT
                self.assertTrue(ArrowBoard(board_data).is_blocked(1, 1))

    def test_all_four_directions_are_clear_without_blocker(self) -> None:
        for direction in (UP, DOWN, LEFT, RIGHT):
            with self.subTest(direction=direction):
                board_data = [[None] * 3 for _ in range(3)]
                board_data[1][1] = direction
                self.assertFalse(ArrowBoard(board_data).is_blocked(1, 1))

    def test_edge_arrow_can_be_removed_without_out_of_bounds_error(self) -> None:
        board = ArrowBoard(((UP, None), (None, RIGHT)))
        self.assertTrue(board.remove_arrow(0, 0))
        self.assertTrue(board.remove_arrow(1, 1))
        self.assertEqual(board.remaining_arrows(), 0)

    def test_blocked_arrow_is_not_removed(self) -> None:
        board = ArrowBoard(((RIGHT, None, LEFT),))
        self.assertFalse(board.remove_arrow(0, 0))
        self.assertEqual(board.remaining_arrows(), 2)

    def test_restart_restores_independent_copy(self) -> None:
        board = ArrowBoard(STARTER_BOARD)
        original_count = board.remaining_arrows()
        arrow_row, arrow_col = next(
            (row, col)
            for row in range(board.rows)
            for col in range(board.cols)
            if board.board[row][col] is not None
        )
        original_direction = board.board[arrow_row][arrow_col]
        board.board[arrow_row][arrow_col] = None
        self.assertEqual(board.remaining_arrows(), original_count - 1)
        board.restart()
        self.assertEqual(board.remaining_arrows(), original_count)
        self.assertEqual(board.board[arrow_row][arrow_col], original_direction)

    def test_empty_cell_cannot_be_checked_as_arrow(self) -> None:
        board = ArrowBoard(((None,),))
        with self.assertRaises(ValueError):
            board.is_blocked(0, 0)


class SolverTest(unittest.TestCase):
    def test_basic_level_grids_increase(self) -> None:
        sizes = [(len(level.board), len(level.board[0])) for level in LEVELS]
        self.assertEqual(sizes, [(5, 5), (6, 6), (7, 7), (8, 8), (9, 9)])

    def test_all_levels_have_executable_solution(self) -> None:
        for level in LEVELS:
            with self.subTest(level=level.name):
                solution = solve(level.board)
                self.assertIsNotNone(solution)

                board = ArrowBoard(level.board)
                self.assertEqual(len(solution), board.remaining_arrows())
                for row, col in solution:
                    self.assertFalse(board.is_blocked(row, col))
                    self.assertTrue(board.remove_arrow(row, col))
                self.assertEqual(board.remaining_arrows(), 0)

    def test_unsolvable_cycle_returns_none(self) -> None:
        self.assertIsNone(solve(((RIGHT, LEFT),)))

    def test_empty_board_returns_empty_solution(self) -> None:
        self.assertEqual(solve(((None, None), (None, None))), [])

    def test_solver_does_not_modify_input_board(self) -> None:
        board = [list(row) for row in STARTER_BOARD]
        original = [row.copy() for row in board]
        self.assertIsNotNone(solve(board))
        self.assertEqual(board, original)

    def test_solver_accepts_partially_cleared_board(self) -> None:
        board = ArrowBoard(STARTER_BOARD)
        first_move = board.removable_arrows()[0]
        self.assertTrue(board.remove_arrow(*first_move))
        solution = solve(board.board)
        self.assertIsNotNone(solution)
        self.assertEqual(len(solution), board.remaining_arrows())


if __name__ == "__main__":
    unittest.main()

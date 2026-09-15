"""路径检测与箭头消除的自动化测试。"""

import sys
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from game_logic import ArrowBoard  # noqa: E402
from levels import DOWN, LEFT, RIGHT, STARTER_BOARD, UP  # noqa: E402


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
        board.board[0][1] = None
        self.assertEqual(board.remaining_arrows(), original_count - 1)
        board.restart()
        self.assertEqual(board.remaining_arrows(), original_count)
        self.assertEqual(board.board[0][1], LEFT)

    def test_empty_cell_cannot_be_checked_as_arrow(self) -> None:
        board = ArrowBoard(((None,),))
        with self.assertRaises(ValueError):
            board.is_blocked(0, 0)


if __name__ == "__main__":
    unittest.main()

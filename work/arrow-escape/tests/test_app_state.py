"""游戏界面状态恢复的集成测试。"""

import sys
import time
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import main  # noqa: E402


class RestartStateTest(unittest.TestCase):
    def setUp(self) -> None:
        # 缩短测试动画，保留与真实动画相同的 after 回调流程。
        self.patchers = (
            patch.object(main, "FLIGHT_STEPS", 1),
            patch.object(main, "FLIGHT_DELAY_MS", 1),
            patch.object(main, "COLLISION_OFFSETS", (0,)),
            patch.object(main, "COLLISION_DELAY_MS", 1),
        )
        for patcher in self.patchers:
            patcher.start()

        try:
            self.root = main.create_window()
        except tk.TclError as error:
            self.skipTest(f"当前环境无法创建 Tkinter 窗口: {error}")

        self.root.withdraw()
        self.app = main.ArrowEscapeApp(self.root)
        self.app.start_new_game()
        self.root.update()

    def tearDown(self) -> None:
        if hasattr(self, "root"):
            try:
                self.root.destroy()
            except tk.TclError:
                pass
        for patcher in reversed(self.patchers):
            patcher.stop()

    def wait_for_animation(self) -> None:
        deadline = time.monotonic() + 1
        while self.app.animating and time.monotonic() < deadline:
            self.root.update()
            time.sleep(0.002)
        self.assertFalse(self.app.animating, "动画未在测试时限内结束")

    def click_cell(self, row: int, col: int) -> None:
        x = main.BOARD_PADDING + col * main.CELL_SIZE + main.CELL_SIZE // 2
        y = main.BOARD_PADDING + row * main.CELL_SIZE + main.CELL_SIZE // 2
        self.app.on_board_click(SimpleNamespace(x=x, y=y))

    def test_restart_restores_board_mistakes_and_labels(self) -> None:
        # 先消除第 1 行第 3 列向上的无阻挡箭头。
        self.click_cell(0, 2)
        self.wait_for_animation()
        self.assertEqual(self.app.game.remaining_arrows(), 12)

        # 再点击第 2 行第 3 列被阻挡的向左箭头。
        self.click_cell(1, 2)
        self.wait_for_animation()
        self.assertEqual(self.app.mistakes_remaining, 2)

        self.app.restart_board()

        self.assertEqual(self.app.game.remaining_arrows(), 13)
        self.assertEqual(self.app.mistakes_remaining, main.MAX_MISTAKES)
        self.assertIsNone(self.app.selected_cell)
        self.assertEqual(self.app.arrow_count_label.cget("text"), "13")
        self.assertEqual(self.app.mistakes_label.cget("text"), "3")
        self.assertIn("棋盘已恢复", self.app.feedback_label.cget("text"))

    def test_restart_is_ignored_while_arrow_is_flying(self) -> None:
        self.click_cell(0, 2)
        self.assertTrue(self.app.animating)

        self.app.restart_board()
        self.assertTrue(self.app.animating)
        self.assertIn("动画结束", self.app.feedback_label.cget("text"))

        self.wait_for_animation()
        self.assertEqual(self.app.game.remaining_arrows(), 12)

    def test_clearing_last_arrow_opens_result_and_next_level(self) -> None:
        # 用单个向上箭头构造可快速验证的通关场景。
        self.app.game.board = [[None] * self.app.game.cols for _ in range(self.app.game.rows)]
        self.app.game.board[0][0] = "up"
        self.app.draw_board()
        self.app._update_arrow_count()

        self.click_cell(0, 0)
        self.wait_for_animation()

        self.assertEqual(self.app.current_screen, "level_clear")
        self.assertEqual(self.app.current_level_index, 0)
        self.assertIsNotNone(self.app.next_level_button)
        self.assertEqual(self.app.next_level_button.cget("text"), "下一关  →")

        self.app.next_level_button.invoke()
        self.root.update()

        self.assertEqual(self.app.current_screen, "game")
        self.assertEqual(self.app.current_level_index, 1)
        self.assertEqual(self.app.game.remaining_arrows(), 17)
        self.assertEqual(self.app.mistakes_remaining, main.MAX_MISTAKES)
        self.assertEqual(self.app.arrow_count_label.cget("text"), "17")
        self.assertEqual(self.app.mistakes_label.cget("text"), "3")

    def test_final_level_opens_all_clear_without_fourth_level(self) -> None:
        self.app.load_level(2)
        self.app.game.board = [[None] * self.app.game.cols for _ in range(self.app.game.rows)]
        self.app.game.board[0][0] = "up"
        self.app.draw_board()
        self.app._update_arrow_count()

        self.click_cell(0, 0)
        self.wait_for_animation()

        self.assertEqual(self.app.current_screen, "all_clear")
        self.assertEqual(self.app.current_level_index, 2)
        self.assertIsNotNone(self.app.replay_all_button)

        self.app.replay_all_button.invoke()
        self.root.update()

        self.assertEqual(self.app.current_screen, "game")
        self.assertEqual(self.app.current_level_index, 0)
        self.assertEqual(self.app.game.remaining_arrows(), 13)
        self.assertEqual(self.app.mistakes_remaining, main.MAX_MISTAKES)


if __name__ == "__main__":
    unittest.main()

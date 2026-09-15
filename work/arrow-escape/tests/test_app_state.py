"""Pygame 界面状态与交互集成测试。"""

import os
import sys
import unittest
from pathlib import Path


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import pygame  # noqa: E402

import main  # noqa: E402


class PygameStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = main.ArrowEscapeApp(create_display=False)
        self.app.start_new_game()

    def tearDown(self) -> None:
        pygame.quit()

    def click_cell(self, row: int, col: int) -> None:
        self.app.on_board_click_pos(tuple(map(int, self.app.cell_center(row, col))))

    def finish_animation(self) -> None:
        if self.app.animation and self.app.animation["kind"] == "collision":
            self.app.update(main.COLLISION_DURATION + 0.1)
        elif self.app.animation:
            self.app.update(3.0)

    def test_start_page_can_enter_game(self) -> None:
        self.app.show_start_screen()
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.start_button.rect.center
        )
        self.app.handle_event(event)
        self.assertEqual(self.app.current_screen, "game")
        self.assertEqual(self.app.game.remaining_arrows(), 13)

    def test_restart_restores_board_and_mistakes(self) -> None:
        self.click_cell(0, 2)
        self.finish_animation()
        self.assertEqual(self.app.game.remaining_arrows(), 12)
        self.click_cell(1, 2)
        self.finish_animation()
        self.assertEqual(self.app.mistakes_remaining, 2)
        self.app.restart_board()
        self.assertEqual(self.app.game.remaining_arrows(), 13)
        self.assertEqual(self.app.mistakes_remaining, main.MAX_MISTAKES)
        self.assertIn("已恢复", self.app.feedback)

    def test_animation_locks_restart(self) -> None:
        self.click_cell(0, 2)
        self.assertTrue(self.app.animating)
        self.app.restart_board()
        self.assertTrue(self.app.animating)
        self.assertIn("动画结束", self.app.feedback)

    def test_three_collisions_open_failure_page(self) -> None:
        for _ in range(3):
            self.click_cell(1, 2)
            self.finish_animation()
        self.assertEqual(self.app.current_screen, "game_over")
        self.assertEqual(self.app.mistakes_remaining, 0)
        self.app.retry_after_failure()
        self.assertEqual(self.app.current_screen, "game")
        self.assertEqual(self.app.game.remaining_arrows(), 13)
        self.assertEqual(self.app.mistakes_remaining, main.MAX_MISTAKES)

    def test_clearing_last_arrow_opens_level_result(self) -> None:
        self.app.game.board = [[None] * self.app.game.cols for _ in range(self.app.game.rows)]
        self.app.game.board[0][0] = "up"
        self.click_cell(0, 0)
        self.finish_animation()
        self.assertEqual(self.app.current_screen, "level_clear")
        self.app.advance_to_next_level()
        self.assertEqual(self.app.current_screen, "game")
        self.assertEqual(self.app.current_level_index, 1)
        self.assertEqual(self.app.game.remaining_arrows(), 17)

    def test_final_level_opens_all_clear(self) -> None:
        self.app.load_level(2)
        self.app.current_screen = "game"
        self.app.game.board = [[None] * self.app.game.cols for _ in range(self.app.game.rows)]
        self.app.game.board[0][0] = "up"
        self.click_cell(0, 0)
        self.finish_animation()
        self.assertEqual(self.app.current_screen, "all_clear")

    def test_all_pages_can_be_rendered(self) -> None:
        for screen in ("start", "game", "level_clear", "game_over", "all_clear"):
            self.app.current_screen = screen
            self.app.draw()
            self.assertEqual(self.app.screen.get_size(), (main.WINDOW_WIDTH, main.WINDOW_HEIGHT))


if __name__ == "__main__":
    unittest.main()

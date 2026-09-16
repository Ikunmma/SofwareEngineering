"""Pygame 界面状态与交互集成测试。"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import pygame  # noqa: E402

import main  # noqa: E402
from advanced_logic import AdvancedBoard  # noqa: E402
from levels import LEVELS  # noqa: E402
from advanced_levels import ADVANCED_LEVELS  # noqa: E402


class PygameStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.save_path = Path(self.temp_dir.name) / "save_data.json"
        self.app = main.ArrowEscapeApp(create_display=False, save_path=self.save_path)
        self.app.start_new_game()

    def tearDown(self) -> None:
        pygame.quit()
        self.temp_dir.cleanup()

    def click_cell(self, row: int, col: int) -> None:
        self.app.on_board_click_pos(tuple(map(int, self.app.cell_center(row, col))))

    def finish_animation(self) -> None:
        if self.app.animation and self.app.animation["kind"] == "collision":
            self.app.update(main.COLLISION_DURATION + 0.1)
        elif self.app.animation:
            self.app.update(3.0)

    def first_blocked_cell(self) -> tuple[int, int]:
        removable = set(self.app.game.removable_arrows())
        return next(
            (row, col)
            for row in range(self.app.game.rows)
            for col in range(self.app.game.cols)
            if self.app.game.board[row][col] is not None and (row, col) not in removable
        )

    def test_start_page_opens_level_map_then_enters_game(self) -> None:
        self.app.show_start_screen()
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.start_button.rect.center
        )
        self.app.handle_event(event)
        self.assertEqual(self.app.current_screen, "level_select")
        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.level_card_rects[0].center
        ))
        self.assertEqual(self.app.current_screen, "game")
        self.assertEqual(self.app.game.remaining_arrows(), 25)

    def test_help_modal_opens_closes_and_blocks_start(self) -> None:
        self.app.show_start_screen()
        open_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.help_button.rect.center
        )
        self.app.handle_event(open_event)
        self.assertTrue(self.app.help_visible)

        start_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.start_button.rect.center
        )
        self.app.handle_event(start_event)
        self.assertEqual(self.app.current_screen, "start")

        close_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.help_close_rect.center
        )
        self.app.handle_event(close_event)
        self.assertFalse(self.app.help_visible)

    def test_mode_selector_starts_advanced_mode(self) -> None:
        self.app.show_start_screen()
        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.start_button.rect.center
        ))
        mode_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.level_mode_advanced_rect.center
        )
        self.app.handle_event(mode_event)
        self.assertEqual(self.app.selected_mode, "advanced")
        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.level_card_rects[0].center
        ))
        self.assertIsInstance(self.app.game, AdvancedBoard)
        self.assertEqual((self.app.game.rows, self.app.game.cols), (16, 12))

    def test_level_select_page_switches_mode_and_opens_chosen_level(self) -> None:
        self.app.show_start_screen()
        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.start_button.rect.center))
        self.assertEqual(self.app.current_screen, "level_select")
        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.level_mode_advanced_rect.center))
        self.assertEqual(self.app.selected_mode, "advanced")
        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.level_card_rects[3].center))
        self.assertEqual(self.app.current_screen, "game")
        self.assertEqual(self.app.current_level_index, 3)
        self.assertEqual((self.app.game.rows, self.app.game.cols), (22, 18))

    def test_game_and_result_pages_can_return_to_level_map(self) -> None:
        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.home_button.rect.center))
        self.assertEqual(self.app.current_screen, "level_select")

        for screen in ("level_clear", "game_over", "all_clear"):
            self.app.current_screen = screen
            self.app.handle_event(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1,
                pos=self.app.result_back_button.rect.center))
            self.assertEqual(self.app.current_screen, "level_select")

    def test_advanced_path_click_flies_out_as_a_whole(self) -> None:
        self.app.selected_mode = "advanced"
        self.app.start_new_game()
        arrow_id = self.app.game.removable_arrows()[0]
        row, col = self.app.game.path(arrow_id).cells[0]
        before = self.app.game.remaining_arrows()
        self.click_cell(row, col)
        self.assertEqual(self.app.animation["arrow_id"], arrow_id)
        self.finish_animation()
        self.assertEqual(self.app.game.remaining_arrows(), before - 1)

    def test_hint_selects_a_currently_removable_arrow(self) -> None:
        initial_score = self.app.level_score
        self.app.show_hint()
        self.assertIn(self.app.hint_cell, self.app.game.removable_arrows())
        self.assertIn("提示", self.app.feedback)
        self.assertEqual(self.app.hints_remaining, main.MAX_HINTS - 1)
        self.assertEqual(self.app.level_score, max(0, initial_score - main.HINT_PENALTY))
        self.app.selected_mode = "advanced"
        self.app.start_new_game()
        self.app.show_hint()
        self.assertIn(self.app.hint_arrow_id, self.app.game.removable_arrows())
        self.assertIn("提示", self.app.feedback)

    def test_hint_limit_and_restart_restores_count(self) -> None:
        for _ in range(main.MAX_HINTS):
            self.app.show_hint()
        self.assertEqual(self.app.hints_remaining, 0)
        previous_hint = self.app.hint_cell
        self.app.show_hint()
        self.assertEqual(self.app.hint_cell, previous_hint)
        self.assertIn("用完", self.app.feedback)
        self.app.restart_board()
        self.assertEqual(self.app.hints_remaining, main.MAX_HINTS)

    def test_all_advanced_levels_clear_through_mouse_events_and_animation(self) -> None:
        self.app.selected_mode = "advanced"
        self.app.start_new_game()
        for index, level in enumerate(ADVANCED_LEVELS):
            self.assertEqual(self.app.current_level_index, index)
            for _ in level.paths:
                if self.app.hints_remaining:
                    self.app.handle_event(pygame.event.Event(
                        pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.hint_rect.center))
                    ident = self.app.hint_arrow_id
                else:
                    ident = self.app.game.removable_arrows()[0]
                self.assertIsNotNone(ident)
                head = self.app.game.path(ident).cells[-1]
                self.app.handle_event(pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN, button=1,
                    pos=tuple(map(int, self.app.cell_center(*head)))))
                self.assertEqual(self.app.animation["kind"], "flight")
                for frame in range(600):
                    self.app.update(1 / 60)
                    if frame == 10:
                        self.app.draw()
                    if not self.app.animating:
                        break
                self.assertFalse(self.app.animating)
                self.assertEqual(self.app.mistakes_remaining, main.MAX_MISTAKES)
            self.assertEqual(self.app.game.remaining_arrows(), 0)
            expected = "all_clear" if index == len(ADVANCED_LEVELS) - 1 else "level_clear"
            self.assertEqual(self.app.current_screen, expected)
            if expected == "level_clear":
                self.app.handle_event(pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN, button=1, pos=self.app.next_button.rect.center))

    def test_flying_body_follows_original_path_and_retains_length(self) -> None:
        self.app.selected_mode = "advanced"
        self.app.start_new_game()
        ident = max(self.app.game.active_ids, key=lambda i: len(self.app.game.path(i).cells))
        path = self.app.game.path(ident)
        size = self.app.board_geometry()[2]
        length = (len(path.cells) - 1) * size
        for travel in (0, size * 0.5, size * 2.5, length, length + 200):
            points = self.app.advanced_flight_points(ident, travel)
            actual = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(points, points[1:]))
            self.assertAlmostEqual(actual, length)
        self.assertEqual(self.app.advanced_flight_points(ident, size)[0],
                         self.app.cell_center(*path.cells[1]))

    def test_restart_restores_board_and_mistakes(self) -> None:
        initial_count = self.app.game.remaining_arrows()
        self.click_cell(*self.app.game.removable_arrows()[0])
        self.finish_animation()
        self.assertEqual(self.app.game.remaining_arrows(), initial_count - 1)
        self.click_cell(*self.first_blocked_cell())
        self.finish_animation()
        self.assertEqual(self.app.mistakes_remaining, 2)
        self.app.restart_board()
        self.assertEqual(self.app.game.remaining_arrows(), initial_count)
        self.assertEqual(self.app.mistakes_remaining, main.MAX_MISTAKES)
        self.assertIn("已恢复", self.app.feedback)

    def test_timer_score_and_collision_penalty(self) -> None:
        self.app.update(2.4)
        self.assertAlmostEqual(self.app.elapsed_time, 2.4)
        initial_score = self.app.level_score
        self.click_cell(*self.app.game.removable_arrows()[0])
        self.finish_animation()
        self.assertEqual(self.app.level_score, initial_score + main.ARROW_SCORE)
        self.click_cell(*self.first_blocked_cell())
        self.finish_animation()
        self.assertEqual(
            self.app.level_score,
            initial_score + main.ARROW_SCORE - main.COLLISION_PENALTY,
        )

    def test_restart_resets_timer_score_and_stars(self) -> None:
        self.app.elapsed_time = 18.0
        self.app.level_score = 1234
        self.app.earned_stars = 2
        self.app.restart_board()
        self.assertEqual(self.app.elapsed_time, 0.0)
        self.assertEqual(self.app.level_score, main.STARTING_SCORE)
        self.assertEqual(self.app.earned_stars, 0)

    def test_clear_awards_three_stars_and_completion_bonuses(self) -> None:
        self.app.game.board = [[None] * self.app.game.cols for _ in range(self.app.game.rows)]
        self.app.game.board[0][0] = "up"
        self.app.elapsed_time = 10.0
        self.click_cell(0, 0)
        self.finish_animation()
        self.assertEqual(self.app.earned_stars, 3)
        self.assertGreater(self.app.level_score, main.STARTING_SCORE + main.ARROW_SCORE)
        self.assertEqual(self.app.total_score, self.app.level_score)
        self.assertEqual(self.app.level_records["basic"][0], 3)
        frozen_time = self.app.elapsed_time
        self.app.update(5.0)
        self.assertEqual(self.app.elapsed_time, frozen_time)

    def test_level_map_keeps_best_stars_separately_for_each_mode(self) -> None:
        self.app.earned_stars = 3
        self.app.level_scored = False
        self.app.finish_level_stats()
        self.app.reset_level_stats()
        self.app.mistakes_remaining = 1
        self.app.elapsed_time = self.app.par_time * 2
        self.app.finish_level_stats()
        self.assertEqual(self.app.level_records["basic"][0], 3)
        self.assertEqual(self.app.level_records["advanced"], {})
        self.app.current_screen = "level_select"
        self.app.draw()

    def test_progress_is_saved_and_restored(self) -> None:
        self.app.selected_mode = "advanced"
        self.app.selected_level_index = 3
        self.app.total_score = 2460
        self.app.level_records = {"basic": {0: 3, 2: 1}, "advanced": {1: 2}}
        self.assertTrue(self.app.save_progress())

        restored = main.ArrowEscapeApp(create_display=False, save_path=self.save_path)
        self.assertEqual(restored.selected_mode, "advanced")
        self.assertEqual(restored.selected_level_index, 3)
        self.assertEqual(restored.total_score, 2460)
        self.assertEqual(restored.level_records["basic"], {0: 3, 2: 1})
        self.assertEqual(restored.level_records["advanced"], {1: 2})

    def test_corrupt_progress_file_falls_back_to_defaults(self) -> None:
        self.save_path.write_text("{not valid json", encoding="utf-8")
        restored = main.ArrowEscapeApp(create_display=False, save_path=self.save_path)
        self.assertEqual(restored.selected_mode, "basic")
        self.assertEqual(restored.selected_level_index, 0)
        self.assertEqual(restored.total_score, 0)
        self.assertEqual(restored.level_records, {"basic": {}, "advanced": {}})

    def test_invalid_progress_values_are_ignored_or_clamped(self) -> None:
        self.save_path.write_text(json.dumps({
            "version": main.SAVE_VERSION,
            "selected_mode": "advanced",
            "selected_level": 999,
            "total_score": -50,
            "level_records": {
                "basic": {"0": 3, "1": 9, "bad": 2},
                "advanced": {"2": 2, "99": 3},
            },
        }), encoding="utf-8")
        restored = main.ArrowEscapeApp(create_display=False, save_path=self.save_path)
        self.assertEqual(restored.selected_level_index, len(ADVANCED_LEVELS) - 1)
        self.assertEqual(restored.total_score, 0)
        self.assertEqual(restored.level_records["basic"], {0: 3})
        self.assertEqual(restored.level_records["advanced"], {2: 2})

    def test_clear_progress_requires_confirmation_and_deletes_save(self) -> None:
        self.app.total_score = 1800
        self.app.level_records = {"basic": {0: 3}, "advanced": {1: 2}}
        self.assertTrue(self.app.save_progress())
        self.assertTrue(self.save_path.exists())
        self.app.current_screen = "level_select"

        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1,
            pos=self.app.clear_progress_button.rect.center,
        ))
        self.assertTrue(self.app.clear_confirm_visible)
        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1,
            pos=self.app.clear_cancel_button.rect.center,
        ))
        self.assertFalse(self.app.clear_confirm_visible)
        self.assertTrue(self.save_path.exists())
        self.assertEqual(self.app.total_score, 1800)

        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1,
            pos=self.app.clear_progress_button.rect.center,
        ))
        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1,
            pos=self.app.clear_confirm_button.rect.center,
        ))
        self.assertFalse(self.app.clear_confirm_visible)
        self.assertFalse(self.save_path.exists())
        self.assertEqual(self.app.total_score, 0)
        self.assertEqual(self.app.level_records, {"basic": {}, "advanced": {}})
        self.assertEqual(self.app.selected_mode, "basic")
        self.assertIn("已清除", self.app.progress_notice)

    def test_clear_confirmation_blocks_level_selection(self) -> None:
        self.app.current_screen = "level_select"
        self.app.clear_confirm_visible = True
        self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1,
            pos=self.app.level_card_rects[2].center,
        ))
        self.assertEqual(self.app.current_screen, "level_select")
        self.assertTrue(self.app.clear_confirm_visible)

    def test_star_rating_boundaries(self) -> None:
        self.app.mistakes_remaining = 2
        self.app.elapsed_time = self.app.par_time
        self.app.finish_level_stats()
        self.assertEqual(self.app.earned_stars, 2)

        self.app.reset_level_stats()
        self.app.mistakes_remaining = 1
        self.app.elapsed_time = self.app.par_time * 2
        self.app.finish_level_stats()
        self.assertEqual(self.app.earned_stars, 1)

    def test_time_format(self) -> None:
        self.assertEqual(self.app.format_time(0), "00:00")
        self.assertEqual(self.app.format_time(65.9), "01:05")

    def test_animation_locks_restart(self) -> None:
        self.click_cell(*self.app.game.removable_arrows()[0])
        self.assertTrue(self.app.animating)
        self.app.restart_board()
        self.assertTrue(self.app.animating)
        self.assertIn("动画结束", self.app.feedback)

    def test_three_collisions_open_failure_page(self) -> None:
        blocked_cell = self.first_blocked_cell()
        for _ in range(3):
            self.click_cell(*blocked_cell)
            self.finish_animation()
        self.assertEqual(self.app.current_screen, "game_over")
        self.assertEqual(self.app.mistakes_remaining, 0)
        self.app.retry_after_failure()
        self.assertEqual(self.app.current_screen, "game")
        self.assertEqual(self.app.game.remaining_arrows(), 25)
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
        expected = sum(cell is not None for row in LEVELS[1].board for cell in row)
        self.assertEqual(self.app.game.remaining_arrows(), expected)

    def test_final_level_opens_all_clear(self) -> None:
        self.app.load_level(len(LEVELS) - 1)
        self.app.current_screen = "game"
        self.app.game.board = [[None] * self.app.game.cols for _ in range(self.app.game.rows)]
        self.app.game.board[0][0] = "up"
        self.click_cell(0, 0)
        self.finish_animation()
        self.assertEqual(self.app.current_screen, "all_clear")

    def test_all_pages_can_be_rendered(self) -> None:
        for screen in ("start", "level_select", "game", "level_clear", "game_over", "all_clear"):
            self.app.current_screen = screen
            self.app.draw()
            self.assertEqual(self.app.screen.get_size(), (main.WINDOW_WIDTH, main.WINDOW_HEIGHT))
        self.app.selected_mode = "advanced"
        self.app.start_new_game()
        self.app.draw()


if __name__ == "__main__":
    unittest.main()

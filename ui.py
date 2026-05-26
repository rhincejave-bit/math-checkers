"""
ui.py - Cleaned, robust UI for Math Checkers

Drop-in replacement for your original ui.py. Preserves visuals/behavior but fixes:
- missing attribute crashes
- invisible popup (draw order)
- deselection bug
- wrong-answer => AI freeze bug
- background scaling & resizing
- safe sound loading
- AI only moves when in game state
"""

import pygame
import sys
import os
from typing import Optional, Tuple, List
from game import GameState
from board import Board
from mathgen import MathQuestion

pygame.init()
FONT = pygame.font.SysFont("Arial", 20)
SMALL = pygame.font.SysFont("Arial", 16)
BIG = pygame.font.SysFont("Arial", 28)

# Colors
WHITE_COLOR = (240, 240, 240)
BLACK_COLOR = (30, 30, 30)
RED = (200, 30, 30)

# Themes
THEMES = {
    "wood": {"light": (222, 184, 135), "dark": (139, 69, 19)},
    "marble": {"light": (235, 235, 245), "dark": (180, 180, 200)},
}
current_theme = "wood"

# sizing
SCREEN_W = 1000
SCREEN_H = 700
SQUARE_SIZE = 64


class UI:
    def update_layout(self):
        """Compute positions from current window size"""
        self.WIDTH, self.HEIGHT = self.screen.get_size()

        total_w = Board.COLS * SQUARE_SIZE
        total_h = Board.ROWS * SQUARE_SIZE

        # center board
        self.board_x = (self.WIDTH - total_w) // 2
        self.board_y = (self.HEIGHT - total_h) // 2 + 30  # slight downward shift for title

        # right side UI panel
        self.ui_start_x = self.board_x + total_w + 40
        self.ui_start_y = self.board_y + 40

    def __init__(self):
        import os
        from game import GameState

        self.game_over = False
        # window + layout
        self.WIDTH = SCREEN_W
        self.HEIGHT = SCREEN_H
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Checkers with Math Challenges")

        # must init UI lists and state BEFORE any drawing/click code runs
        self.state = "menu"
        self.selected = None
        self.message = ""
        self.awaiting_question: Optional[MathQuestion] = None
        self.pending_move = None
        self.answer_text = ""
        self.clock = pygame.time.Clock()
        self.running = True

        # UI lists used by menu screens
        self.menu_buttons: List[Tuple[str, Optional[pygame.Rect]]] = [("Play", None), ("Settings", None), ("Exit", None)]
        self.play_buttons: List[Tuple[str, Optional[pygame.Rect]]] = []
        self.difficulty_buttons: List[Tuple[str, Optional[pygame.Rect]]] = []
        self.settings_options = ["Wood", "Marble", "Gradient", "Dark"]
        self.selected_theme = 0
        self.selected_math_type = None

        # game-over popup rects (initialized None)
        self.restart_rect = None
        self.menu_rect = None
        self.winner = None

        # board geometry (computed by update_layout)
        self.board_w = Board.COLS * SQUARE_SIZE
        self.board_h = Board.ROWS * SQUARE_SIZE

        # load background safely (scale once to initial window, keep source in self.bg_orig)
        self.bg = None
        self.bg_orig = None
        try:
            bg_path = os.path.join(os.path.dirname(__file__), "bg.png")
            if os.path.exists(bg_path):
                self.bg_orig = pygame.image.load(bg_path).convert()
                # initial scale
                self.bg = pygame.transform.smoothscale(self.bg_orig, (self.WIDTH, self.HEIGHT))
        except Exception as e:
            print(f"⚠️ Background not loaded: {e}")
            self.bg = None
            self.bg_orig = None

        # create initial layout
        self.update_layout()

        # --- Game settings ---
        self.gs = GameState(
            mode="ai",
            ai_difficulty=3,
            math_ops=["add", "sub", "mul"],
            timed_mode=False,
            time_limit=25.0,
        )
        # ensure AI object if needed
        if self.gs.mode == "ai" and getattr(self.gs, "ai", None) is None:
            try:
                from ai import AI
                self.gs.ai = AI(color="B", difficulty=self.gs.options.get("ai_difficulty", 2))
            except Exception:
                self.gs.ai = None

        # Safe audio
        assets = os.path.dirname(__file__)
        try:
            pygame.mixer.music.load(os.path.join(assets, "bg_music.mp3"))
            pygame.mixer.music.set_volume(0.35)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

        def _safe_sound(name):
            try:
                p = pygame.mixer.Sound(os.path.join(assets, name))
                p.set_volume(1.0)
                return p
            except Exception:
                return None

        self.sfx_move = _safe_sound("move.wav")
        self.sfx_capture = _safe_sound("capture.wav")
        self.sfx_button = _safe_sound("button.wav")

    # ---------------- Drawing ----------------
    def draw_board(self):
        # background shadow
        shadow = pygame.Rect(self.board_x + 6, self.board_y + 6, self.board_w, self.board_h)
        pygame.draw.rect(self.screen, (0, 0, 0, 90), shadow, border_radius=10)

        theme = THEMES.get(current_theme, THEMES["wood"])
        for r in range(Board.ROWS):
            for c in range(Board.COLS):
                x = self.board_x + c * SQUARE_SIZE
                y = self.board_y + r * SQUARE_SIZE
                color = theme["dark"] if (r + c) % 2 else theme["light"]
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

                op = self.gs.board.operator_at((r, c))
                if op:
                    op_symbol = {"*": "×", "/": "÷"}.get(op, op)
                    op_txt = BIG.render(op_symbol, True, (10, 70, 60))
                    self.screen.blit(op_txt, (x + 20, y + 6))

                piece = self.gs.board.get((r, c))
                if piece:
                    center = (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)
                    radius = SQUARE_SIZE // 2 - 6
                    fill = (240, 230, 200) if piece.color == "W" else (80, 50, 30)
                    pygame.draw.circle(self.screen, fill, center, radius)

                    val_txt = FONT.render(str(piece.value), True, (0, 0, 0) if piece.color == "W" else (255, 255, 255))
                    self.screen.blit(val_txt, (center[0] - val_txt.get_width() // 2, center[1] - val_txt.get_height() // 2))

                    if piece.king:
                        k_txt = FONT.render("K", True, (200, 0, 0))
                        self.screen.blit(k_txt, (center[0] - k_txt.get_width() // 2, center[1] - k_txt.get_height() // 2))

        # highlight selected
        if self.selected:
            r, c = self.selected
            x = self.board_x + c * SQUARE_SIZE
            y = self.board_y + r * SQUARE_SIZE
            pygame.draw.rect(self.screen, (0, 255, 120), (x - 2, y - 2, SQUARE_SIZE + 4, SQUARE_SIZE + 4), 4, border_radius=6)

        # highlight legal moves
        if self.selected:
            moves = self.gs.board.legal_moves_from(self.selected)
            for (rr, cc) in moves:
                cx = self.board_x + cc * SQUARE_SIZE + SQUARE_SIZE // 2
                cy = self.board_y + rr * SQUARE_SIZE + SQUARE_SIZE // 2
                pygame.draw.circle(self.screen, (0, 150, 255), (cx, cy), 10)

    def draw_ui(self):
        start_x = self.ui_start_x
        start_y = self.ui_start_y
        y = start_y

        panel_w = 200
        panel_h = 350
        glass = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        glass.fill((255, 255, 255, 120))
        pygame.draw.rect(glass, (255, 255, 255, 120), (0, 0, panel_w, panel_h), border_radius=15)
        self.screen.blit(glass, (start_x - 20, start_y - 20))

        info = SMALL.render(f"Turn: {'White' if self.gs.turn == 'W' else 'Black'}", True, BLACK_COLOR)
        self.screen.blit(info, (start_x, y)); y += 25
        mode = SMALL.render(f"Mode: {self.gs.mode}", True, BLACK_COLOR)
        self.screen.blit(mode, (start_x, y)); y += 25

        score_w = self.gs.scores.get("W", 0)
        score_b = self.gs.scores.get("B", 0)
        self.screen.blit(SMALL.render("Scores:", True, BLACK_COLOR), (start_x, y)); y += 20
        self.screen.blit(SMALL.render(f"White: {score_w}", True, BLACK_COLOR), (start_x, y)); y += 20
        self.screen.blit(SMALL.render(f"Black: {score_b}", True, BLACK_COLOR), (start_x, y)); y += 30

        buttons = [("New", (start_x, y)), ("Undo", (start_x + 90, y)),
                   ("Save", (start_x, y + 40)), ("Load", (start_x + 90, y + 40))]
        for label, pos in buttons:
            pygame.draw.rect(self.screen, (200, 200, 200), (*pos, 80, 32), border_radius=6)
            txt = SMALL.render(label, True, BLACK_COLOR)
            self.screen.blit(txt, (pos[0] + 10, pos[1] + 8))

        y += 90
        toggles = [("Toggle Mode", (start_x, y)), ("Toggle Timed", (start_x, y + 40))]
        for label, pos in toggles:
            pygame.draw.rect(self.screen, (220, 220, 220), (*pos, 160, 32), border_radius=6)
            txt = SMALL.render(label, True, BLACK_COLOR)
            self.screen.blit(txt, (pos[0] + 6, pos[1] + 6))

        msg = SMALL.render(self.message, True, RED)
        self.screen.blit(msg, (start_x, y + 90))

    def draw_question_modal(self):
        """Draw a centered modal and block input (must call after drawing background/board/ UI)."""
        cur_w, cur_h = self.screen.get_size()
        w, h = 420, 160
        x = (cur_w - w) // 2
        y = (cur_h - h) // 2

        # dim background (semi-transparent overlay)
        overlay = pygame.Surface((cur_w, cur_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # popup box
        pygame.draw.rect(self.screen, (245, 245, 245), (x, y, w, h), border_radius=10)
        pygame.draw.rect(self.screen, BLACK_COLOR, (x, y, w, h), 2, border_radius=10)

        title = BIG.render("Math Question", True, BLACK_COLOR)
        self.screen.blit(title, (x + 10, y + 8))
        expr = self.awaiting_question.text if self.awaiting_question else "?"
        expr_surf = FONT.render(expr, True, BLACK_COLOR)
        self.screen.blit(expr_surf, (x + 10, y + 50))

        pygame.draw.rect(self.screen, (255, 255, 255), (x + 10, y + 90, w - 20, 36), border_radius=6)
        pygame.draw.rect(self.screen, (0, 0, 0), (x + 10, y + 90, w - 20, 36), 2, border_radius=6)
        ans = FONT.render(self.answer_text, True, (0, 0, 0))
        self.screen.blit(ans, (x + 14, y + 94))

        hint = SMALL.render("Type your answer, then press Enter. Esc cancels", True, (50, 50, 50))
        self.screen.blit(hint, (x + 10, y + 130))

    def draw_menu(self):
        self.screen.fill((30, 30, 40))
        w, h = self.screen.get_size()
        title = BIG.render("♟ Math Checkers ♟", True, (240, 240, 240))
        self.screen.blit(title, ((w - title.get_width()) // 2, 80))

        btn_w, btn_h = 300, 56
        gap = 18
        start_y = 180
        labels = ["Play", "Settings", "Exit"]
        for i, label in enumerate(labels):
            x = (w - btn_w) // 2
            y = start_y + i * (btn_h + gap)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, border_radius=8)
            txt = FONT.render(label, True, (20, 20, 20))
            self.screen.blit(txt, (x + (btn_w - txt.get_width()) // 2, y + (btn_h - txt.get_height()) // 2))
            # store rect (make sure list length okay)
            if len(self.menu_buttons) <= i:
                self.menu_buttons.append((label, rect))
            else:
                self.menu_buttons[i] = (label, rect)

    def draw_play_select(self):
        # reset selected math type when opening
        self.selected_math_type = None
        self.screen.fill((25, 25, 35))
        w, h = self.screen.get_size()
        title = BIG.render("Select Math Type", True, (240, 240, 240))
        self.screen.blit(title, ((w - title.get_width()) // 2, 80))

        labels = ["Integers", "Fractions", "Algebra", "Back"]
        btn_w, btn_h, gap = 300, 56, 18
        start_y = 180
        self.play_buttons = []
        for i, label in enumerate(labels):
            x = (w - btn_w) // 2
            y = start_y + i * (btn_h + gap)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, border_radius=8)
            txt = FONT.render(label, True, (20, 20, 20))
            self.screen.blit(txt, (x + (btn_w - txt.get_width()) // 2, y + (btn_h - txt.get_height()) // 2))
            self.play_buttons.append((label, rect))

    def draw_difficulty_select(self):
        self.screen.fill((25, 25, 35))
        w, h = self.screen.get_size()
        title = BIG.render(f"{self.selected_math_type} – Choose Difficulty", True, (240, 240, 240))
        self.screen.blit(title, ((w - title.get_width()) // 2, 80))

        labels = ["Easy", "Average", "Hard", "Back"]
        btn_w, btn_h, gap = 300, 56, 18
        start_y = 180
        self.difficulty_buttons = []
        for i, label in enumerate(labels):
            x = (w - btn_w) // 2
            y = start_y + i * (btn_h + gap)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, border_radius=8)
            txt = FONT.render(label, True, (20, 20, 20))
            self.screen.blit(txt, (x + (btn_w - txt.get_width()) // 2, y + (btn_h - txt.get_height()) // 2))
            self.difficulty_buttons.append((label, rect))

    def draw_settings(self):
        self.screen.fill((36, 40, 44))
        w, h = self.screen.get_size()
        title = BIG.render("Settings", True, (240, 240, 240))
        self.screen.blit(title, ((w - title.get_width()) // 2, 40))

        label = SMALL.render("Select Background Theme:", True, (220, 220, 220))
        self.screen.blit(label, (120, 120))

        start_y = 160
        for i, opt in enumerate(self.settings_options):
            y = start_y + i * 36
            cx = 140
            cy = y + 8
            pygame.draw.circle(self.screen, (200, 200, 200), (cx, cy), 8, 1)
            if i == self.selected_theme:
                pygame.draw.circle(self.screen, (200, 200, 200), (cx, cy), 4)
            txt = SMALL.render(opt, True, (230, 230, 230))
            self.screen.blit(txt, (cx + 20, y))

        btn_w, btn_h = 120, 40
        apply_rect = pygame.Rect(w - 280, h - 120, btn_w, btn_h)
        back_rect = pygame.Rect(w - 140, h - 120, btn_w, btn_h)
        pygame.draw.rect(self.screen, (180, 180, 180), apply_rect, border_radius=6)
        pygame.draw.rect(self.screen, (180, 180, 180), back_rect, border_radius=6)
        self.screen.blit(SMALL.render("Apply", True, (10, 10, 10)), (apply_rect.x + 24, apply_rect.y + 10))
        self.screen.blit(SMALL.render("Back", True, (10, 10, 10)), (back_rect.x + 30, back_rect.y + 10))

        self.apply_rect = apply_rect
        self.back_rect = back_rect

    # ---------------- Input handlers ----------------
    def handle_menu_click(self, pos):
        if self.state == "menu":
            for label, rect in self.menu_buttons:
                if rect and rect.collidepoint(pos):
                    if label == "Play":
                        self.selected_math_type = None
                        self.play_buttons = []
                        self.difficulty_buttons = []
                        self.state = "play_select"
                        return
                    if label == "Settings":
                        self.state = "settings"
                        return
                    if label == "Exit":
                        pygame.quit()
                        sys.exit()
        elif self.state == "settings":
            x, y = pos
            w, h = self.screen.get_size()
            start_y = 160
            for i in range(len(self.settings_options)):
                item_rect = pygame.Rect(120, start_y + i * 36, 300, 28)
                if item_rect.collidepoint(pos):
                    self.selected_theme = i
                    return
            if hasattr(self, "apply_rect") and self.apply_rect.collidepoint(pos):
                self.message = f"Theme set to {self.settings_options[self.selected_theme]}"
                return
            if hasattr(self, "back_rect") and self.back_rect.collidepoint(pos):
                self.state = "menu"
                return

    def handle_play_click(self, pos):
        for label, rect in self.play_buttons:
            if rect.collidepoint(pos):
                if label == "Back":
                    self.selected_math_type = None
                    self.play_buttons = []
                    self.difficulty_buttons = []
                    self.state = "menu"
                    return
                else:
                    self.selected_math_type = label
                    self.difficulty_buttons = []
                    self.state = "difficulty_select"
                    return

    def handle_difficulty_click(self, pos):
        for label, rect in self.difficulty_buttons:
            if rect.collidepoint(pos):
                if label == "Back":
                    self.selected_math_type = None
                    self.difficulty_buttons = []
                    self.state = "play_select"
                    return
                else:
                    if not self.selected_math_type:
                        self.state = "play_select"
                        return
                    self.start_game_with_mode(self.selected_math_type, label)
                    return

    def start_game_with_mode(self, math_type, difficulty):
        diff_map = {"Easy": 1, "Average": 2, "Hard": 3}
        ops_map = {
            "Integers": ["add", "sub", "mul"],
            "Fractions": ["add", "sub"],
            "Algebra": ["add", "sub", "mul"],
        }
        self.gs = GameState(
            mode="ai",
            ai_difficulty=diff_map.get(difficulty, 2),
            math_ops=ops_map.get(math_type, ["add", "sub"]),
            timed_mode=False,
            time_limit=25.0,
        )
        if not hasattr(self.gs, "scores"):
            self.gs.scores = {"W": 0, "B": 0}
        # ensure ai object created when requested
        if self.gs.mode == "ai":
            try:
                from ai import AI
                self.gs.ai = AI(color="B", difficulty=self.gs.options.get("ai_difficulty", 2))
            except Exception:
                self.gs.ai = None
        self.state = "game"
        self.game_over = False
        self.winner = None
        self.winner_name = ""
        self.winner_scores = ""
        self.message = f"{math_type} – {difficulty} started"
        # reset UI selection state
        self.selected = None
        self.awaiting_question = None
        self.pending_move = None
        self.answer_text = ""

    def handle_click(self, pos):
        # handle winner popup buttons first
        if self.game_over:
            if self.restart_rect and self.restart_rect.collidepoint(pos):
                # Restart: reset game state and UI flags
                self.gs.reset()
                self.game_over = False
                self.winner = None
                self.winner_name = ""
                self.winner_scores = ""
                self.selected = None
                self.message = "New game started!"
                return
            if self.menu_rect and self.menu_rect.collidepoint(pos):
                # Back to main menu
                self.game_over = False
                self.winner = None
                self.winner_name = ""
                self.winner_scores = ""
                self.selected = None
                self.message = ""
                self.state = "menu"
                return
            return  # block all other clicks while popup is showing
        if self.awaiting_question is not None:
            return
        if self.gs.mode == "ai" and getattr(self.gs, "ai", None) and self.gs.turn == self.gs.ai.color:
            # do not allow human input during AI thinking
            self.message = "AI thinking..."
            return

        x, y = pos
        bx = x - self.board_x
        by = y - self.board_y
        board_w = Board.COLS * SQUARE_SIZE
        board_h = Board.ROWS * SQUARE_SIZE

        # CLICK ON BOARD
        if 0 <= bx < board_w and 0 <= by < board_h:
            c = bx // SQUARE_SIZE
            r = by // SQUARE_SIZE
            coord = (r, c)
            piece = self.gs.board.get(coord)

            # select if none
            if self.selected is None:
                if piece and piece.color == self.gs.turn:
                    self.selected = coord
                return

            # clicked same square -> deselect
            if coord == self.selected:
                self.selected = None
                return

            # clicked another friendly piece -> switch selection
            if piece and piece.color == self.gs.turn:
                self.selected = coord
                return

            # attempt move
            frm = self.selected
            to = coord
            res_try = self.gs.board.try_move(frm, to)
            if not res_try["valid"]:
                self.message = res_try.get("message", "Invalid move")
                return

            # capture -> ask math Q
            if res_try.get("capture"):
                q = self.gs.get_math_question_for_move(frm, to)
                if q:
                    self.pending_move = (frm, to, q)
                    self.prompt_question(q)
                    return
                else:
                    # fallback: apply capture without question
                    self.gs.push_undo() if hasattr(self.gs, "push_undo") else None
                    self.animate_move(frm, to)
                    apply_res = self.gs.board.apply_move(frm, to)
                    if apply_res.get("capture") and self.sfx_capture:
                        try:
                            self.sfx_capture.play()
                        except Exception:
                            pass
                    self.gs.move_count = getattr(self.gs, "move_count", 0) + 1
                    self.gs.capture_count = getattr(self.gs, "capture_count", 0) + (1 if apply_res.get("capture") else 0)
                    self.selected = None
                    self.check_game_over()
                    if not self.game_over:
                        self.gs.turn = "W" if self.gs.turn == "B" else "B"
                    return

            # normal move
            if self.sfx_move:
                try:
                    self.sfx_move.play()
                except Exception:
                    pass
            if hasattr(self.gs, "push_undo"):
                try:
                    self.gs.push_undo()
                except Exception:
                    pass
            self.animate_move(frm, to)
            self.gs.board.apply_move(frm, to)
            self.gs.move_count = getattr(self.gs, "move_count", 0) + 1
            self.selected = None

            # flip turn and maybe AI move (AI auto-move handled in run() main loop)
            self.gs.turn = "W" if self.gs.turn == "B" else "B"
            return

        # CLICK ON UI PANEL (right side)
        start_x = self.board_x + Board.COLS * SQUARE_SIZE + 40
        y_start = self.board_y + 40

        # New
        if start_x <= x <= start_x + 120 and y_start <= y <= y_start + 40:
            if self.sfx_button:
                try:
                    self.sfx_button.play()
                except Exception:
                    pass
            self.gs.reset()
            self.game_over = False
            self.winner = None
            self.winner_name = ""
            self.winner_scores = ""
            self.message = "New game"
            return

        # Undo
        if start_x <= x <= start_x + 120 and y_start + 50 <= y <= y_start + 90:
            if self.sfx_button:
                try:
                    self.sfx_button.play()
                except Exception:
                    pass
            ok = self.gs.undo()
            self.message = "Undo" if ok else "Nothing to undo"
            return

        # Save
        if start_x <= x <= start_x + 120 and y_start + 100 <= y <= y_start + 140:
            if self.sfx_button:
                try:
                    self.sfx_button.play()
                except Exception:
                    pass
            self.gs.save("savegame.json")
            self.message = "Saved"
            return

        # Load
        if start_x <= x <= start_x + 120 and y_start + 150 <= y <= y_start + 190:
            if self.sfx_button:
                try:
                    self.sfx_button.play()
                except Exception:
                    pass
            try:
                self.gs.load("savegame.json")
                self.message = "Loaded"
            except Exception as e:
                self.message = f"Load failed: {e}"
            return

        # Toggle mode
        if start_x <= x <= start_x + 120 and y_start + 200 <= y <= y_start + 240:
            if self.sfx_button:
                try:
                    self.sfx_button.play()
                except Exception:
                    pass
            self.gs.mode = "ai" if self.gs.mode == "2p" else "2p"
            if self.gs.mode == "ai":
                try:
                    from ai import AI
                    self.gs.ai = AI(color="B", difficulty=self.gs.options.get("ai_difficulty", 2))
                except Exception:
                    self.gs.ai = None
            else:
                self.gs.ai = None
            self.message = f"Mode: {self.gs.mode}"
            return
    # ---------------- Game helpers ----------------

    def animate_move(self, frm, to):
        """
        Simple move handler (no animation yet).
        Prevents crash when animate_move is called.
        """
        # For now, just do nothing (logic already applies move elsewhere)
        pass

    def prompt_question(self, question):
        """
        Show math question modal and block game input.
        """
        self.awaiting_question = question
        self.answer_text = ""
        self.message = "Answer the question to continue."

    def check_game_over(self):
        """
        Check if game is finished and store result for popup.
        """
        try:
            winner = self.gs.check_winner()
        except Exception:
            winner = None

        if winner:
            self.game_over = True
            self.winner = winner
            name = "White" if winner == "W" else "Black"
            w_score = self.gs.scores.get("W", 0)
            b_score = self.gs.scores.get("B", 0)
            self.winner_name = name
            self.winner_scores = f"White: {w_score} pts   |   Black: {b_score} pts"
            self.message = f"{name} wins!"


    def draw_winner_popup(self):
        """
        Draw Game Over popup with winner name, scores, and Restart/Menu buttons.
        """
        w, h = self.screen.get_size()

        box_w, box_h = 440, 240
        x = (w - box_w) // 2
        y = (h - box_h) // 2

        # Dark overlay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Popup box
        pygame.draw.rect(self.screen, (245, 245, 245), (x, y, box_w, box_h), border_radius=14)
        pygame.draw.rect(self.screen, (0, 0, 0), (x, y, box_w, box_h), 2, border_radius=14)

        # Trophy + Game Over title
        title = BIG.render("🏆 Game Over!", True, (30, 30, 30))
        self.screen.blit(title, (x + (box_w - title.get_width()) // 2, y + 20))

        # Winner name
        winner_name = getattr(self, "winner_name", "Unknown")
        winner_surf = FONT.render(f"{winner_name} wins!", True, (180, 50, 50))
        self.screen.blit(winner_surf, (x + (box_w - winner_surf.get_width()) // 2, y + 70))

        # Scores
        scores_str = getattr(self, "winner_scores", "")
        scores_surf = SMALL.render(scores_str, True, (60, 60, 60))
        self.screen.blit(scores_surf, (x + (box_w - scores_surf.get_width()) // 2, y + 105))

        # Buttons: Restart + Menu
        btn_w, btn_h = 160, 42
        gap = 20
        total_btn_w = btn_w * 2 + gap
        btn_y = y + 155

        restart_x = x + (box_w - total_btn_w) // 2
        menu_x = restart_x + btn_w + gap

        self.restart_rect = pygame.Rect(restart_x, btn_y, btn_w, btn_h)
        self.menu_rect = pygame.Rect(menu_x, btn_y, btn_w, btn_h)

        pygame.draw.rect(self.screen, (100, 180, 100), self.restart_rect, border_radius=8)
        pygame.draw.rect(self.screen, (100, 130, 200), self.menu_rect, border_radius=8)

        r_txt = FONT.render("▶  Restart", True, (255, 255, 255))
        m_txt = FONT.render("⌂  Menu", True, (255, 255, 255))

        self.screen.blit(r_txt, (self.restart_rect.x + (btn_w - r_txt.get_width()) // 2,
                                  self.restart_rect.y + (btn_h - r_txt.get_height()) // 2))
        self.screen.blit(m_txt, (self.menu_rect.x + (btn_w - m_txt.get_width()) // 2,
                                  self.menu_rect.y + (btn_h - m_txt.get_height()) // 2))

        hint = SMALL.render("Press ESC to return to menu", True, (60, 60, 60))
        self.screen.blit(hint, (x + 90, y + 140))

    # ----------------- main loop -----------------
    def run(self):
        self.running = True
        while self.running:
            self.clock.tick(30)

            # EVENTS
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    break

                # window resized -> update layout and rescale bg preview
                if ev.type == pygame.VIDEORESIZE:
                    self.update_layout()
                    if self.bg_orig:
                        try:
                            self.bg = pygame.transform.smoothscale(self.bg_orig, self.screen.get_size())
                        except Exception:
                            self.bg = None

                # modal (math question) exclusive handling
                if self.awaiting_question is not None:
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_RETURN:
                            if not self.pending_move:
                                self.awaiting_question = None
                                self.answer_text = ""
                                continue
                            frm, to, q = self.pending_move
                            try:
                                res = self.gs.make_move_with_math(frm, to, self.answer_text, q)
                            except Exception as e:
                                res = {"valid": False, "message": f"Error: {e}"}

                            self.message = res.get("message", self.message)

                            if res.get("valid"):
                                # correct -> apply animation / sfx if needed
                                if self.sfx_move:
                                    try:
                                        self.sfx_move.play()
                                    except Exception:
                                        pass

                                if not res.get("applied", False):
                                    try:
                                        self.gs.push_undo()
                                    except Exception:
                                        pass
                                    self.animate_move(frm, to)
                                    apply_res = self.gs.board.apply_move(frm, to)
                                    if apply_res.get("capture") and self.sfx_capture:
                                        try:
                                            self.sfx_capture.play()
                                        except Exception:
                                            pass
                                    self.gs.move_count = getattr(self.gs, "move_count", 0) + 1
                                    if apply_res.get("capture"):
                                        self.gs.capture_count = getattr(self.gs, "capture_count", 0) + 1

                                self.check_game_over()
                                if not self.game_over:
                                    self.gs.turn = "W" if self.gs.turn == "B" else "B"
                                    # do not trigger AI here; AI auto-move handled below in main loop
                            else:
                                # wrong answer -> cancel move, keep player's turn
                                self.message = "Wrong! Move canceled."
                                self.selected = None
                                # DO NOT switch turn, DO NOT trigger AI

                            # always clear modal state
                            self.awaiting_question = None
                            self.pending_move = None
                            self.answer_text = ""
                        elif ev.key == pygame.K_ESCAPE:
                            self.awaiting_question = None
                            self.pending_move = None
                            self.answer_text = ""
                            self.message = "Question cancelled."
                        elif ev.key == pygame.K_BACKSPACE:
                            self.answer_text = self.answer_text[:-1]
                        elif ev.type == pygame.KEYDOWN:
                            ch = ev.unicode
                            if ch.isdigit() or (ch == "-" and not self.answer_text):
                                self.answer_text += ch
                    # swallow all other events while modal active
                    continue

                # normal input (no modal)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    pos = ev.pos
                    if self.state in ("menu", "settings"):
                        self.handle_menu_click(pos)
                    elif self.state == "game":
                        self.handle_click(pos)
                    elif self.state == "play_select":
                        self.handle_play_click(pos)
                    elif self.state == "difficulty_select":
                        self.handle_difficulty_click(pos)
                elif ev.type == pygame.KEYDOWN:
                    if self.state == "game":
                        if ev.key == pygame.K_u:
                            self.gs.undo()
                        elif ev.key == pygame.K_s:
                            self.gs.save("savegame.json")
                        elif ev.key == pygame.K_ESCAPE:
                            self.selected = None
                            self.message = "Selection cleared."

            # AI auto-move: only during game state and when no modal is active
            if (
                self.state == "game"
                and self.gs
                and self.gs.mode == "ai"
                and getattr(self.gs, "ai", None) is not None
                and self.gs.turn == self.gs.ai.color
                and self.awaiting_question is None
                and not self.game_over
            ):
                try:
                    ai_res = self.gs.make_move_ai()
                    if isinstance(ai_res, dict):
                        self.message = ai_res.get("message", self.message)
                        # play sfx for capture if reported
                        if ai_res.get("capture") and self.sfx_capture:
                            try:
                                self.sfx_capture.play()
                            except Exception:
                                pass
                        # AI applied move inside game.make_move_ai()
                        self.check_game_over()
                except Exception:
                    pass

            # RENDERING

            # Draw background scaled to current window
            if getattr(self, "bg", None):
                try:
                    bg_scaled = pygame.transform.smoothscale(self.bg, self.screen.get_size())
                    self.screen.blit(bg_scaled, (0, 0))
                except Exception:
                    self.screen.fill((255, 230, 240))
            else:
                self.screen.fill((255, 230, 240))

            # If modal active: draw board/UI underneath and then modal overlay; skip normal frame flipping after drawing modal
            if self.awaiting_question is not None:
                self.draw_board()
                # draw title above board
                title = BIG.render("Math Checkers", True, (0, 0, 0))
                title_x = self.board_x + (Board.COLS * SQUARE_SIZE - title.get_width()) // 2
                title_y = self.board_y - 50
                self.screen.blit(title, (title_x, title_y))
                self.draw_ui()
                self.draw_question_modal()
                pygame.display.flip()
                continue

            # normal state drawing
            if self.state == "game" and self.gs:
                self.draw_board()
                title = BIG.render("Math Checkers", True, (0, 0, 0))
                title_x = self.board_x + (Board.COLS * SQUARE_SIZE - title.get_width()) // 2
                title_y = self.board_y - 50
                self.screen.blit(title, (title_x, title_y))
                self.draw_ui()
                if self.game_over:
                    self.draw_winner_popup()
            elif self.state == "menu":
                self.draw_menu()
            elif self.state == "settings":
                self.draw_settings()
            elif self.state == "play_select":
                self.draw_play_select()
            elif self.state == "difficulty_select":
                self.draw_difficulty_select()
            else:
                self.screen.fill((30, 30, 30))

            pygame.display.flip()

        # cleanup
        pygame.quit()

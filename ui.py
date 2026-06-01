"""
ui.py — Math Checkers | Chess.com-Style Redesign
Classic Mode: standard math checkers
Enhanced Mode: ability cards, special pieces, chain captures
"""

import pygame
import sys
import os
import math
from typing import Optional, Tuple, List
from game import GameState
from board import Board
from mathgen import MathQuestion

pygame.init()

# ── Palette (Chess.com inspired) ─────────────────────────────────
BG          = (38, 36, 33)
BG2         = (28, 27, 25)
BOARD_DARK  = (118, 150, 86)
BOARD_LIGHT = (238, 238, 210)
PANEL_BG    = (45, 43, 40)
PANEL_BDR   = (70, 68, 65)
BTN_GREEN   = (129, 182, 76)
BTN_GREEN_H = (110, 158, 58)
BTN_DARK    = (60, 58, 55)
BTN_DARK_H  = (80, 78, 75)
BTN_RED     = (180, 60, 60)
BTN_BLUE    = (65, 105, 180)
BTN_GOLD    = (200, 162, 40)
TEXT_W      = (255, 255, 255)
TEXT_DIM    = (165, 162, 155)
TEXT_DARK   = (25, 24, 22)
ACCENT      = (240, 217, 181)
SELECT_CLR  = (246, 246, 105)
CHAIN_CLR   = (120, 220, 120)
RED_MSG     = (220, 80, 80)
GREEN_MSG   = (100, 200, 100)
GOLD_MSG    = (230, 185, 60)

# ── Full Game Themes ──────────────────────────────────────────────
GAME_THEMES = {
    "dark": {
        "name": "Dark Classic", "accent_name": "Green",
        "BG": (38, 36, 33),   "BG2": (28, 27, 25),
        "BOARD_DARK": (118, 150, 86),  "BOARD_LIGHT": (238, 238, 210),
        "PANEL_BG": (45, 43, 40),      "PANEL_BDR": (70, 68, 65),
        "BTN_GREEN": (129, 182, 76),   "BTN_GREEN_H": (110, 158, 58),
        "ACCENT": (240, 217, 181),     "SELECT_CLR": (246, 246, 105),
    },
    "ocean": {
        "name": "Ocean Blue", "accent_name": "Cyan",
        "BG": (12, 22, 40),   "BG2": (8, 15, 30),
        "BOARD_DARK": (45, 95, 155),   "BOARD_LIGHT": (195, 218, 248),
        "PANEL_BG": (18, 35, 62),      "PANEL_BDR": (42, 72, 118),
        "BTN_GREEN": (45, 165, 225),   "BTN_GREEN_H": (30, 140, 195),
        "ACCENT": (140, 215, 255),     "SELECT_CLR": (100, 240, 255),
    },
    "royal": {
        "name": "Royal Purple", "accent_name": "Gold",
        "BG": (22, 14, 38),   "BG2": (15, 9, 28),
        "BOARD_DARK": (95, 52, 158),   "BOARD_LIGHT": (228, 210, 255),
        "PANEL_BG": (38, 24, 64),      "PANEL_BDR": (80, 50, 130),
        "BTN_GREEN": (195, 155, 50),   "BTN_GREEN_H": (165, 130, 35),
        "ACCENT": (255, 215, 100),     "SELECT_CLR": (255, 235, 80),
    },
    "sunset": {
        "name": "Sunset Fire", "accent_name": "Orange",
        "BG": (32, 18, 12),   "BG2": (22, 12, 8),
        "BOARD_DARK": (175, 82, 35),   "BOARD_LIGHT": (255, 218, 175),
        "PANEL_BG": (52, 32, 20),      "PANEL_BDR": (100, 60, 35),
        "BTN_GREEN": (225, 105, 45),   "BTN_GREEN_H": (195, 85, 30),
        "ACCENT": (255, 195, 90),      "SELECT_CLR": (255, 220, 60),
    },
}

# ── Fonts ─────────────────────────────────────────────────────────
def _f(size, bold=False):
    for name in ("Segoe UI", "Calibri", "Arial", None):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

FT  = _f(15)
FS  = _f(17)
FM  = _f(21)
FL  = _f(28, bold=True)
FX  = _f(46, bold=True)
FXX = _f(60, bold=True)

# ── Layout ────────────────────────────────────────────────────────
SCREEN_W = 1120
SCREEN_H = 760
SQ = 70  # square size


# ── Drawing helpers ───────────────────────────────────────────────
def rrect(surf, color, rect, r=10, border=0, bc=None):
    pygame.draw.rect(surf, color, rect, border_radius=r)
    if border and bc:
        pygame.draw.rect(surf, bc, rect, border, border_radius=r)

def txt(surf, text, font, color, x, y, center=False):
    s = font.render(str(text), True, color)
    if center:
        surf.blit(s, (x - s.get_width()//2, y))
    else:
        surf.blit(s, (x, y))
    return s.get_width(), s.get_height()

def btn(surf, label, font, rect, bg, tc=TEXT_W, r=8, border=0, bc=None):
    rrect(surf, bg, rect, r, border, bc)
    s = font.render(label, True, tc)
    surf.blit(s, (rect.x + (rect.w - s.get_width())//2,
                   rect.y + (rect.h - s.get_height())//2))


class UI:
    # ── Init ─────────────────────────────────────────────────────
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        pygame.display.set_caption("Math Checkers")
        self.clock = pygame.time.Clock()
        self.running = True

        # State machine
        self.state = "menu"           # menu | mode_select | play_select | difficulty_select | settings | game
        self.game_mode = "classic"    # "classic" | "enhanced"
        self.opponent_mode = "ai"     # "ai" | "2p"
        self.selected_math_type = None
        self.selected_theme = "chess"

        # Game
        self.gs: Optional[GameState] = None
        self.selected = None
        self.message = ""
        self.msg_color = TEXT_DIM
        self.msg_timer = 0            # frames to show message
        self.game_over = False
        self.winner = None
        self.winner_name = ""
        self.winner_scores = ""

        # Math modal
        self.awaiting_question: Optional[MathQuestion] = None
        self.pending_move = None
        self.answer_text = ""
        self.skip_next_question = False  # ability: skip question

        # Ability card pending action
        self.pending_ability = None

        # UI rects (populated on draw)
        self.restart_rect = None
        self.menu_btn_rect = None
        self.ability_rects = {}   # card_name -> Rect

        # Board layout
        self.board_x = 80
        self.board_y = 60

        self.show_settings_overlay = False
        self.music_on = True
        self.sfx_on   = True
        self.music_vol = 0.3   # 0.1 / 0.3 / 0.6
        self.settings_tab = "appearance"   # appearance|audio|stats|credits|howto
        self.game_theme = "dark"

        # Statistics (persisted to stats.json)
        self.stats = {
            "games_played": 0, "games_won": 0, "games_lost": 0,
            "best_score": 0,   "total_captures": 0,
            "correct_answers": 0, "wrong_answers": 0,
            "highest_streak": 0, "classic_played": 0, "enhanced_played": 0,
        }
        self._load_stats()

        # Button rect storage
        self._btn_rects = {}

        # Load assets
        self._load_audio()

    def _load_audio(self):
        assets = os.path.dirname(__file__)
        try:
            pygame.mixer.music.load(os.path.join(assets, "bg_music.mp3"))
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

        def _snd(name):
            try:
                s = pygame.mixer.Sound(os.path.join(assets, name))
                s.set_volume(0.8)
                return s
            except Exception:
                return None

        self.sfx_move    = _snd("move.wav")
        self.sfx_capture = _snd("capture.wav")
        self.sfx_btn     = _snd("button.wav")

    def set_message(self, msg, color=TEXT_DIM, frames=120):
        self.message = msg
        self.msg_color = color
        self.msg_timer = frames

    # ── Theme application ─────────────────────────────────────────
    def apply_game_theme(self, theme_key):
        """Update all module-level color globals for the selected theme."""
        theme = GAME_THEMES.get(theme_key)
        if not theme:
            return
        self.game_theme = theme_key
        import ui as _ui_mod
        g = vars(_ui_mod)
        for k, v in theme.items():
            if k in g and isinstance(v, tuple):
                g[k] = v

    # ── Stats persistence ─────────────────────────────────────────
    def _load_stats(self):
        import json, os
        path = os.path.join(os.path.dirname(__file__), "stats.json")
        try:
            with open(path) as f:
                saved = json.load(f)
                self.stats.update(saved)
        except Exception:
            pass

    def _save_stats(self):
        import json, os
        path = os.path.join(os.path.dirname(__file__), "stats.json")
        try:
            with open(path, "w") as f:
                json.dump(self.stats, f, indent=2)
        except Exception:
            pass

    def _record_game_end(self, winner):
        """Call when a game ends to update statistics."""
        self.stats["games_played"] += 1
        human_color = "W"  # human always plays white vs AI
        if winner == human_color:
            self.stats["games_won"] += 1
        else:
            self.stats["games_lost"] += 1
        score = self.gs.scores.get(human_color, 0) if self.gs else 0
        if score > self.stats["best_score"]:
            self.stats["best_score"] = score
        if self.gs:
            self.stats["total_captures"] += self.gs.capture_count
            if self.gs.game_mode == "enhanced":
                self.stats["enhanced_played"] += 1
            else:
                self.stats["classic_played"] += 1
            streak = max(self.gs.combo_streak.values()) if self.gs.combo_streak else 0
            if streak > self.stats["highest_streak"]:
                self.stats["highest_streak"] = streak
        self._save_stats()

    def _record_answer(self, correct: bool):
        if correct:
            self.stats["correct_answers"] += 1
        else:
            self.stats["wrong_answers"] += 1
        self._save_stats()

    # ── Board geometry ────────────────────────────────────────────
    def sq_rect(self, r, c):
        x = self.board_x + c * SQ
        y = self.board_y + r * SQ
        return pygame.Rect(x, y, SQ, SQ)

    def board_coord(self, px, py):
        c = (px - self.board_x) // SQ
        r = (py - self.board_y) // SQ
        if 0 <= r < 8 and 0 <= c < 8:
            return (r, c)
        return None

    # ── New game ──────────────────────────────────────────────────
    def start_game(self, math_type, difficulty):
        diff_map = {"Easy": 1, "Average": 2, "Hard": 3}
        ops_map  = {
            "Integers":  ["add", "sub", "mul"],
            "Fractions": ["add", "sub"],
            "Algebra":   ["add", "sub", "mul"],
        }
        self.gs = GameState(
            mode=self.opponent_mode,
            ai_difficulty=diff_map.get(difficulty, 2),
            math_ops=ops_map.get(math_type, ["add", "sub"]),
            timed_mode=False,
            time_limit=25.0,
            game_mode=self.game_mode,
        )
        if self.gs.mode == "ai" and getattr(self.gs, "ai", None) is None:
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
        self.selected = None
        self.awaiting_question = None
        self.pending_move = None
        self.answer_text = ""
        self.skip_next_question = False
        self.set_message(f"{self.game_mode.upper()} — {math_type} | {difficulty}", TEXT_DIM)

    # ── Check winner ─────────────────────────────────────────────
    def check_game_over(self):
        if not self.gs:
            return
        try:
            winner = self.gs.check_winner()
        except Exception:
            winner = None
        if winner:
            self.game_over = True
            self.winner = winner
            self.winner_name = "White" if winner == "W" else "Black"
            ws = self.gs.scores.get("W", 0)
            bs = self.gs.scores.get("B", 0)
            self.winner_scores = f"White  {ws} pts    Black  {bs} pts"
            self.set_message(f"🏆 {self.winner_name} wins!", GOLD_MSG, 9999)
            self._record_game_end(winner)

    # ════════════════════════════════════════════════════════════════
    # DRAWING
    # ════════════════════════════════════════════════════════════════

    # ── Background ───────────────────────────────────────────────
    def draw_bg(self):
        self.screen.fill(BG)
        w, h = self.screen.get_size()
        # Subtle dot grid
        for gx in range(0, w, 40):
            for gy in range(0, h, 40):
                pygame.draw.circle(self.screen, (50, 48, 45), (gx, gy), 1)

    # ── Menu ─────────────────────────────────────────────────────
    def draw_menu(self):
        self.draw_bg()
        w, h = self.screen.get_size()
        cx = w // 2

        # Logo area
        pygame.draw.rect(self.screen, BG2, (cx - 260, 60, 520, 120), border_radius=16)
        pygame.draw.rect(self.screen, BTN_GREEN, (cx - 260, 60, 520, 120), 2, border_radius=16)
        txt(self.screen, "♟  MATH CHECKERS  ♟", FX, BTN_GREEN, cx, 85, center=True)
        txt(self.screen, "Master math. Dominate the board.", FS, TEXT_DIM, cx, 145, center=True)

        # Buttons
        bw, bh, gap = 320, 58, 16
        labels = [("▶  Play", BTN_GREEN, TEXT_DARK), ("⚙  Settings", BTN_DARK, TEXT_W), ("✕  Exit", BTN_DARK, TEXT_DIM)]
        sy = 210
        self._btn_rects["menu"] = []
        for i, (label, bg, tc) in enumerate(labels):
            r = pygame.Rect(cx - bw//2, sy + i*(bh+gap), bw, bh)
            is_hover = r.collidepoint(self.hover_pos) if self.hover_pos else False
            c = BTN_GREEN_H if bg == BTN_GREEN and is_hover else (BTN_DARK_H if bg == BTN_DARK and is_hover else bg)
            btn(self.screen, label, FL, r, c, tc, r=10)
            self._btn_rects["menu"].append((label.split("  ")[1].strip(), r))

        # Footer
        txt(self.screen, "v2.0  •  Enhanced Edition", FT, TEXT_DIM, cx, h-36, center=True)

    # ── Mode select ──────────────────────────────────────────────
    def draw_mode_select(self):
        self.draw_bg()
        w, h = self.screen.get_size()
        cx = w // 2

        txt(self.screen, "SELECT GAME MODE", FL, ACCENT, cx, 55, center=True)

        cards = [
            ("classic",
             "CLASSIC MODE",
             BTN_GREEN,
             ["Standard math checkers rules",
              "Answer math questions to capture",
              "First to eliminate all pieces wins"]),
            ("enhanced",
             "ENHANCED MODE",
             BTN_GOLD,
             ["⚡ Wild pieces — auto-capture!",
              "💎 Power pieces — double score!",
              "🃏 Ability cards: Skip, Double, Freeze AI",
              "🔗 Chain captures for combos"]),
        ]

        self._btn_rects["mode"] = []
        for i, (key, title, color, features) in enumerate(cards):
            cx2 = w // 4 + i * (w // 2)
            cw, ch = 340, 320
            cr = pygame.Rect(cx2 - cw//2, 110, cw, ch)
            is_sel = self.game_mode == key
            rrect(self.screen, PANEL_BG, cr, r=16, border=3, bc=color if is_sel else PANEL_BDR)

            txt(self.screen, title, FL, color, cx2, 128, center=True)
            pygame.draw.line(self.screen, color if is_sel else PANEL_BDR,
                             (cr.x+20, 175), (cr.x+cw-20, 175), 1)
            for j, feat in enumerate(features):
                txt(self.screen, feat, FS, TEXT_W if is_sel else TEXT_DIM, cx2, 192 + j*36, center=True)

            rb = pygame.Rect(cx2 - 120, cr.bottom - 60, 240, 44)
            btn(self.screen, "✓ Selected" if is_sel else "Select", FM, rb,
                color if is_sel else BTN_DARK, TEXT_DARK if is_sel else TEXT_W, r=10)
            self._btn_rects["mode"].append((key, rb))

        # ── Opponent selector ────────────────────────────────────
        oy = 460
        txt(self.screen, "OPPONENT", FL, TEXT_W, cx, oy, center=True)

        opp_items = [
            ("ai", "🤖  vs AI",     "Play against the computer"),
            ("2p", "👥  vs Friend", "Local 2-player mode"),
        ]
        obw, obh = 320, 66
        total_opp_w = len(opp_items) * obw + (len(opp_items)-1) * 20
        ox = cx - total_opp_w // 2
        for key, label, desc in opp_items:
            is_sel = self.opponent_mode == key
            color = BTN_GREEN if key == "ai" else BTN_BLUE
            or2 = pygame.Rect(ox, oy + 40, obw, obh)
            rrect(self.screen, PANEL_BG, or2, r=12,
                  border=3, bc=color if is_sel else PANEL_BDR)
            txt(self.screen, label, FL, color if is_sel else TEXT_DIM,
                or2.x + or2.w//2, or2.y + 8, center=True)
            txt(self.screen, desc, FT, TEXT_DIM if not is_sel else TEXT_W,
                or2.x + or2.w//2, or2.y + 42, center=True)
            self._btn_rects["mode"].append((f"opp_{key}", or2))
            ox += obw + 20

        # Back + continue
        br = pygame.Rect(40, h-70, 130, 44)
        btn(self.screen, "← Back", FM, br, BTN_DARK, TEXT_W, r=8)
        self._btn_rects["mode"].append(("back", br))

        cr2 = pygame.Rect(w-220, h-70, 180, 44)
        btn(self.screen, "Continue →", FM, cr2, BTN_GREEN, TEXT_DARK, r=8)
        self._btn_rects["mode"].append(("continue", cr2))

    # ── Play select ──────────────────────────────────────────────
    def draw_play_select(self):
        self.draw_bg()
        w, h = self.screen.get_size()
        cx = w // 2
        txt(self.screen, "SELECT MATH TYPE", FL, ACCENT, cx, 60, center=True)

        items = [
            ("Integers",  "Whole number operations",     BTN_GREEN),
            ("Fractions", "Fractional arithmetic",        BTN_BLUE),
            ("Algebra",   "Variables & expressions",      BTN_GOLD),
        ]
        self._btn_rects["play"] = []
        bw, bh, gap = 340, 80, 18
        sy = 130
        for i, (label, desc, color) in enumerate(items):
            r = pygame.Rect(cx - bw//2, sy + i*(bh+gap), bw, bh)
            rrect(self.screen, PANEL_BG, r, r=12, border=2, bc=color)
            txt(self.screen, label, FL, color, cx, r.y+10, center=True)
            txt(self.screen, desc, FS, TEXT_DIM, cx, r.y+44, center=True)
            self._btn_rects["play"].append((label, r))

        br = pygame.Rect(40, h-70, 130, 44)
        btn(self.screen, "← Back", FM, br, BTN_DARK, TEXT_W, r=8)
        self._btn_rects["play"].append(("Back", br))

    # ── Difficulty select ────────────────────────────────────────
    def draw_difficulty_select(self):
        self.draw_bg()
        w, h = self.screen.get_size()
        cx = w // 2
        mt = self.selected_math_type or "Math"
        txt(self.screen, f"{mt}  ·  CHOOSE DIFFICULTY", FL, ACCENT, cx, 60, center=True)

        items = [
            ("Easy",    "Slower questions, simple numbers",  BTN_GREEN,  1),
            ("Average", "Balanced challenge",                BTN_GOLD,   2),
            ("Hard",    "Fast, complex, unforgiving",        BTN_RED,    3),
        ]
        self._btn_rects["diff"] = []
        bw, bh, gap = 380, 80, 18
        sy = 140
        for label, desc, color, stars in items:
            r = pygame.Rect(cx - bw//2, sy, bw, bh)
            rrect(self.screen, PANEL_BG, r, r=12, border=2, bc=color)
            txt(self.screen, label, FL, color, cx, r.y+10, center=True)
            txt(self.screen, desc, FS, TEXT_DIM, cx, r.y+44, center=True)
            self._btn_rects["diff"].append((label, r))
            sy += bh + gap

        br = pygame.Rect(40, h-70, 130, 44)
        btn(self.screen, "← Back", FM, br, BTN_DARK, TEXT_W, r=8)
        self._btn_rects["diff"].append(("Back", br))

    # ── Settings (tabbed) ────────────────────────────────────────
    def draw_settings(self):
        self.draw_bg()
        w, h = self.screen.get_size()
        cx = w // 2

        txt(self.screen, "SETTINGS", FX, ACCENT, cx, 28, center=True)

        # ── Tab bar ───────────────────────────────────────────────
        tabs = [
            ("appearance", "🎨  Appearance"),
            ("audio",      "🔊  Audio"),
            ("stats",      "📊  Stats"),
            ("credits",    "ℹ️  Credits"),
            ("howto",      "📖  How to Play"),
        ]
        tbw = (w - 80) // len(tabs)
        self._btn_rects["settings_tabs"] = []
        for i, (key, label) in enumerate(tabs):
            r = pygame.Rect(40 + i * tbw, 90, tbw - 6, 44)
            is_active = self.settings_tab == key
            rrect(self.screen, BTN_GREEN if is_active else BTN_DARK, r, r=8,
                  border=2, bc=BTN_GREEN if is_active else PANEL_BDR)
            txt(self.screen, label, FS, TEXT_DARK if is_active else TEXT_DIM, r.x + r.w//2, r.y + 12, center=True)
            self._btn_rects["settings_tabs"].append((key, r))

        # ── Content area ──────────────────────────────────────────
        content = pygame.Rect(40, 148, w - 80, h - 230)
        rrect(self.screen, PANEL_BG, content, r=14, border=1, bc=PANEL_BDR)

        if   self.settings_tab == "appearance": self._draw_tab_appearance(content)
        elif self.settings_tab == "audio":      self._draw_tab_audio(content)
        elif self.settings_tab == "stats":      self._draw_tab_stats(content)
        elif self.settings_tab == "credits":    self._draw_tab_credits(content)
        elif self.settings_tab == "howto":      self._draw_tab_howto(content)

        # Back button
        br = pygame.Rect(40, h - 68, 140, 46)
        btn(self.screen, "← Back", FM, br, BTN_DARK, TEXT_W, r=8)
        self._btn_rects["settings_back"] = br

    # ── Appearance tab ───────────────────────────────────────────
    def _draw_tab_appearance(self, area):
        cx = area.x + area.w // 2
        txt(self.screen, "Game Theme", FL, TEXT_W, cx, area.y + 18, center=True)
        txt(self.screen, "Changes the entire game  —  board, panels, buttons and all colors",
            FS, TEXT_DIM, cx, area.y + 52, center=True)

        themes_order = ["dark", "ocean", "royal", "sunset"]
        tw, th = 240, 172
        gap = 18
        total = len(themes_order) * tw + (len(themes_order) - 1) * gap
        tx = cx - total // 2
        self._btn_rects["themes"] = []

        for key in themes_order:
            t = GAME_THEMES[key]
            r = pygame.Rect(tx, area.y + 84, tw, th)
            is_sel = self.game_theme == key
            card_cx = r.x + r.w // 2

            rrect(self.screen, t["PANEL_BG"], r, r=12,
                  border=3, bc=t["BTN_GREEN"] if is_sel else PANEL_BDR)

            # Mini 4x4 board preview
            sq = 16
            board_w = 4 * sq
            bx = card_cx - board_w // 2
            by = r.y + 12
            for pr2 in range(4):
                for pc2 in range(4):
                    c2 = t["BOARD_DARK"] if (pr2 + pc2) % 2 else t["BOARD_LIGHT"]
                    pygame.draw.rect(self.screen, c2,
                                     (bx + pc2 * sq, by + pr2 * sq, sq - 1, sq - 1))

            # Accent color strip
            swatch_y = by + 4 * sq + 10
            pygame.draw.rect(self.screen, t["BTN_GREEN"],
                             pygame.Rect(r.x + 16, swatch_y, tw - 32, 8), border_radius=4)

            # Theme name
            ns = FM.render(t["name"], True, t["ACCENT"])
            self.screen.blit(ns, (card_cx - ns.get_width() // 2, swatch_y + 16))

            # Accent label
            ac = FT.render(t["accent_name"] + " accent", True, TEXT_DIM)
            self.screen.blit(ac, (card_cx - ac.get_width() // 2, swatch_y + 40))

            # Active badge
            if is_sel:
                badge_r = pygame.Rect(card_cx - 38, r.bottom - 30, 76, 22)
                rrect(self.screen, t["BTN_GREEN"], badge_r, r=6)
                bs = FT.render("Active", True, TEXT_DARK)
                self.screen.blit(bs, (card_cx - bs.get_width() // 2, r.bottom - 26))

            self._btn_rects["themes"].append((key, r))
            tx += tw + gap

    # ── Audio tab ────────────────────────────────────────────────
    def _draw_tab_audio(self, area):
        cx = area.x + area.w // 2
        txt(self.screen, "Sound & Music", FL, TEXT_W, cx, area.y + 20, center=True)
        self._btn_rects["audio_btns"] = []
        bw, bh, gap = 420, 58, 18
        y = area.y + 74

        # Music toggle
        mc = BTN_GREEN if self.music_on else BTN_DARK
        mr = pygame.Rect(cx - bw//2, y, bw, bh)
        rrect(self.screen, mc, mr, r=10, border=2, bc=BTN_GREEN if self.music_on else PANEL_BDR)
        txt(self.screen, f"🎵  Background Music   {'ON ✓' if self.music_on else 'OFF'}", FM, TEXT_W, cx, y+16, center=True)
        self._btn_rects["audio_btns"].append(("music", mr))
        y += bh + gap

        # SFX toggle
        sc = BTN_GREEN if self.sfx_on else BTN_DARK
        sr = pygame.Rect(cx - bw//2, y, bw, bh)
        rrect(self.screen, sc, sr, r=10, border=2, bc=BTN_GREEN if self.sfx_on else PANEL_BDR)
        txt(self.screen, f"🔊  Sound Effects       {'ON ✓' if self.sfx_on else 'OFF'}", FM, TEXT_W, cx, y+16, center=True)
        self._btn_rects["audio_btns"].append(("sfx", sr))
        y += bh + gap + 10

        # Volume levels
        txt(self.screen, "Music Volume", FM, TEXT_DIM, cx, y, center=True)
        y += 34
        vols = [("Low", 0.1), ("Medium", 0.3), ("High", 0.6)]
        vbw = 120
        vx = cx - (len(vols)*vbw + (len(vols)-1)*14)//2
        for label, val in vols:
            vr = pygame.Rect(vx, y, vbw, 46)
            is_sel = abs(self.music_vol - val) < 0.05
            rrect(self.screen, BTN_GREEN if is_sel else BTN_DARK, vr, r=8,
                  border=2, bc=BTN_GREEN if is_sel else PANEL_BDR)
            txt(self.screen, ("✓ " if is_sel else "") + label, FM,
                TEXT_DARK if is_sel else TEXT_W, vx + vbw//2, y+12, center=True)
            self._btn_rects["audio_btns"].append((f"vol_{label.lower()}", vr))
            vx += vbw + 14

    # ── Stats tab ─────────────────────────────────────────────────
    def _draw_tab_stats(self, area):
        cx = area.x + area.w // 2
        txt(self.screen, "Your Statistics", FL, TEXT_W, cx, area.y + 18, center=True)

        s = self.stats
        total_ans = s["correct_answers"] + s["wrong_answers"]
        acc = int(s["correct_answers"] / total_ans * 100) if total_ans > 0 else 0
        wr  = int(s["games_won"] / s["games_played"] * 100) if s["games_played"] > 0 else 0

        # (label, main_value, sub_value)
        rows = [
            ("Games Played",    str(s["games_played"]),       ""),
            ("Wins",            str(s["games_won"]),           f"{wr}% win rate"),
            ("Losses",          str(s["games_lost"]),          ""),
            ("Best Score",      str(s["best_score"]),          "pts"),
            ("Correct Answers", str(s["correct_answers"]),     f"{acc}% accuracy"),
            ("Total Captures",  str(s["total_captures"]),      ""),
            ("Highest Combo",   str(s["highest_streak"]),      "streak"),
            ("Classic Games",   str(s["classic_played"]),      ""),
            ("Enhanced Games",  str(s["enhanced_played"]),     ""),
        ]

        rw, rh, gap = area.w - 80, 40, 5
        rx = area.x + 40
        y  = area.y + 66
        for i, (label, main_val, sub_val) in enumerate(rows):
            bg = (52, 50, 47) if i % 2 == 0 else PANEL_BG
            row_rect = pygame.Rect(rx, y, rw, rh)
            rrect(self.screen, bg, row_rect, r=6)

            # Label on left
            txt(self.screen, label, FM, TEXT_DIM, rx + 16, y + 10)

            # Main value right-aligned
            val_surf = FL.render(main_val, True, TEXT_W)
            vx = rx + rw - 14 - val_surf.get_width()
            if sub_val:
                # Push main value left to make room for sub label
                sub_surf = FT.render(sub_val, True, TEXT_DIM)
                vx = rx + rw - 14 - val_surf.get_width() - sub_surf.get_width() - 10
                self.screen.blit(sub_surf, (rx + rw - 14 - sub_surf.get_width(), y + 13))
            self.screen.blit(val_surf, (vx, y + 5))
            y += rh + gap

        # Reset stats button
        self._btn_rects["reset_stats"] = pygame.Rect(cx - 110, area.bottom - 54, 220, 40)
        btn(self.screen, "Reset All Stats", FS, self._btn_rects["reset_stats"], BTN_RED, TEXT_W, r=8)

    # ── Credits tab ──────────────────────────────────────────────
    def _draw_tab_credits(self, area):
        cx = area.x + area.w // 2
        y  = area.y + 24

        # Game logo area
        rrect(self.screen, (25, 24, 22), pygame.Rect(cx-200, y, 400, 80), r=12,
              border=2, bc=BTN_GREEN)
        txt(self.screen, "♟  MATH CHECKERS", FL, BTN_GREEN, cx, y+10, center=True)
        txt(self.screen, "Version 2.0  —  Enhanced Edition", FS, TEXT_DIM, cx, y+48, center=True)
        y += 104

        items = [
            ("Developer",    "Rhince Jave"),
            ("Built With",   "Python 3  &  Pygame 2"),
            ("Inspired By",  "Damath  —  Filipino Math Board Game"),
            ("AI Engine",    "Minimax Heuristic Search"),
            ("Audio",        "Custom SFX & Background Music"),
            ("Source Code",  "github.com/rhincejave-bit/math-checkers"),
        ]

        cw, ch = area.w - 80, 50
        label_w = cw // 3
        for label, value in items:
            row_r = pygame.Rect(area.x+40, y, cw, ch)
            rrect(self.screen, (42, 40, 37), row_r, r=8)
            # Colored left accent bar
            pygame.draw.rect(self.screen, BTN_GREEN,
                             pygame.Rect(area.x+40, y, 4, ch), border_radius=4)
            txt(self.screen, label, FM, TEXT_DIM, area.x + 56, y + 14)
            txt(self.screen, value,  FM, ACCENT,  area.x + 56 + label_w, y + 14)
            y += ch + 8

        y += 12
        # Plain text footer — no emojis
        txt(self.screen, "Made with love  |  Philippines  |  2026", FS, TEXT_DIM, cx, y, center=True)

    # ── How to Play tab ──────────────────────────────────────────
    def _draw_tab_howto(self, area):
        cx = area.x + area.w // 2
        col_w = (area.w - 100) // 2

        # Classic column
        cl_x = area.x + 24
        txt(self.screen, "♟  CLASSIC MODE", FM, BTN_GREEN, cl_x + col_w//2, area.y+18, center=True)
        pygame.draw.line(self.screen, BTN_GREEN, (cl_x, area.y+46), (cl_x+col_w, area.y+46), 1)
        classic_tips = [
            "Move pieces diagonally on dark squares",
            "Capture by jumping over an opponent",
            "Answer the math question to capture",
            "Wrong answer? Your turn is forfeited",
            "Reach the far end to become a King",
            "Kings can move in any direction",
            "Game ends when a side has no pieces",
            "Player with the HIGHEST score wins",
        ]
        y = area.y + 58
        for tip in classic_tips:
            txt(self.screen, f"•  {tip}", FS, TEXT_DIM, cl_x + 8, y)
            y += 30

        # Enhanced column
        en_x = cl_x + col_w + 52
        txt(self.screen, "✨  ENHANCED MODE", FM, BTN_GOLD, en_x + col_w//2, area.y+18, center=True)
        pygame.draw.line(self.screen, BTN_GOLD, (en_x, area.y+46), (en_x+col_w, area.y+46), 1)
        enhanced_tips = [
            "All Classic rules apply",
            "Wild pieces  —  auto-capture (no question!)",
            "Power pieces  —  double your capture score",
            "Skip card  —  bypass a math question",
            "Double card  —  2x points next capture",
            "Freeze card  —  AI skips 3 turns",
            "Chain captures  —  combo after a capture!",
            "3+ combos in a row  =  bonus points",
        ]
        y = area.y + 58
        for tip in enhanced_tips:
            txt(self.screen, f"•  {tip}", FS, TEXT_DIM, en_x + 8, y)
            y += 30

        # Controls
        pygame.draw.line(self.screen, PANEL_BDR, (area.x+24, area.bottom-72), (area.right-24, area.bottom-72), 1)
        controls = [("U", "Undo"), ("S", "Save"), ("Esc", "Deselect / Close")]
        kx = cx - 240
        for key, action in controls:
            rrect(self.screen, BTN_DARK, pygame.Rect(kx, area.bottom-60, 50, 30), r=6)
            txt(self.screen, key, FS, ACCENT, kx+25, area.bottom-52, center=True)
            txt(self.screen, action, FS, TEXT_DIM, kx+58, area.bottom-52)
            kx += 160

    # ── Board ────────────────────────────────────────────────────
    def draw_board(self):
        theme_map = {
            "chess": (BOARD_DARK, BOARD_LIGHT),
            "wood":  ((160, 100, 50), (230, 195, 150)),
            "slate": ((70, 70, 90), (190, 190, 210)),
        }
        dark, light = theme_map.get(self.selected_theme, (BOARD_DARK, BOARD_LIGHT))

        # Board shadow
        shadow = pygame.Rect(self.board_x+6, self.board_y+6, 8*SQ, 8*SQ)
        pygame.draw.rect(self.screen, (20, 18, 16), shadow, border_radius=4)

        # Coordinate labels
        for i in range(8):
            c_lbl = chr(ord('a') + i)
            r_lbl = str(8 - i)
            txt(self.screen, c_lbl, FT, TEXT_DIM, self.board_x + i*SQ + SQ//2 - 4, self.board_y - 20)
            txt(self.screen, r_lbl, FT, TEXT_DIM, self.board_x - 18, self.board_y + i*SQ + SQ//2 - 8)

        for r in range(8):
            for c in range(8):
                sq = self.sq_rect(r, c)
                color = dark if (r + c) % 2 else light
                pygame.draw.rect(self.screen, color, sq)

                # Operator label
                op = self.gs.board.operator_at((r, c))
                if op:
                    sym = {"*": "×", "/": "÷"}.get(op, op)
                    op_color = (50, 80, 40) if (r+c)%2 else (180, 170, 140)
                    txt(self.screen, sym, FM, op_color, sq.x + 4, sq.y + 4)

                # Piece
                piece = self.gs.board.get((r, c))
                if piece:
                    self._draw_piece(piece, sq, (r, c))

        # Selected highlight
        if self.selected:
            sr, sc = self.selected
            sq = self.sq_rect(sr, sc)
            over = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
            over.fill((246, 246, 105, 100))
            self.screen.blit(over, sq.topleft)
            pygame.draw.rect(self.screen, SELECT_CLR, sq, 3)

            # Legal move dots
            for (mr, mc) in self.gs.board.legal_moves_from(self.selected):
                msq = self.sq_rect(mr, mc)
                cx2 = msq.x + SQ//2
                cy2 = msq.y + SQ//2
                dot_color = (0,0,0,80) if (mr+mc)%2 == 0 else (0,0,0,60)
                dot_surf = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                pygame.draw.circle(dot_surf, (0, 0, 0, 100), (SQ//2, SQ//2), 12)
                self.screen.blit(dot_surf, msq.topleft)

        # Chain capture highlight
        if self.gs and self.gs.game_mode == "enhanced" and self.gs.chain_capture_pos:
            cr2, cc2 = self.gs.chain_capture_pos
            csq = self.sq_rect(cr2, cc2)
            over2 = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
            over2.fill((120, 220, 120, 120))
            self.screen.blit(over2, csq.topleft)
            pygame.draw.rect(self.screen, CHAIN_CLR, csq, 4)

    def _draw_piece(self, piece, sq, coord):
        cx2 = sq.x + SQ//2
        cy2 = sq.y + SQ//2
        radius = SQ//2 - 7

        # Special piece glow
        stype = getattr(piece, "special", None)
        if stype == "wild":
            for ring in range(3, 0, -1):
                alpha = 60 + ring * 30
                gsurf = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                pygame.draw.circle(gsurf, (*BTN_GOLD, alpha), (SQ//2, SQ//2), radius + ring*2)
                self.screen.blit(gsurf, sq.topleft)
        elif stype == "power":
            for ring in range(3, 0, -1):
                alpha = 60 + ring * 30
                gsurf = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                pygame.draw.circle(gsurf, (*BTN_BLUE, alpha), (SQ//2, SQ//2), radius + ring*2)
                self.screen.blit(gsurf, sq.topleft)

        # Piece body
        if piece.color == "W":
            fill   = (240, 235, 210)
            shadow = (180, 170, 145)
            text_c = (30, 25, 20)
            border = (200, 190, 165)
        else:
            fill   = (55, 42, 30)
            shadow = (30, 22, 14)
            text_c = (240, 230, 210)
            border = (90, 72, 55)

        pygame.draw.circle(self.screen, shadow, (cx2+2, cy2+2), radius)
        pygame.draw.circle(self.screen, fill, (cx2, cy2), radius)
        pygame.draw.circle(self.screen, border, (cx2, cy2), radius, 2)

        # Value
        val_surf = FM.render(str(piece.value), True, text_c)
        self.screen.blit(val_surf, (cx2 - val_surf.get_width()//2, cy2 - val_surf.get_height()//2))

        # King crown
        if piece.king:
            crown = _f(11, bold=True).render("♛", True, BTN_GOLD)
            self.screen.blit(crown, (cx2 - crown.get_width()//2, sq.y + 3))

        # Special badge
        if stype == "wild":
            badge = FT.render("⚡", True, BTN_GOLD)
            self.screen.blit(badge, (sq.right - 18, sq.y + 2))
        elif stype == "power":
            badge = FT.render("💎", True, BTN_BLUE)
            self.screen.blit(badge, (sq.right - 18, sq.y + 2))

    # ── Side panel ───────────────────────────────────────────────
    def draw_panel(self):
        w, h = self.screen.get_size()
        px = self.board_x + 8*SQ + 30
        pw = w - px - 20
        ph = 8*SQ
        pr = pygame.Rect(px, self.board_y, pw, ph)
        rrect(self.screen, PANEL_BG, pr, r=14, border=1, bc=PANEL_BDR)

        y = self.board_y + 18
        cx2 = px + pw//2

        # Turn indicator
        turn_color = (240, 235, 210) if self.gs.turn == "W" else (55, 42, 30)
        turn_border = (200, 190, 165) if self.gs.turn == "W" else (90, 72, 55)
        pygame.draw.circle(self.screen, turn_border, (cx2, y+14), 18)
        pygame.draw.circle(self.screen, turn_color, (cx2, y+14), 16)
        turn_name = "White" if self.gs.turn == "W" else "Black"
        txt(self.screen, f"{turn_name}'s Turn", FM, TEXT_W, cx2, y+38, center=True)
        y += 72

        # Mode badge
        mc = BTN_GOLD if self.gs.game_mode == "enhanced" else TEXT_DIM
        txt(self.screen, self.gs.game_mode.upper(), FT, mc, cx2, y, center=True)
        y += 22

        # Divider
        pygame.draw.line(self.screen, PANEL_BDR, (px+16, y), (px+pw-16, y))
        y += 12

        # Scores
        ws = self.gs.scores.get("W", 0)
        bs = self.gs.scores.get("B", 0)
        txt(self.screen, "SCORES", FT, TEXT_DIM, cx2, y, center=True)
        y += 20
        rrect(self.screen, BTN_DARK, pygame.Rect(px+12, y, pw-24, 44), r=8)
        txt(self.screen, f"⬜ {ws}", FM, (240, 235, 210), px+22, y+12)
        txt(self.screen, f"⬛ {bs}", FM, (120, 100, 80), px+pw//2, y+12)
        y += 54

        # Combo streaks (Enhanced)
        if self.gs.game_mode == "enhanced":
            streak_w = self.gs.combo_streak.get("W", 0)
            streak_b = self.gs.combo_streak.get("B", 0)
            if streak_w > 1 or streak_b > 1:
                txt(self.screen, f"🔥 Combo  W:{streak_w}  B:{streak_b}", FS, GOLD_MSG, cx2, y, center=True)
                y += 28

        # AI frozen indicator
        if self.gs.game_mode == "enhanced" and self.gs.ai_frozen_turns > 0:
            txt(self.screen, f"❄️ AI frozen ({self.gs.ai_frozen_turns})", FS, (120, 200, 240), cx2, y, center=True)
            y += 26

        pygame.draw.line(self.screen, PANEL_BDR, (px+16, y), (px+pw-16, y))
        y += 12

        # Buttons row 1: New | Undo
        bw2 = (pw-36)//2
        self._btn_rects["new"]  = pygame.Rect(px+12, y, bw2, 38)
        self._btn_rects["undo"] = pygame.Rect(px+24+bw2, y, bw2, 38)
        btn(self.screen, "New",  FS, self._btn_rects["new"],  BTN_DARK, TEXT_W, r=7)
        btn(self.screen, "Undo", FS, self._btn_rects["undo"], BTN_DARK, TEXT_W, r=7)
        y += 46

        # Buttons row 2: Save | Load
        self._btn_rects["save"] = pygame.Rect(px+12, y, bw2, 38)
        self._btn_rects["load"] = pygame.Rect(px+24+bw2, y, bw2, 38)
        btn(self.screen, "Save", FS, self._btn_rects["save"], BTN_DARK, TEXT_W, r=7)
        btn(self.screen, "Load", FS, self._btn_rects["load"], BTN_DARK, TEXT_W, r=7)
        y += 46

        # Settings button (full width)
        self._btn_rects["settings_btn"] = pygame.Rect(px+12, y, pw-24, 38)
        btn(self.screen, "⚙  Settings", FS, self._btn_rects["settings_btn"], BTN_DARK, ACCENT, r=7)
        y += 46

        # ── Ability Cards (Enhanced only) ─────────────────────────
        if self.gs.game_mode == "enhanced":
            pygame.draw.line(self.screen, PANEL_BDR, (px+16, y), (px+pw-16, y))
            y += 10
            txt(self.screen, "ABILITY CARDS", FT, TEXT_DIM, cx2, y, center=True)
            y += 20

            player = self.gs.turn
            cards_def = [
                ("skip",   "⚡ Skip Q",   BTN_GOLD,  "Skip question"),
                ("double", "💎 Double",   BTN_BLUE,  "2× next score"),
                ("freeze", "❄️ Freeze AI", (100,180,220), "Freeze AI 3 turns"),
            ]
            self.ability_rects = {}
            cbw = (pw - 36) // 3
            for i, (key, label, color, tip) in enumerate(cards_def):
                count = self.gs.ability_cards.get(player, {}).get(key, 0)
                cx3 = px + 12 + i * (cbw + 6)
                cr3 = pygame.Rect(cx3, y, cbw, 52)
                active = count > 0 and self.gs.turn == "W"
                rrect(self.screen, color if active else BTN_DARK, cr3, r=8,
                      border=2, bc=color if active else PANEL_BDR)
                txt(self.screen, label, FT, TEXT_W if active else TEXT_DIM, cr3.x + cr3.w//2, cr3.y + 8, center=True)
                txt(self.screen, f"×{count}", FM, TEXT_W if active else TEXT_DIM, cr3.x + cr3.w//2, cr3.y+28, center=True)
                self.ability_rects[key] = cr3
            y += 62
            txt(self.screen, "Cards apply to YOUR next capture", FT, TEXT_DIM, cx2, y, center=True)

        # Message bar
        if self.message and self.msg_timer > 0:
            pygame.draw.line(self.screen, PANEL_BDR, (px+16, pr.bottom-52), (px+pw-16, pr.bottom-52))
            txt(self.screen, self.message, FS, self.msg_color, cx2, pr.bottom-40, center=True)

    # ── Game title bar ───────────────────────────────────────────
    def draw_title_bar(self):
        txt(self.screen, "MATH CHECKERS", FL, BTN_GREEN, self.board_x, self.board_y - 46)
        mode_str = "✦ ENHANCED" if self.gs.game_mode == "enhanced" else "CLASSIC"
        mc = BTN_GOLD if self.gs.game_mode == "enhanced" else TEXT_DIM
        txt(self.screen, mode_str, FS, mc, self.board_x + 8*SQ - 10, self.board_y - 40,
            center=False)

    def draw_settings_overlay(self):
        w, h = self.screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 440, 330
        x = (w - bw) // 2
        y = (h - bh) // 2
        rrect(self.screen, (30, 28, 26), pygame.Rect(x, y, bw, bh), r=16,
              border=2, bc=ACCENT)

        txt(self.screen, "SETTINGS", FL, ACCENT, x + bw//2, y + 16, center=True)
        pygame.draw.line(self.screen, PANEL_BDR, (x+30, y+52), (x+bw-30, y+52), 1)

        # Music toggle
        mc = BTN_GREEN if self.music_on else BTN_DARK
        mr = pygame.Rect(x+40, y+66, bw-80, 50)
        rrect(self.screen, mc, mr, r=10, border=2, bc=BTN_GREEN if self.music_on else PANEL_BDR)
        txt(self.screen, f"Music     {'ON  ✓' if self.music_on else 'OFF'}", FM, TEXT_W,
            x + bw//2, y + 84, center=True)
        self._btn_rects["ov_music"] = mr

        # SFX toggle
        sc2 = BTN_GREEN if self.sfx_on else BTN_DARK
        sr = pygame.Rect(x+40, y+126, bw-80, 50)
        rrect(self.screen, sc2, sr, r=10, border=2, bc=BTN_GREEN if self.sfx_on else PANEL_BDR)
        txt(self.screen, f"Sound FX  {'ON  ✓' if self.sfx_on else 'OFF'}", FM, TEXT_W,
            x + bw//2, y + 144, center=True)
        self._btn_rects["ov_sfx"] = sr

        pygame.draw.line(self.screen, PANEL_BDR, (x+30, y+190), (x+bw-30, y+190), 1)

        # Back to Menu button (full width)
        self._btn_rects["ov_menu"] = pygame.Rect(x+40, y+200, bw-80, 44)
        btn(self.screen, "Back to Main Menu", FM,
            self._btn_rects["ov_menu"], BTN_BLUE, TEXT_W, r=10)

        # Quit + Resume row
        bw2 = (bw - 100) // 2
        self._btn_rects["ov_quit"]  = pygame.Rect(x+40,           y+258, bw2, 48)
        self._btn_rects["ov_close"] = pygame.Rect(x+60+bw2,       y+258, bw2, 48)
        btn(self.screen, "Quit Game", FM, self._btn_rects["ov_quit"],  BTN_RED,  TEXT_W, r=10)
        btn(self.screen, "Resume",    FM, self._btn_rects["ov_close"], BTN_DARK, TEXT_W, r=10)

    # ── Math question modal ──────────────────────────────────────
    def draw_question_modal(self):
        w, h = self.screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 500, 220
        x = (w - bw)//2
        y = (h - bh)//2

        rrect(self.screen, (30, 28, 26), pygame.Rect(x, y, bw, bh), r=16,
              border=2, bc=BTN_GREEN)

        txt(self.screen, "MATH CHALLENGE", FL, BTN_GREEN, x + bw//2, y+16, center=True)
        pygame.draw.line(self.screen, BTN_GREEN, (x+30, y+52), (x+bw-30, y+52), 1)

        q = self.awaiting_question
        expr = q.text if q else "?"
        txt(self.screen, expr, FX, ACCENT, x + bw//2, y+64, center=True)

        # Answer box
        ab = pygame.Rect(x+60, y+130, bw-120, 46)
        rrect(self.screen, (55, 52, 48), ab, r=8, border=2,
              bc=BTN_GREEN if self.answer_text else PANEL_BDR)
        if self.answer_text:
            txt(self.screen, self.answer_text, FL, TEXT_W, ab.x+14, ab.y+10)
        else:
            txt(self.screen, "Type your answer...", FM, TEXT_DIM, ab.x+14, ab.y+12)

        txt(self.screen, "Enter = confirm    Esc = cancel", FT, TEXT_DIM,
            x + bw//2, y+188, center=True)

    # ── Winner popup ─────────────────────────────────────────────
    def draw_winner_popup(self):
        w, h = self.screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 480, 280
        x = (w-bw)//2
        y = (h-bh)//2

        rrect(self.screen, (30, 28, 26), pygame.Rect(x, y, bw, bh), r=18,
              border=3, bc=BTN_GOLD)

        txt(self.screen, "🏆", FXX, BTN_GOLD, x+bw//2, y+12, center=True)
        txt(self.screen, f"{self.winner_name} Wins!", FX, BTN_GOLD, x+bw//2, y+90, center=True)

        pygame.draw.line(self.screen, PANEL_BDR, (x+40, y+148), (x+bw-40, y+148), 1)
        txt(self.screen, self.winner_scores, FM, TEXT_DIM, x+bw//2, y+160, center=True)

        bw2 = 180
        self.restart_rect = pygame.Rect(x + bw//2 - bw2 - 10, y+200, bw2, 48)
        self.menu_btn_rect = pygame.Rect(x + bw//2 + 10, y+200, bw2, 48)
        btn(self.screen, "▶ Play Again", FM, self.restart_rect, BTN_GREEN, TEXT_DARK, r=10)
        btn(self.screen, "⌂ Menu",       FM, self.menu_btn_rect, BTN_DARK,  TEXT_W,    r=10)

    # ════════════════════════════════════════════════════════════════
    # INPUT HANDLERS
    # ════════════════════════════════════════════════════════════════

    def handle_menu_click(self, pos):
        for label, r in self._btn_rects.get("menu", []):
            if r.collidepoint(pos):
                self._play(self.sfx_btn)
                if label == "Play":
                    self.state = "mode_select"
                elif label == "Settings":
                    self.state = "settings"
                elif label == "Exit":
                    pygame.quit(); sys.exit()

    def handle_mode_click(self, pos):
        for key, r in self._btn_rects.get("mode", []):
            if r.collidepoint(pos):
                self._play(self.sfx_btn)
                if key in ("classic", "enhanced"):
                    self.game_mode = key
                elif key == "opp_ai":
                    self.opponent_mode = "ai"
                elif key == "opp_2p":
                    self.opponent_mode = "2p"
                elif key == "back":
                    self.state = "menu"
                elif key == "continue":
                    self.state = "play_select"

    def handle_play_click(self, pos):
        for label, r in self._btn_rects.get("play", []):
            if r.collidepoint(pos):
                self._play(self.sfx_btn)
                if label == "Back":
                    self.state = "mode_select"
                else:
                    self.selected_math_type = label
                    self.state = "difficulty_select"

    def handle_diff_click(self, pos):
        for label, r in self._btn_rects.get("diff", []):
            if r.collidepoint(pos):
                self._play(self.sfx_btn)
                if label == "Back":
                    self.state = "play_select"
                else:
                    self.start_game(self.selected_math_type or "Integers", label)

    def handle_settings_click(self, pos):
        self._play(self.sfx_btn)

        # Back button
        if self._btn_rects.get("settings_back") and self._btn_rects["settings_back"].collidepoint(pos):
            self.state = "menu"
            return

        # Tab switching
        for key, r in self._btn_rects.get("settings_tabs", []):
            if r.collidepoint(pos):
                self.settings_tab = key
                return

        # Reset stats
        if self.settings_tab == "stats":
            rb = self._btn_rects.get("reset_stats")
            if rb and rb.collidepoint(pos):
                for k in self.stats:
                    self.stats[k] = 0
                self._save_stats()
            return

        # Theme buttons
        if self.settings_tab == "appearance":
            for key, r in self._btn_rects.get("themes", []):
                if r.collidepoint(pos):
                    self.apply_game_theme(key)
            return

        # Audio buttons
        if self.settings_tab == "audio":
            for key, r in self._btn_rects.get("audio_btns", []):
                if r.collidepoint(pos):
                    if key == "music":
                        self.music_on = not self.music_on
                        try:
                            if self.music_on:
                                pygame.mixer.music.set_volume(self.music_vol)
                                pygame.mixer.music.unpause()
                            else:
                                pygame.mixer.music.pause()
                        except Exception:
                            pass
                    elif key == "sfx":
                        self.sfx_on = not self.sfx_on
                    elif key.startswith("vol_"):
                        vol_map = {"vol_low": 0.1, "vol_medium": 0.3, "vol_high": 0.6}
                        self.music_vol = vol_map.get(key, 0.3)
                        if self.music_on:
                            try:
                                pygame.mixer.music.set_volume(self.music_vol)
                            except Exception:
                                pass

    def handle_game_click(self, pos):
        x, y = pos

        # Winner popup buttons
        if self.game_over:
            if self.restart_rect and self.restart_rect.collidepoint(pos):
                self._play(self.sfx_btn)
                self.gs.reset()
                self.game_over = False
                self.winner = None
                self.selected = None
                self.set_message("New game started!", GREEN_MSG)
            elif self.menu_btn_rect and self.menu_btn_rect.collidepoint(pos):
                self._play(self.sfx_btn)
                self.game_over = False
                self.state = "menu"
            return

        if self.awaiting_question:
            return

        if self.gs.mode == "ai" and getattr(self.gs, "ai", None) and self.gs.turn == self.gs.ai.color:
            self.set_message("AI is thinking...", TEXT_DIM, 30)
            return

        # Ability card clicks (Enhanced, player's turn)
        if self.gs.game_mode == "enhanced" and self.gs.turn == "W":
            for card_key, cr in self.ability_rects.items():
                if cr.collidepoint(pos):
                    count = self.gs.ability_cards.get("W", {}).get(card_key, 0)
                    if count > 0:
                        res = self.gs.use_ability("W", card_key)
                        if res.get("valid"):
                            self._play(self.sfx_btn)
                            self.set_message(res["message"], GOLD_MSG)
                            if res.get("effect") == "skip":
                                self.skip_next_question = True
                    else:
                        self.set_message("No cards left!", RED_MSG, 60)
                    return

        # Settings overlay open
        r = self._btn_rects.get("settings_btn")
        if r and r.collidepoint(pos):
            self._play(self.sfx_btn)
            self.show_settings_overlay = True
            return

        # Panel buttons
        for key in ("new", "undo", "save", "load"):
            r = self._btn_rects.get(key)
            if r and r.collidepoint(pos):
                self._play(self.sfx_btn)
                if key == "new":
                    self.gs.reset()
                    self.game_over = False
                    self.winner = None
                    self.selected = None
                    self.skip_next_question = False
                    self.set_message("New game", GREEN_MSG)
                elif key == "undo":
                    ok = self.gs.undo()
                    self.set_message("Undone" if ok else "Nothing to undo", TEXT_DIM)
                elif key == "save":
                    self.gs.save("savegame.json")
                    self.set_message("Game saved ✓", GREEN_MSG)
                elif key == "load":
                    try:
                        self.gs.load("savegame.json")
                        self.set_message("Game loaded ✓", GREEN_MSG)
                    except Exception as e:
                        self.set_message(f"Load failed: {e}", RED_MSG)
                return

        # Board click
        coord = self.board_coord(x, y)
        if coord is None:
            return

        r, c = coord
        piece = self.gs.board.get(coord)

        # Chain capture: force selection of chain piece
        if self.gs.game_mode == "enhanced" and self.gs.chain_capture_pos:
            self.selected = self.gs.chain_capture_pos

        if self.selected is None:
            if piece and piece.color == self.gs.turn:
                self.selected = coord
            return

        if coord == self.selected:
            if not (self.gs.game_mode == "enhanced" and self.gs.chain_capture_pos):
                self.selected = None
            return

        if piece and piece.color == self.gs.turn:
            if not (self.gs.game_mode == "enhanced" and self.gs.chain_capture_pos):
                self.selected = coord
            return

        # Attempt move
        frm = self.selected
        to  = coord
        res_try = self.gs.board.try_move(frm, to)
        if not res_try["valid"]:
            self.set_message(res_try.get("message", "Invalid move"), RED_MSG, 60)
            return

        if res_try.get("capture"):
            # Skip question card active?
            if self.skip_next_question:
                self.skip_next_question = False
                res = self.gs.make_move_with_math(frm, to, "", skip_question=True)
                self._handle_move_result(res, frm, to)
                return

            q = self.gs.get_math_question_for_move(frm, to)
            if q:
                self.pending_move = (frm, to, q)
                self.awaiting_question = q
                self.answer_text = ""
            else:
                # No question: apply directly
                res = self.gs.make_move_with_math(frm, to, "", skip_question=True)
                self._handle_move_result(res, frm, to)
        else:
            # Normal move
            self.gs.push_undo()
            self.gs.board.apply_move(frm, to)
            if self.gs.game_mode == "enhanced":
                self.gs._move_special(frm, to)
                self.gs.combo_streak[self.gs.turn] = 0
                self.gs.chain_capture_pos = None
            self.gs.move_count += 1
            self.gs.turn = "W" if self.gs.turn == "B" else "B"
            self._play(self.sfx_move)
            self.selected = None
            self.set_message("Moved", TEXT_DIM, 60)
            self.check_game_over()

    def _handle_move_result(self, res, frm, to):
        msg   = res.get("message", "")
        valid = res.get("valid", False)

        if valid:
            self._play(self.sfx_capture)
            color = GOLD_MSG if "Chain" in msg or "combo" in msg.lower() else GREEN_MSG
            self.set_message(msg, color)
            self.selected = None
            if res.get("chain"):
                self.gs.chain_capture_pos = res.get("chain_pos")
                self.selected = res.get("chain_pos")
                self.set_message(msg + " — Select next capture!", CHAIN_CLR)
            else:
                self.gs.chain_capture_pos = None
        else:
            self._play(None)
            self.set_message(msg, RED_MSG)
            self.selected = None

        if res.get("winner"):
            self.check_game_over()

    def handle_modal_key(self, ev):
        if ev.key == pygame.K_RETURN:
            if not self.pending_move:
                self.awaiting_question = None
                self.answer_text = ""
                return
            frm, to, q = self.pending_move
            res = self.gs.make_move_with_math(frm, to, self.answer_text, q)
            self._record_answer(res.get("valid", False))
            self.awaiting_question = None
            self.pending_move = None
            self.answer_text = ""
            self._handle_move_result(res, frm, to)
        elif ev.key == pygame.K_ESCAPE:
            self.awaiting_question = None
            self.pending_move = None
            self.answer_text = ""
            self.set_message("Cancelled", TEXT_DIM, 60)
        elif ev.key == pygame.K_BACKSPACE:
            self.answer_text = self.answer_text[:-1]
        else:
            ch = ev.unicode
            if ch.isdigit() or (ch in ("-", ".") and ch not in self.answer_text):
                self.answer_text += ch

    def _handle_overlay_click(self, pos):
        if self._btn_rects.get("ov_music") and self._btn_rects["ov_music"].collidepoint(pos):
            self.music_on = not self.music_on
            try:
                if self.music_on:
                    pygame.mixer.music.set_volume(self.music_vol)
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.pause()
            except Exception:
                pass
        elif self._btn_rects.get("ov_sfx") and self._btn_rects["ov_sfx"].collidepoint(pos):
            self.sfx_on = not self.sfx_on
        elif self._btn_rects.get("ov_menu") and self._btn_rects["ov_menu"].collidepoint(pos):
            self.show_settings_overlay = False
            self.game_over = False
            self.selected = None
            self.state = "menu"
        elif self._btn_rects.get("ov_quit") and self._btn_rects["ov_quit"].collidepoint(pos):
            pygame.quit()
            sys.exit()
        elif self._btn_rects.get("ov_close") and self._btn_rects["ov_close"].collidepoint(pos):
            self.show_settings_overlay = False

    def _play(self, sfx):
        if sfx and self.sfx_on:
            try: sfx.play()
            except Exception: pass

    # ════════════════════════════════════════════════════════════════
    # MAIN LOOP
    # ════════════════════════════════════════════════════════════════
    def run(self):
        while self.running:
            self.clock.tick(30)
            self.hover_pos = pygame.mouse.get_pos()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False; break

                if ev.type == pygame.VIDEORESIZE:
                    pass  # RESIZABLE handles it

                # Modal exclusive
                if self.awaiting_question is not None:
                    if ev.type == pygame.KEYDOWN:
                        self.handle_modal_key(ev)
                    continue

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    p = ev.pos
                    if self.state == "menu":
                        self.handle_menu_click(p)
                    elif self.state == "mode_select":
                        self.handle_mode_click(p)
                    elif self.state == "play_select":
                        self.handle_play_click(p)
                    elif self.state == "difficulty_select":
                        self.handle_diff_click(p)
                    elif self.state == "settings":
                        self.handle_settings_click(p)
                    elif self.state == "game":
                        if self.show_settings_overlay:
                            self._handle_overlay_click(p)
                        else:
                            self.handle_game_click(p)

                if ev.type == pygame.KEYDOWN and self.state == "game":
                    if ev.key == pygame.K_ESCAPE:
                        if self.show_settings_overlay:
                            self.show_settings_overlay = False
                        else:
                            self.selected = None
                    elif ev.key == pygame.K_u:
                        self.gs.undo()
                        self.set_message("Undone", TEXT_DIM)
                    elif ev.key == pygame.K_s:
                        self.gs.save("savegame.json")
                        self.set_message("Saved ✓", GREEN_MSG)

            # Decrement message timer
            if self.msg_timer > 0:
                self.msg_timer -= 1

            # AI auto-move
            if (self.state == "game" and self.gs
                    and self.gs.mode == "ai"
                    and getattr(self.gs, "ai", None)
                    and self.gs.turn == self.gs.ai.color
                    and self.awaiting_question is None
                    and not self.game_over):
                try:
                    ai_res = self.gs.make_move_ai()
                    if isinstance(ai_res, dict):
                        msg = ai_res.get("message", "")
                        color = GREEN_MSG if ai_res.get("capture") else TEXT_DIM
                        if "frozen" in msg:
                            color = (120, 200, 240)
                        self.set_message(msg, color)
                        if ai_res.get("capture") and self.sfx_capture:
                            self._play(self.sfx_capture)
                        self.check_game_over()
                except Exception:
                    pass

            # ── Render ───────────────────────────────────────────
            self.draw_bg()

            if self.state == "menu":
                self.draw_menu()
            elif self.state == "mode_select":
                self.draw_mode_select()
            elif self.state == "play_select":
                self.draw_play_select()
            elif self.state == "difficulty_select":
                self.draw_difficulty_select()
            elif self.state == "settings":
                self.draw_settings()
            elif self.state == "game" and self.gs:
                self.draw_title_bar()
                self.draw_board()
                self.draw_panel()
                if self.game_over:
                    self.draw_winner_popup()
                if self.awaiting_question:
                    self.draw_question_modal()
                if self.show_settings_overlay:
                    self.draw_settings_overlay()
            else:
                self.screen.fill(BG)

            pygame.display.flip()

        pygame.quit()

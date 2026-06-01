"""
game.py

High-level game management: current Board, turns, applying moves subject to math checks,
undo stack, save/load integration, modes (2p vs AI), options.

Class GameState: public interface used by UI.
"""

from typing import Optional, Tuple, List, Dict
from board import Board
from piece import WHITE, BLACK
from mathgen import generate_question, MathQuestion
from ai import AI
import savegame
import random
print("✅ USING THIS game.py FILE")


Coord = Tuple[int, int]


class GameState:
    def __init__(self, mode="ai", ai_difficulty=2, math_ops=None, timed_mode=False, time_limit=0.0, game_mode="classic"):
        if math_ops is None:
            math_ops = ["add", "sub"]

        self.mode = mode
        self.ai_difficulty = ai_difficulty
        self.math_ops = math_ops
        self.game_mode = game_mode  # "classic" or "enhanced"

        self.options = {
            "math_ops": math_ops,
            "timed_mode": timed_mode,
            "time_limit": time_limit,
            "ai_difficulty": ai_difficulty,
        }

        self.timed_mode = timed_mode
        self.time_limit = time_limit

        from board import Board
        self.board = Board()
        self.turn = "W"
        self.undo_stack = []
        self.move_count = 0
        self.capture_count = 0
        self.scores = {"W": 0, "B": 0}
        self.ai = None

        # Enhanced mode state
        self.ability_cards = {"W": {}, "B": {}}
        self.special_pieces = {}   # pos -> "wild" | "power"
        self.combo_streak = {"W": 0, "B": 0}
        self.ai_frozen_turns = 0
        self.pending_double = False  # double-points card queued
        self.chain_capture_pos = None  # position for chain capture

        if self.mode == "ai":
            try:
                from ai import AI
                ai_color = "W" if self.turn == "B" else "B"
                self.ai = AI(color=ai_color, difficulty=self.ai_difficulty)
            except Exception as e:
                print("⚠️ Failed to create AI in GameState __init__:", e)
                self.ai = None

        if self.game_mode == "enhanced":
            self._init_enhanced()

    # --------------------------------------------------------------
    # Enhanced Mode Setup
    # --------------------------------------------------------------
    def _init_enhanced(self):
        """Set up ability cards and special pieces for Enhanced mode."""
        self.ability_cards = {
            "W": {"skip": 2, "double": 1, "freeze": 1},
            "B": {"skip": 2, "double": 1, "freeze": 1},
        }
        self._assign_special_pieces()

    def _assign_special_pieces(self):
        """Randomly mark 2 wild + 2 power pieces per side."""
        self.special_pieces = {}
        for color in ["W", "B"]:
            pieces = self.board.all_pieces(color)
            if len(pieces) >= 4:
                chosen = random.sample(pieces, 4)
                for i, pos in enumerate(chosen):
                    piece = self.board.get(pos)
                    if piece:
                        stype = "wild" if i < 2 else "power"
                        piece.special = stype
                        self.special_pieces[pos] = stype

    def _move_special(self, frm, to, captured_pos=None):
        """Update special_pieces tracking when a piece moves or is captured."""
        if frm in self.special_pieces:
            self.special_pieces[to] = self.special_pieces.pop(frm)
        if captured_pos and captured_pos in self.special_pieces:
            del self.special_pieces[captured_pos]

    def use_ability(self, player: str, card: str) -> Dict:
        """Use an ability card. Returns {"valid", "message", "effect"}."""
        if self.game_mode != "enhanced":
            return {"valid": False, "message": "Enhanced mode only"}
        cards = self.ability_cards.get(player, {})
        if cards.get(card, 0) <= 0:
            return {"valid": False, "message": f"No {card} cards left!"}
        self.ability_cards[player][card] -= 1
        if card == "freeze":
            self.ai_frozen_turns = 3
            return {"valid": True, "message": "❄️ AI frozen for 3 turns!", "effect": "freeze"}
        if card == "double":
            self.pending_double = True
            return {"valid": True, "message": "💎 Next capture scores 2×!", "effect": "double"}
        if card == "skip":
            return {"valid": True, "message": "⚡ Question skipped!", "effect": "skip"}
        return {"valid": False, "message": "Unknown card"}

    def check_chain_capture(self, pos) -> bool:
        """Check if the piece at pos can make another capture."""
        if self.game_mode != "enhanced":
            return False
        r, c = pos
        for dr in [-1, 1]:
            for dc in [-1, 1]:
                target = (r + dr * 2, c + dc * 2)
                res = self.board.try_move(pos, target)
                if res.get("valid") and res.get("capture"):
                    return True
        return False

    # --------------------------------------------------------------
    # Utility and state management
    # --------------------------------------------------------------
    def reset(self):
        self.board.reset()
        self.turn = WHITE
        self.undo_stack.clear()
        self.move_count = 0
        self.capture_count = 0
        self.scores = {"W": 0, "B": 0}
        self.combo_streak = {"W": 0, "B": 0}
        self.ai_frozen_turns = 0
        self.pending_double = False
        self.chain_capture_pos = None
        if self.game_mode == "enhanced":
            self._init_enhanced()

    def push_undo(self):
        self.undo_stack.append({
            "board": self.board.clone(),
            "turn": self.turn,
            "move_count": self.move_count,
            "capture_count": self.capture_count,
            "scores": self.scores.copy()
        })
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        st = self.undo_stack.pop()
        self.board = st["board"]
        self.turn = st["turn"]
        self.move_count = st["move_count"]
        self.capture_count = st["capture_count"]
        self.scores = st["scores"]
        return True

        # --------------------------------------------------------------
        # Math question generation
        # --------------------------------------------------------------
        
    def get_math_question_for_move(self, frm, to):

        # Check if this is a valid capture
        res_try = self.board.try_move(frm, to)
        if not res_try["valid"] or not res_try.get("capture"):
            return None

        moving_piece = self.board.get(frm)
        captured_pos = res_try["capture"]
        captured_piece = self.board.get(captured_pos)

        if not moving_piece or not captured_piece:
            return None

        # ✅ Correct operator location:
        # Operator comes from the LANDING SQUARE
        op = self.board.operator_at(to)

        if not op:
            print(f"⚠️ No operator on landing square {to}")
            return None

        a = moving_piece.value
        b = captured_piece.value

        # Compute result based on operator from landing tile
        try:
            if op == '+':
                answer = a + b
            elif op == '-':
                answer = a - b
            elif op in ['*', '×']:
                answer = a * b
            elif op in ['/', '÷']:
                if b == 0:
                    return None
                answer = int(a / b)   # truncated
            else:
                return None
        except Exception as ex:
            print("⚠️ Error computing math:", ex)
            return None

        # Display-friendly operator
        display_op = {'*': '×', '/': '÷'}.get(op, op)

        text = f"{a} {display_op} {b}"
        return MathQuestion(text=text, answer=answer)


    def generate_math_for_move(self) -> MathQuestion:
        level = 1 + (self.capture_count // 1) + (self.move_count // 10)
        timed = self.options["time_limit"] if self.options["timed_mode"] else 0.0
        return generate_question(level=level, ops=self.options["math_ops"], timed=timed)

    # --------------------------------------------------------------
    # Main move logic (with math check)
    # --------------------------------------------------------------
    def make_move_with_math(self, frm, to, player_response: str, q: Optional[MathQuestion] = None, skip_question: bool = False):
        """
        Apply a move that may require a math question to capture.
        Enhanced mode: supports wild/power pieces, double card, chain captures.
        Returns a dict {"valid": bool, "message": str}
        """
        try:
            piece = self.board.get(frm)
            if piece is None or piece.color != self.turn:
                return {"valid": False, "message": "Invalid piece selection"}

            res_try = self.board.try_move(frm, to)
            if not res_try["valid"]:
                return {"valid": False, "message": res_try["message"]}

            if res_try.get("capture"):
                # Enhanced: wild piece auto-captures without question
                is_wild = self.game_mode == "enhanced" and self.special_pieces.get(frm) == "wild"
                is_power = self.game_mode == "enhanced" and self.special_pieces.get(frm) == "power"

                if not is_wild and not skip_question:
                    question = q if q is not None else self.get_math_question_for_move(frm, to)
                    if not question:
                        return {"valid": False, "message": "No math question generated"}

                    player_resp_str = "" if player_response is None else str(player_response).strip()
                    if player_resp_str == "":
                        return {"valid": False, "message": "No answer entered"}

                    try:
                        ok = question.check(player_resp_str)
                    except Exception as ex:
                        import traceback; traceback.print_exc()
                        return {"valid": False, "message": f"Error validating answer: {ex}"}

                    if not ok:
                        self.combo_streak[self.turn] = 0
                        self.turn = WHITE if self.turn == BLACK else BLACK
                        return {"valid": False, "message": "Wrong answer! Enemy's turn"}
                else:
                    # Wild/skip — create a dummy "question" with answer=0 for score
                    question = None

                # ✅ Correct / wild / skipped — apply capture
                self.push_undo()
                captured_pos = res_try.get("capture")
                self.board.apply_move(frm, to)

                # Score calculation
                if question:
                    try:
                        safe_score = int(float(question.answer))
                    except Exception:
                        safe_score = 0
                else:
                    safe_score = 5 if is_wild else 0  # wild gives flat 5 pts

                # Power piece doubles score
                if is_power:
                    safe_score *= 2
                # Double card active
                if self.pending_double and self.game_mode == "enhanced":
                    safe_score *= 2
                    self.pending_double = False

                if not isinstance(self.scores, dict):
                    self.scores = {"W": 0, "B": 0}
                self.scores[self.turn] = self.scores.get(self.turn, 0) + safe_score

                # Combo streak (Enhanced)
                if self.game_mode == "enhanced":
                    self.combo_streak[self.turn] = self.combo_streak.get(self.turn, 0) + 1
                    if self.combo_streak[self.turn] >= 3:
                        bonus = 5 * self.combo_streak[self.turn]
                        self.scores[self.turn] += bonus
                        safe_score += bonus

                # Update special piece tracking
                if self.game_mode == "enhanced":
                    self._move_special(frm, to, captured_pos)

                sign = "+" if safe_score >= 0 else ""
                self.move_count += 1
                self.capture_count += 1
                msg = f"⚡ Wild capture! +{safe_score} pts" if is_wild else f"Correct! {sign}{safe_score} pts"
                if is_power and not is_wild:
                    msg = f"💎 Power! {sign}{safe_score} pts (×2)"

                # Chain capture check (Enhanced)
                if self.game_mode == "enhanced" and self.check_chain_capture(to):
                    self.chain_capture_pos = to
                    # Don't switch turn — player gets another capture
                    winner = self.check_winner()
                    return {"valid": True, "message": msg + " — CHAIN!", "applied": True,
                            "winner": winner, "chain": True, "chain_pos": to}

            else:
                # Normal move (no capture)
                self.push_undo()
                self.board.apply_move(frm, to)
                if self.game_mode == "enhanced":
                    self._move_special(frm, to)
                    self.combo_streak[self.turn] = 0
                self.move_count += 1
                self.chain_capture_pos = None
                msg = "Moved"
                self.turn = WHITE if self.turn == BLACK else BLACK
                winner = self.check_winner()
                return {"valid": True, "message": msg, "applied": True, "winner": winner}

            # Switch turn after capture
            self.chain_capture_pos = None
            self.turn = WHITE if self.turn == BLACK else BLACK
            winner = self.check_winner()
            return {"valid": True, "message": msg, "applied": True, "winner": winner}

        except Exception as e:
            import traceback
            print("\n=== UNEXPECTED ERROR in make_move_with_math ===")
            traceback.print_exc()
            print("=== END TRACE ===\n")
            return {"valid": False, "message": f"Unexpected error: {e}"}


    # --------------------------------------------------------------
    # AI logic
    # --------------------------------------------------------------
    def make_move_ai(self) -> Dict:
        if not self.ai or self.turn != self.ai.color:
            return {"valid": False, "message": "AI not active or not AI's turn"}

        # Enhanced: AI frozen
        if self.game_mode == "enhanced" and self.ai_frozen_turns > 0:
            self.ai_frozen_turns -= 1
            self.turn = "W" if self.turn == "B" else "B"
            remaining = self.ai_frozen_turns
            return {"valid": False, "message": f"❄️ AI frozen! ({remaining} turns left)"}

        chosen = self.ai.choose_move(self.board)
        if not chosen:
            # No moves available at all — switch turn so game doesn't freeze
            print("AI.choose_move returned no move — switching turn.")
            self.turn = "W" if self.turn == "B" else "B"
            winner = self.check_winner()
            return {"valid": False, "message": "AI has no moves", "winner": winner}

        frm, to = chosen
        print(f"AI attempting move {frm} -> {to}")
        res_try = self.board.try_move(frm, to)
        if not res_try["valid"]:
            # Invalid move chosen — switch turn to avoid infinite retry loop
            print("AI tried invalid move:", res_try.get("message"), "— switching turn.")
            self.turn = "W" if self.turn == "B" else "B"
            return {"valid": False, "message": "AI moved"}

        # If capture, handle math question (AI may fail)
        if res_try.get("capture"):
            question = self.get_math_question_for_move(frm, to)
            if not question:
                # No operator on landing square — forfeit capture, switch turn
                # CRITICAL: must switch turn here or UI freezes retrying every frame
                print("AI: no question for capture — forfeiting, switching turn.")
                self.turn = "W" if self.turn == "B" else "B"
                return {"valid": False, "message": "AI moved"}

            # AI solves with probability based on difficulty
            if not self.ai.solve_math_success():
                print("AI failed math question; capture not applied.")
                self.turn = "W" if self.turn == "B" else "B"
                return {"valid": False, "message": "AI failed math (no capture)"}

            # AI solved: apply capture and grant points
            self.push_undo()
            self.board.apply_move(frm, to)
            try:
                pts = int(question.answer)
            except Exception:
                pts = 0
            self.scores[self.ai.color] = self.scores.get(self.ai.color, 0) + pts
            self.move_count = getattr(self, "move_count", 0) + 1
            self.capture_count = getattr(self, "capture_count", 0) + 1
            msg = f"AI captured and gained +{pts} points"
            self.turn = "W" if self.turn == "B" else "B"
            print("AI capture applied:", frm, to, "points:", pts)
            winner = self.check_winner()
            return {"valid": True, "message": msg, "capture": True, "applied": True, "winner": winner}

        # Non-capture simple move
        self.push_undo()
        self.board.apply_move(frm, to)
        self.move_count = getattr(self, "move_count", 0) + 1
        msg = "AI moved"
        self.turn = "W" if self.turn == "B" else "B"
        print("AI move applied:", frm, to)
        winner = self.check_winner()
        return {"valid": True, "message": msg, "applied": True, "winner": winner}


    # --------------------------------------------------------------
    # Winner Detection
    # --------------------------------------------------------------
    def check_winner(self) -> Optional[str]:
        """
        Game ends when a player has no pieces or no valid moves.
        Winner = player with the HIGHEST score.
        Tie-break: more pieces remaining.
        """
        w_pieces = []
        b_pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.board.get((row, col))
                if piece:
                    if piece.color == WHITE:
                        w_pieces.append((row, col))
                    else:
                        b_pieces.append((row, col))

        game_ended = False

        # Condition 1: a side has no pieces left
        if not w_pieces or not b_pieces:
            game_ended = True

        # Condition 2: current player has no valid moves
        if not game_ended:
            current_pieces = w_pieces if self.turn == WHITE else b_pieces
            has_move = False
            for pos in current_pieces:
                r, c = pos
                for dr in [-1, 1]:
                    for dc in [-1, 1]:
                        for dist in [1, 2]:
                            target = (r + dr * dist, c + dc * dist)
                            result = self.board.try_move(pos, target)
                            if result.get("valid"):
                                has_move = True
                                break
                        if has_move: break
                    if has_move: break
                if has_move: break
            if not has_move:
                game_ended = True

        if not game_ended:
            return None

        # Winner = highest score
        ws = self.scores.get("W", 0)
        bs = self.scores.get("B", 0)
        if ws > bs:
            return WHITE
        elif bs > ws:
            return BLACK
        else:
            # Tie-break: more pieces remaining
            return WHITE if len(w_pieces) >= len(b_pieces) else BLACK

    def get_winner_message(self) -> Optional[str]:
        """Returns a human-readable winner message, or None if game is ongoing."""
        winner = self.check_winner()
        if winner == WHITE:
            w_score = self.scores.get("W", 0)
            b_score = self.scores.get("B", 0)
            return f"🏆 White wins! (White: {w_score} pts  |  Black: {b_score} pts)"
        elif winner == BLACK:
            w_score = self.scores.get("W", 0)
            b_score = self.scores.get("B", 0)
            return f"🏆 Black wins! (White: {w_score} pts  |  Black: {b_score} pts)"
        return None

    # --------------------------------------------------------------
    # Save/Load
    # --------------------------------------------------------------
    def save(self, path: str):
        savegame.save_game(path, self.board, self.turn, self.options)

    def load(self, path: str):
        b, turn, opts = savegame.load_game(path)
        self.board = b
        self.turn = turn
        self.options.update(opts)
        # Re-create AI if mode demands it
        if self.mode == "ai":
            try:
                self.ai = AI(color=BLACK, difficulty=self.options.get("ai_difficulty", self.ai_difficulty))
            except Exception:
                self.ai = None
        else:
            self.ai = None
        return True

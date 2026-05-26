"""
ai.py

Basic AI for single-player mode. Design goals:
- Simple, explainable.
- Adjustable difficulty.
- Uses board.available_moves_for to get legal moves; evaluates via a simple heuristic.
- Also models math challenge 'failure' probability: at higher difficulty AI 'solves' higher fraction of questions.

Class: AI
"""

from typing import Tuple, Optional, List
from board import Board
import random
import copy

Coord = Tuple[int,int]

class AI:
    def __init__(self, color: str, difficulty: int = 2):
        """
        difficulty: 1 (easy) .. 5 (hard)
        The AI will solve math questions with probability = 0.5 + 0.1*(difficulty-1).
        The AI chooses moves by a shallow search (depth = difficulty).
        """
        self.color = color
        self.difficulty = max(1, min(5, difficulty))

    def solve_math_success(self) -> bool:
        p = 0.5 + 0.1*(self.difficulty-1)
        return random.random() < p

    def heuristic(self, board: Board) -> int:
        # Evaluate by piece count + king weight
        score = 0
        for r in range(Board.ROWS):
            for c in range(Board.COLS):
                p = board.get((r,c))
                if p:
                    val = 1 + (1 if p.king else 0)
                    score += val if p.color == self.color else -val
        return score

    def choose_move(self, board: Board) -> Optional[Tuple[Coord,Coord]]:
        """
        Choose best move using depth-limited greedy search (not full minimax for simplicity).
        For performance and simplicity, perform one-step lookahead upto depth = difficulty.
        """
        moves = board.available_moves_for(self.color)
        if not moves:
            return None
        best = None
        best_score = -10**9
        # If many moves, sample randomness to avoid long loops
        sample_moves = moves if len(moves) <= 20 else random.sample(moves, 20)
        for frm, to, _ in sample_moves:
            b2 = board.clone()
            b2.apply_move(frm, to)
            score = self.heuristic(b2)
            # shallow search: evaluate next opponent move (simulate)
            # depth based on difficulty
            for _ in range(self.difficulty - 1):
                opp_moves = b2.available_moves_for(self.opponent())
                if not opp_moves:
                    break
                # assume opponent picks best (adversarial)
                best_opp_score = 10**9
                chosen = None
                for ofrm, oto, _ in opp_moves:
                    b3 = b2.clone()
                    b3.apply_move(ofrm, oto)
                    s = self.heuristic(b3)
                    if s < best_opp_score:
                        best_opp_score = s
                        chosen = (ofrm, oto)
                if chosen:
                    b2.apply_move(*chosen)
                    score = self.heuristic(b2)
                else:
                    break
            # small randomness for exploration
            score += random.uniform(-0.5, 0.5)
            if score > best_score:
                best_score = score
                best = (frm, to)
        return best

    def opponent(self):
        return "W" if self.color == "B" else "B"
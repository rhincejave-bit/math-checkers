"""
piece.py

Defines Piece class and constants.
"""

from dataclasses import dataclass

WHITE = "W"
BLACK = "B"

@dataclass
class Piece:
    color: str           # 'W' or 'B'
    value: int = 0       # Damath integer assigned to the piece
    king: bool = False

    def crown(self):
        self.king = True

    def opposite(self):
        return BLACK if self.color == WHITE else WHITE

    def __repr__(self):
        return f"{'K' if self.king else 'P'}{self.color}({self.value})"

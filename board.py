"""
board.py

Board: holds an 8x8 matrix of Pieces or None. Implements movement rules, captures,
kinging, and provides available moves for a player.

Separation of concerns: pure game-state logic (no UI).
"""

from typing import List, Tuple, Optional, Dict
from piece import Piece, WHITE, BLACK
import copy

# --------------------------------------------------------------------
# Operator layout (from Damath board image, 8×8, operators only on dark squares)
# --------------------------------------------------------------------
OP_LAYOUT = [
    [None, '/',   None, '-',   None, '+',   None, '*'],
    ['-',  None,  '+',  None,  '*',  None,  '/',  None],
    [None, '*',   None, '/',   None, '+',   None, '-'],
    ['+',  None,  '-',  None,  '/',  None,  '*',  None],
    [None, '*',   None, '/',   None, '+',   None, '-'],
    ['/',  None,  '*',  None,  '+',  None,  '-',  None],
    [None, '-',   None, '+',   None, '/',   None, '*'],
    ['+',  None,  '-',  None,  '/',  None,  '*',  None],
]

# --------------------------------------------------------------------
# Piece values (from Damath layout)
# --------------------------------------------------------------------
# Values for White pieces (bottom side)
WHITE_VALUES = [
    [-9,   6, -1,  4],
    [ 0,  -3, 10, -7],
    [-11,  8, -5,  2]
]

# Mirrored values for Black pieces (top side)
BLACK_VALUES = [
    [-2,   5, -8, 11],
    [ 7, -10,  3,  0],
    [-4,   1, -6,  9]
]

Coord = Tuple[int, int]  # (row, col)
Move = Tuple[Coord, Coord]  # (from, to)

# --------------------------------------------------------------------
# Board class
# --------------------------------------------------------------------
class Board:
    ROWS = 8
    COLS = 8

    def legal_moves_from(self, pos):
        """Return a list of legal tiles this piece can move to."""
        piece = self.get(pos)
        if not piece:
            return []

        r, c = pos
        potential_moves = []

        # Single and double steps (move & capture patterns)
        for dr in (-1, 1, -2, 2):
            for dc in (-1, 1, -2, 2):
                to = (r + dr, c + dc)
                if not self.inside(*to):
                    continue
                result = self.try_move(pos, to)
                if result["valid"]:
                    potential_moves.append(to)

        return potential_moves

    def __init__(self):
        # grid[row][col] holds Piece or None
        self.grid: List[List[Optional[Piece]]] = [
            [None for _ in range(Board.COLS)] for _ in range(Board.ROWS)
        ]
        self.reset()

    def reset(self):
        """Place initial pieces with correct Damath values on dark squares only."""
        self.grid = [[None for _ in range(Board.COLS)] for _ in range(Board.ROWS)]

        # --- Black pieces (rows 0–2, mirrored values) ---
        for r in range(3):  # rows 0,1,2
            for c in range(Board.COLS):
                if (r + c) % 2 == 1:  # only dark squares
                    value = BLACK_VALUES[r][c // 2]
                    self.grid[r][c] = Piece(BLACK, value)

        # --- White pieces (rows 5–7, original values) ---
        for r in range(5, 8):  # rows 5,6,7
            for c in range(Board.COLS):
                if (r + c) % 2 == 1:  # only dark squares
                    value = WHITE_VALUES[r - 5][c // 2]  # shift down index
                    self.grid[r][c] = Piece(WHITE, value)

    def operator_at(self, pos: Coord) -> Optional[str]:
        """Return operator symbol at a square, or None if not an operator square."""
        r, c = pos
        if 0 <= r < Board.ROWS and 0 <= c < Board.COLS:
            return OP_LAYOUT[r][c]
        return None

    def inside(self, r: int, c: int) -> bool:
        return 0 <= r < Board.ROWS and 0 <= c < Board.COLS

    def get(self, pos: Coord) -> Optional[Piece]:
        r, c = pos
        return self.grid[r][c]

    def set(self, pos: Coord, piece: Optional[Piece]):
        r, c = pos
        self.grid[r][c] = piece

    def clone(self) -> "Board":
        return copy.deepcopy(self)

    def king_row_for(self, color: str) -> int:
        return 0 if color == WHITE else Board.ROWS - 1

    def try_move(self, frm: Coord, to: Coord) -> Dict:
        """
        Attempt a move; return dict with keys:
         - valid: bool
         - capture: Optional[Coord] (position of captured piece)
         - promote: bool
         - message: str
        Does not require math checks; just rule evaluation.
        """
        if not self.inside(*frm) or not self.inside(*to):
            return {"valid": False, "message": "Out of bounds", "capture": None, "promote": False}
        piece = self.get(frm)
        if piece is None:
            return {"valid": False, "message": "No piece at source", "capture": None, "promote": False}
        dest_piece = self.get(to)
        if dest_piece is not None:
            return {"valid": False, "message": "Destination not empty", "capture": None, "promote": False}
        dr = to[0] - frm[0]
        dc = to[1] - frm[1]
        absdr, absdc = abs(dr), abs(dc)

        direction = -1 if piece.color == WHITE else 1

        # Simple move
        if absdr == 1 and absdc == 1:
            if piece.king or dr == direction:
                promote = (to[0] == self.king_row_for(piece.color))
                return {"valid": True, "capture": None, "promote": promote, "message": "Move"}
            return {"valid": False, "message": "Wrong direction", "capture": None, "promote": False}

        # Capture
        if absdr == 2 and absdc == 2:
            mid = ((frm[0] + to[0]) // 2, (frm[1] + to[1]) // 2)
            mid_piece = self.get(mid)
            if mid_piece and mid_piece.color != piece.color:
                if piece.king or (dr == 2 * direction):
                    promote = (to[0] == self.king_row_for(piece.color))
                    return {"valid": True, "capture": mid, "promote": promote, "message": "Capture"}
                return {"valid": False, "message": "Wrong direction for capture", "capture": None, "promote": False}
            return {"valid": False, "message": "No opponent to capture", "capture": None, "promote": False}

        return {"valid": False, "message": "Invalid move", "capture": None, "promote": False}

    def apply_move(self, frm: Coord, to: Coord) -> Dict:
        """Mutates the board if move valid. Returns the same dict as try_move but applied."""
        res = self.try_move(frm, to)
        if not res["valid"]:
            return res
        piece = self.get(frm)
        self.set(frm, None)
        self.set(to, piece)
        if res["capture"]:
            self.set(res["capture"], None)
        if res["promote"]:
            piece.crown()
        return res

    def all_pieces(self, color: str) -> List[Coord]:
        coords = []
        for r in range(Board.ROWS):
            for c in range(Board.COLS):
                p = self.grid[r][c]
                if p and p.color == color:
                    coords.append((r, c))
        return coords

    def available_moves_for(self, color: str) -> List[Tuple[Coord, Coord, Dict]]:
        """Returns a list of (from, to, result_dict) for all legal moves for color."""
        moves = []
        captures = []
        for frm in self.all_pieces(color):
            r, c = frm
            for dr in (-1, 1, -2, 2):
                for dc in (-1, 1, -2, 2):
                    to = (r + dr, c + dc)
                    if not self.inside(*to):
                        continue
                    res = self.try_move(frm, to)
                    if res["valid"]:
                        if res["capture"]:
                            captures.append((frm, to, res))
                        else:
                            moves.append((frm, to, res))
        return captures if captures else moves

    def winner(self) -> Optional[str]:
        """Return 'W' or 'B' or None (if none yet or draw)."""
        w = self.all_pieces(WHITE)
        b = self.all_pieces(BLACK)
        if not w:
            return BLACK
        if not b:
            return WHITE
        if not self.available_moves_for(WHITE):
            return BLACK
        if not self.available_moves_for(BLACK):
            return WHITE
        return None

    def __repr__(self):
        rows = []
        for r in range(Board.ROWS):
            row = []
            for c in range(Board.COLS):
                p = self.grid[r][c]
                row.append('.' if p is None else (
                    'W' if p.color == WHITE and not p.king else
                    'w' if p.color == WHITE and p.king else
                    'B' if p.color == BLACK and not p.king else
                    'b'))
            rows.append(' '.join(row))
        return '\n'.join(rows)

"""
savegame.py

Save and load game state (board, turn, options) into/from JSON.
"""

import json
from typing import Dict
from board import Board
from piece import Piece

# --- savegame.py: replace board_to_dict and board_from_dict ---

def board_to_dict(board: Board) -> Dict:
    data = []
    for r in range(Board.ROWS):
        row = []
        for c in range(Board.COLS):
            p = board.get((r,c))
            if p:
                row.append({
                    "color": p.color,
                    "king": p.king,
                    "value": p.value
                })
            else:
                row.append(None)
        data.append(row)
    return data

def board_from_dict(data) -> Board:
    b = Board()
    # start with empty grid (Board() already reset() but we'll replace)
    b.grid = [[None for _ in range(Board.COLS)] for _ in range(Board.ROWS)]
    for r in range(Board.ROWS):
        for c in range(Board.COLS):
            val = data[r][c]
            if val:
                # If value saved, use it; otherwise fallback to 0
                v = val.get("value", 0)
                b.set((r,c), Piece(color=val["color"], value=v, king=val["king"]))
            else:
                b.set((r,c), None)
    return b

def save_game(path: str, board: Board, turn: str, options: Dict):
    payload = {"board": board_to_dict(board), "turn": turn, "options": options}
    with open(path, "w") as f:
        json.dump(payload, f)

def load_game(path: str):
    with open(path, "r") as f:
        payload = json.load(f)
    b = board_from_dict(payload["board"])
    return b, payload.get("turn", "W"), payload.get("options", {})
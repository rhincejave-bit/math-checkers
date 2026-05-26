import pytest
from ..board import Board
from ..piece import Piece, WHITE, BLACK


def test_initial_setup():
    b = Board()
    # In Damath, each side still has 12 pieces at start
    wcount = len(b.all_pieces(WHITE))
    bcount = len(b.all_pieces(BLACK))
    assert wcount == 12
    assert bcount == 12

def test_simple_move_and_capture():
    b = Board()
    # try to move one white piece forward (non-capture)
    moved = False
    for frm in b.all_pieces(WHITE):
        r, c = frm
        for dc in (-1, 1):
            to = (r - 1, c + dc)
            if b.inside(*to) and b.get(to) is None:
                res = b.try_move(frm, to)
                if res["valid"]:
                    b.apply_move(frm, to)
                    assert b.get(to) is not None
                    moved = True
                    break
        if moved:
            break
    assert moved, "No valid simple move found for White"

def test_capture_rule():
    b = Board()
    # clear board
    b.grid = [[None] * 8 for _ in range(8)]
    # setup capture: White at (2,3), Black at (3,4)
    b.set((2, 3), Piece(WHITE, value=5))
    b.set((3, 4), Piece(BLACK, value=-3))
    res = b.try_move((2, 3), (4, 5))
    assert res["valid"] and res["capture"] == (3, 4)
    b.apply_move((2, 3), (4, 5))
    assert b.get((3, 4)) is None
    assert b.get((4, 5)) is not None

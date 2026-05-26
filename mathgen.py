"""
mathgen.py

Generates math questions for gating moves. It supports:
- adjustable operations (add, sub, mul, div)
- scaling difficulty by 'level' integer
- optional time limit (seconds)

Class: MathQuestion
Functions: generate_question

Design choices:
- Questions are small to medium sized to be appropriate for older players.
- Difficulty scales by increasing magnitude and optionally number of terms.
"""

# --- mathgen.py: replace MathQuestion class and random() implementation ---

from dataclasses import dataclass
import random
from typing import List

Ops = {
    "add": ("+", lambda a, b: a + b),
    "sub": ("-", lambda a, b: a - b),
    "mul": ("×", lambda a, b: a * b),
    "div": ("÷", lambda a, b: a // b),
}

@dataclass
class MathQuestion:
    text: str
    answer: int
    time_limit: float = 0.0  # seconds; 0 means no timer

    def __init__(self, text: str, answer: int, time_limit: float = 0.0):
        self.text = text
        self.answer = int(answer)
        self.time_limit = time_limit

    @staticmethod
    def random(ops: List[str]):
        """Return a random math question based on allowed operators (ops list)."""
        op = random.choice(ops)

        # Integer values range
        a = random.randint(1, 12)
        b = random.randint(1, 12)

        if op == "add":
            text = f"{a} + {b}"
            answer = a + b

        elif op == "sub":
            text = f"{a} - {b}"
            answer = a - b

        elif op == "mul":
            text = f"{a} × {b}"
            answer = a * b

        elif op == "div":
            # ensure b != 0 and use integer division
            if b == 0:
                b = 1
            text = f"{a} ÷ {b}"
            answer = a // b

        else:
            text = f"{a} + {b}"
            answer = a + b

        return MathQuestion(text, answer)

    def check(self, response: str) -> bool:
        try:
            # handle negatives, spaces, and accidental floats safely
            user_ans = int(float(response.strip()))
            correct_ans = int(float(self.answer))
            return user_ans == correct_ans
        except Exception:
            return False

def generate_question(level:int=1, ops:List[str]=None, allow_negative:bool=False, timed:float=0.0)->MathQuestion:
    """
    Create a math question scaled by level.
    level: 1..n (higher => bigger numbers / more terms)
    ops: list of op keys from Ops
    allow_negative: whether to permit negative results for subtraction
    timed: time limit in seconds (0 for none)
    """
    if ops is None:
        ops = ["add", "sub"]
    ops = [o for o in ops if o in Ops]
    if not ops:
        ops = ["add"]

    # Determine term count: 2 or 3 for higher levels
    terms = 2 if level <= 2 else 3
    # Magnitude scales with level
    base = min(10 + level*5, 200)
    numbers = []
    for _ in range(terms):
        n = random.randint(1, max(5, base))
        numbers.append(n)

    chosen_ops = [random.choice(ops) for _ in range(terms-1)]

    # Build expression left to right using integer arithmetic (division uses floor)
    expr = str(numbers[0])
    val = numbers[0]
    for i, op_key in enumerate(chosen_ops):
        sym, func = Ops[op_key]
        b = numbers[i+1]
        # For division, ensure divisible-ish to avoid fractions: adjust b to divisor where possible
        if op_key == "div":
            # make val divisible by b by making val = val * b
            # or ensure integer division by using values that keep integers
            b = random.randint(1, max(1, base//2))
            numbers[i+1] = b
        expr += f" {sym} {b}"
        # compute using integer division
        if op_key == "div":
            if b == 0:
                b = 1
            val = val // b
        elif op_key == "mul":
            val = val * b
        elif op_key == "add":
            val = val + b
        elif op_key == "sub":
            val = val - b

    if not allow_negative and val < 0:
        # fallback to absolute
        val = abs(val)
        expr = f"|{expr}|"

    question = MathQuestion(text=expr, answer=val, time_limit=timed)
    return question
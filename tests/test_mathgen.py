from mathgen import generate_question

def test_generate_basic():
    q = generate_question(level=1, ops=["add","sub"])
    assert isinstance(q.text, str)
    assert isinstance(q.answer, int)
    assert q.check(str(q.answer))

def test_division_produces_int():
    # include div and ensure answer is integer
    q = generate_question(level=3, ops=["div"])
    assert isinstance(q.answer, int)
    assert q.check(str(q.answer))
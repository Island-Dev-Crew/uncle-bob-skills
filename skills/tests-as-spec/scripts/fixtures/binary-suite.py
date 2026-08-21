"""Forge attempt: a file the lint cannot decode.

Byte 0xff below is not valid UTF-8. Reading it raises UnicodeDecodeError, a
subclass of ValueError - so an uncaught one exits 1, the "violations found"
code, and an unreadable input becomes indistinguishable from a real verdict.
The lint must exit 2 here.
"""


def test_cart_totals_zero_when_empty():
    assert 0 == 0  # latin-1 tail: café ÿþ

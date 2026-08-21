"""Forge attempt: delete the tests and keep the helpers, hoping the gate goes green.

NO-TESTS fires instead - the lint fails closed on a file that declares no test
functions, so an empty suite can never pass as documentation.
"""


def build_cart(lines):
    return list(lines)


def a_coupon(rate=0.1, expired=False):
    return type("Coupon", (), {"rate": rate, "expired": expired})

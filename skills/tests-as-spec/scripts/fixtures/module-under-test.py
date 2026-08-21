"""Fixture: the module the two suites below describe. Parsed, never imported."""


class Cart:
    def __init__(self, lines=()):
        self.lines = list(lines)

    def total(self):
        return sum(qty * price for _, qty, price in self.lines)


def render_invoice_line(name, qty, price):
    return f"{name} x{qty} @ {price:.2f}"


def apply_coupon(cart, coupon):
    if coupon.expired:
        raise ValueError("coupon expired")
    return cart.total() * (1 - coupon.rate)

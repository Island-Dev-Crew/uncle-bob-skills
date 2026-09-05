"""Fixture: the MISSING verdict alone, with nothing beside it to fire.

Syntactically valid on purpose. One exported def carries no comment at all; the other
carries a full interface comment that neither leaks nor restates, and every declared name
reaches a def. So the exit 1 this file produces rests on MISSING and on no other verdict:
silence that one emission in the lint and this file prints green. That is what makes its
proof row evidence about MISSING rather than about whichever neighbour fired alongside it.
"""

__all__ = ["settle", "price"]


def settle(trade):
    return 0


def price(trade):
    """Return the settlement amount for trade in minor units, raising KeyError when unknown."""
    return 0

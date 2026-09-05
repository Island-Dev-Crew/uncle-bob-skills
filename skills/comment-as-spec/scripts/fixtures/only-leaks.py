"""Fixture: the LEAKS verdict alone, with nothing beside it to fire.

Syntactically valid on purpose. Both exported defs carry a comment, and one of them names
implementation in a single enforced phrasing — 'under the hood' — while adding words the
symbol name never carried, so it cannot fire RESTATES instead. Every declared name reaches
a def. The exit 1 here therefore rests on LEAKS and on no other verdict: silence that one
emission in the lint and this file prints green.
"""

__all__ = ["settle", "price"]


def settle(trade):
    """Return the amount owed on trade in minor units; under the hood it nets the day's positions."""
    return 0


def price(trade):
    """Return the settlement amount for trade in minor units, raising KeyError when unknown."""
    return 0

"""Fixture: the RESTATES verdict alone, with nothing beside it to fire.

Syntactically valid on purpose. Both exported defs carry a comment, and one of them is the
comment Martin is right about — 'Parses a row.' over parse_row — adding no word the name did
not already carry and naming no implementation, so LEAKS stays silent. Every declared name
reaches a def. The exit 1 here therefore rests on RESTATES and on no other verdict: silence
that one emission in the lint and this file prints green.
"""

__all__ = ["parse_row", "price"]


def parse_row(row):
    """Parses a row."""
    return tuple(row)


def price(trade):
    """Return the settlement amount for trade in minor units, raising KeyError when unknown."""
    return 0

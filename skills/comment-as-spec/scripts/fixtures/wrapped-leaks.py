"""Fixture: the leak vocabulary read across a line break and around a zero-width char.

Syntactically valid on purpose. Every comment here is a normal, well-wrapped docstring
that names implementation in one of the eight enforced phrasings — but the phrase is
split by the line wrap any formatter or author produces, or by a U+FEFF posted inside it.
Matching the raw string would print green over all four, so the comment is folded to one
line-shape (whitespace collapsed, NFKC, format characters dropped) before the vocabulary
reads it. The words themselves are untouched.
"""

__all__ = ["scan", "read_all", "settle", "price"]


def scan(rows):
    """Return every parsed row in file order; the caller owns the list. Under the
    hood it batches, and that may change without notice.
    """
    return rows


def read_all(store):
    """Return every row the store holds, in write order. The batching is an implementation
    detail no caller may depend on.
    """
    return []


def settle(trade):
    """Return the amount owed on trade in minor units. Behind the
    scenes it nets against the day's positions.
    """
    return 0


def price(trade):
    """Return the settlement amount for trade in minor units, walking each leg with a
    for﻿-loop over the day's positions.
    """
    return 0

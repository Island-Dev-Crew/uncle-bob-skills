"""Fixture: an __all__ no static read can reduce to a fixed list of names.

Syntactically valid on purpose. The surface is computed at import time, so the lint
cannot know what this module exports. Falling back to the module-level rule here
would print a green exit over a one-name surface that is not the real one — so the
only honest verdict is exit 2, the same fail-closed answer an empty surface gets.
"""

_PUBLIC = ["read_all", "_settle"]

__all__ = list(_PUBLIC)


def read_all(store):
    """Return every row the store holds, in write order, as a list the caller owns.

    Raises KeyError when the store has been closed.
    """
    return []


def _settle(trade):
    return 0

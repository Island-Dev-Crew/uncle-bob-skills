"""Fixture: a surface split across statements — the standard package idiom.

Syntactically valid on purpose. __all__ is built by a '+' concatenation and then a
'+=' extension, so a lint that reads only the first plain literal would see a
one-name surface and never judge the rest. Its comments also carry the two
commonest spellings of a named private symbol: a dotted attribute and a
name-mangled helper.
"""

__all__ = ["read_all"] + ["scan"]
__all__ += ["settle"]


def read_all(store):
    """Return every row the store holds, drained from store._pending_rows first,
    then from the on-disk segment files in write order."""
    return []


def scan(rows):
    """Walk rows with a for-loop, delegating each to __parse_row before yielding."""
    return rows


def settle(trade):
    return 0


def not_exported(value):
    return value

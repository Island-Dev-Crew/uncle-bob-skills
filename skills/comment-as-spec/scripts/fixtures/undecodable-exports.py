"""Fixture: a source this lint cannot decode as UTF-8.

The interface comment below carries one raw 0xff byte, so reading the file raises
UnicodeDecodeError before any surface can be read. An unreadable source is an IO
condition, never a verdict, so it must exit 2 and never 1.
"""

__all__ = ["read_all"]


def read_all(store):
    """Return every row the store holds, in write order: ÿ bytes the caller owns."""
    return []

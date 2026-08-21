"""Fixture: definitions bound inside a block that runs in the enclosing scope.

Syntactically valid on purpose. Every public name here exists at runtime — check with
[n for n in dir(m.Engine) if not n.startswith('_')] → ['flush', 'price', 'rollback'] —
and a lint that walks only the direct children of a class body, or only handles the
version-gate shape at module scope, prints green over three of them. The gated method's
comment also names a private symbol spelled with capitals, which is a private symbol to
the interpreter and so is one to the leak vocabulary.
"""
import contextlib
import sys

__all__ = ["Engine", "warmup"]


class Engine:
    """A caller-facing pricing engine addressed by trade id, safe across restarts."""

    def price(self, trade):
        """Return the settlement amount for trade in minor units, raising KeyError when unknown."""
        return 0

    if sys.version_info >= (3, 8):

        def rollback(self, trade):
            return None

    try:

        def flush(self):
            """Write pending rows out in _MAX_ROWS-sized segments and return the sequence number."""
            return None

    except Exception:
        pass


with contextlib.suppress(ImportError):

    def warmup(store):
        return store

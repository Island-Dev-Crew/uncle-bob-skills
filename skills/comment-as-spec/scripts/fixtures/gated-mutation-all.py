"""Fixture: __all__ mutated in place inside a block, not at the top of the module body.

Syntactically valid on purpose. The surface really is two names at runtime, but only one
of them can be read from a literal, so the lint must fail closed here exactly as it does
on a computed __all__ — a mutation check that scanned only the top level of the module
body would print a green one-name verdict over a surface it never read.
"""
import sys

__all__ = ["documented"]

if sys.version_info >= (3, 8):
    __all__.extend(["hidden"])


def documented(x):
    """Return x scaled to the caller's unit, raising ValueError on a negative x."""
    return x


def hidden(x):
    return x

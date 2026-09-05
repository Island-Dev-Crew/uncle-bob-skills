"""Fixture: the UNJUDGED verdict alone, with nothing beside it to fire.

Syntactically valid on purpose. __all__ declares one name bound to an import — the
re-export shape this lint reports but cannot judge — beside one def with a full interface
comment. Nothing here is missing, leaks or restates, so the exit 1 rests on UNJUDGED and on
no other verdict: silence that one emission in the lint and this file prints green over a
declared name the lint never judged, the package-facade escape restored.
"""
from json import JSONDecoder

__all__ = ["JSONDecoder", "price"]


def price(trade):
    """Return the settlement amount for trade in minor units, raising KeyError when unknown."""
    return 0

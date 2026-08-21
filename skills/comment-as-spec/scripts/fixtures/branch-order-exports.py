"""Fixture: one exported name bound in two branches of a gate, in both orders.

Syntactically valid on purpose. Exactly one branch of each gate runs and static reading
cannot know which, so every def a public name can hold has to be judged. A walk that kept
one binding per name would let branch ORDER decide the verdict: 'warmup' hides its
undocumented def in the FIRST branch and 'settle' hides its in the second, so a lint that
keeps only the last binding prints green over one of them and red over the other.
"""
import sys

__all__ = ["warmup", "settle"]


if sys.version_info < (3, 11):

    def warmup(store):
        return store

else:

    def warmup(store):
        """Prime store's cache and return it, raising OSError when the store is unreachable."""
        return store


if sys.version_info < (3, 11):

    def settle(trade):
        """Return the amount owed on trade in minor units, raising KeyError when unknown."""
        return 0

else:

    def settle(trade):
        return 0

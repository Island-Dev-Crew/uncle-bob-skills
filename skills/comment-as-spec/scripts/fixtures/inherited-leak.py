"""Cache module — an inherited comment that leaks implementation.

The mixin's method is public on the subclass, and its comment describes internals a
caller must not depend on. Moving a leaking member into a base must not hide the leak.
"""
__all__ = ["Engine"]


class _CacheMixin:
    def warm(self):
        """Internally walks _pending_rows in a for loop under the hood."""
        return 1


class Engine(_CacheMixin):
    """Settlement engine for one trading day; construct one per session and close it."""

"""Settlement engine module — the extract-a-base-class shape.

The exported class documents itself but inherits two undocumented public methods.
A caller holding an Engine() sees Engine.price and Engine.settle, so both are part
of the exported interface and must carry an interface comment.
"""
__all__ = ["Engine"]


class BaseEngine:
    def price(self, order):
        return 0

    def settle(self, order):
        return 0


class Engine(BaseEngine):
    """Settlement engine for one trading day; construct one per session and close it."""

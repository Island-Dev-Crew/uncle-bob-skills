"""Fixture: the package-facade shape — an __all__ whose names are not all defs.

Syntactically valid on purpose. Three of its four exported names never reach a
def or class the lint can judge, and the fourth reaches one only through a
module-level alias. This is the default shape of every __init__.py, and it must
not be able to pass by being invisible.
"""
from json import JSONDecoder

__all__ = ["RiskEngine", "JSONDecoder", "PORT", "settle_trade"]

PORT = 8080


class _Engine:
    def price(self, trade):
        return 0


RiskEngine = _Engine

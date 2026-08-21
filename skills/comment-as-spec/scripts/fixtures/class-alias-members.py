"""Fixture: public class attributes bound by ALIAS inside a class body.

Syntactically valid on purpose. Every public name here exists at runtime — check with
[n for n in dir(m.Engine) if not n.startswith('_')] -> ['render', 'warm', 'wrapped'] —
and a class walk that reads only 'def' statements prints green over all three, the exact
false green the module-level walk had before it followed aliases. 'render' aliases a
private def defined at MODULE scope; 'warm' aliases a different private def in each
branch of a version gate, so judging only the last binding would let branch order decide.

'wrapped' is the stated limit, captured here as a run rather than as a sentence: its
value is a CALL, not a name, so it reaches no definition this lint follows and never
appears below — out of the surface for the same reason 'Engine = make_engine()' is at
module scope, and the printed count is what says so.
"""
import sys

__all__ = ["Engine"]


def _render(order, template):
    return template


class Engine:
    """A caller-facing pricing engine addressed by trade id, safe across restarts."""

    def _warm_fast(self, cfg):
        return None

    def _warm_slow(self, cfg):
        """Prime the cache described by cfg and return None, raising OSError when the store is unreachable."""
        return None

    render = _render

    if sys.version_info >= (3, 12):
        warm = _warm_fast
    else:
        warm = _warm_slow

    wrapped = staticmethod(_render)

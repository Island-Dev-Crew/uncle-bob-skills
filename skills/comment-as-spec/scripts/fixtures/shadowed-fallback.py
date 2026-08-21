"""Fixture: the same shadowing under the fallback rule, in a module with no __all__.

Syntactically valid on purpose. 'warmup' is a public module-level def name that a walk
keeping only the LAST binding loses outright — the 'except:' import overwrites it and the
name drops out of the surface and the count, not merely out of the verdicts. 'render' is
the mixed case: a def in one branch, an alias to a documented private def in the other,
where following the alias alone prints green over an undocumented public function.
Neither shape is exotic — one is an optional-dependency fallback, the other a flag.
"""
FAST = True


def _fallback_render(order, template):
    """Return the invoice text for order, formatted with template; raises KeyError on an unknown line item."""
    return template


try:

    def warmup(store):
        return store

except ImportError:
    from _fast import warmup


if FAST:

    def render(order, template):
        return template

else:
    render = _fallback_render

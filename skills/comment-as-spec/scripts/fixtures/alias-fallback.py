"""Fixture: a public export bound by alias, in a module that declares no __all__.

Syntactically valid on purpose. Deleting __all__ used to be a one-line move that hid an
export from the gate: 'render_invoice = _render_invoice' is a public module-level name at
runtime — check with [n for n in dir(m) if not n.startswith('_')] — and the fallback rule
walked defs only. The bare 'import sys', the imported JSONDecoder and the PORT constant
stay out of this surface on purpose: the fallback judges definitions and the public names
that reach them, a narrowing named in the island's advisory section rather than hidden.
"""
import sys
from json import JSONDecoder

PORT = 8080


def documented(x):
    """Return x scaled to the caller's unit, raising ValueError on a negative x."""
    return x


def _render_invoice(order, template):
    return template


render_invoice = _render_invoice

decode_payload = JSONDecoder

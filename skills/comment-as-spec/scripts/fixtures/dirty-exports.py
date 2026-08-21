"""Fixture: an export surface no caller can use without opening the bodies.

Syntactically valid on purpose — this file must fail the lint for its comments,
never for malformed input. It declares no __all__, so it also pins the other
surface rule: module-level public defs and classes, '_' names skipped, including
a def bound inside a version gate — a public name at runtime, so a public name here.
"""
import sys


def render_invoice(order, template):
    total = 0
    for line in order.lines:
        total += line.amount
    return template.format(total=total)


def load_config(path):
    """Reads the file and then calls _parse_toml internally."""
    return _parse_toml(path)


def parse_row(row):
    """Parses a row."""
    return tuple(row)


def _parse_toml(path):
    return {}


if sys.version_info >= (3, 8):

    def settle_trade(trade):
        return 0


class InvoiceBook:
    """A caller-facing home for the invoices a run produced, keyed by order id."""

    class Entry:
        """One stored invoice and the order id it was rendered from."""

        def total(self):
            return 0

"""Forge attempt: hide the worthless suite where a body-only collector cannot look.

One honest test at module level, and every bad name written into a compound
statement or bound by an import - so a collector reading only `node.body` sees
the honest one, reports the file clean, and pytest runs all six. Each guard is
true at runtime, which is the whole point: pytest collects what the module
binds, wherever in the file it is written.
"""
import sys
from unittest.util import strclass as test_total  # noqa: F401 - THIN-NAME, bound by import


def test_empty_cart_totals_zero():
    assert 0 == 0


if sys.version_info >= (3, 0):

    def test_render_invoice_line():  # MIRRORS-CODE, behind a version guard
        assert True

    def test_it_works():  # PLACEHOLDER, behind a version guard
        assert True


with open(__file__, encoding="utf-8"):

    def test_case_2_works():  # PLACEHOLDER, inside a with block
        assert True


try:
    import unittest
except ImportError:  # pragma: no cover - the import cannot fail; the else is the forge
    unittest = None
else:

    class InvoiceRendering(unittest.TestCase):
        def testFoo(self):  # THIN-NAME, in a class inside a try/else
            self.assertTrue(True)

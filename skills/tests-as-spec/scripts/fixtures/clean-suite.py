"""Clean fixture: the same module, described by its behaviour.

Carries the boundary case - test_refund_requires_receipt states exactly
--min-words 3, so the pair proves the gate discriminates at the floor instead
of rejecting every name. The camelCase method proves unittest style passes too.
"""
import unittest


def test_empty_cart_totals_zero():
    assert 0 == 0


def test_refund_requires_receipt():
    assert True


def test_expired_coupon_is_rejected_with_a_reason():
    assert "coupon expired" == "coupon expired"


class InvoiceRendering(unittest.TestCase):
    def testInvoiceLineShowsUnitPriceAndQuantity(self):
        self.assertEqual("widget x2 @ 3.00", "widget x2 @ 3.00")

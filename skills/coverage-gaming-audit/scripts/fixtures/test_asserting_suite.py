"""KNOWN-CLEAN fixture — the boundary cases the scanner must NOT flag.

Every test here asserts on the code under test, in a different idiom each time,
so the pair proves the scanner discriminates rather than rejecting everything.
Parsed by ast, never executed.
"""
import sys
import unittest

import pytest
from pytest import raises

from billing import charge_card, render_invoice, load_receipt
from billing import ReceiptMissing as Missing


def test_total_rounds_half_up():
    # Plain assert statement.
    assert render_invoice({"items": [10, 5], "tax": 0.1}).total == 17


def test_rejects_negative_amount():
    # pytest.raises IS an assertion — the exception is the observed behaviour.
    with pytest.raises(ValueError):
        render_invoice({"items": [-1], "tax": 0.0})


def test_rejects_empty_items():
    # The same assertion through a bare `from pytest import raises` binding.
    with raises(ValueError):
        render_invoice({"items": [], "tax": 0.0})


def test_charge_card_returns_receipt(mocker):
    # A mock assertion is fine when a real one stands beside it.
    gateway = mocker.Mock()
    receipt = charge_card(gateway, amount=1200)
    gateway.charge.assert_called_once_with(1200)
    assert receipt.status == "settled"


def test_charge_card_records_and_settles(mocker):
    # A mock-OBSERVATION assert is fine when a real one stands beside it.
    gateway = mocker.Mock()
    receipt = charge_card(gateway, amount=1200)
    assert gateway.charge.call_count == 1
    assert receipt.total == 1200


def test_missing_receipt_falls_back():
    # A NARROW handler with an empty body is cleanup, not a swallow.
    try:
        load_receipt("/nonexistent/receipt.json")
    except FileNotFoundError:
        pass
    assert load_receipt.cache_misses == 1


def test_retry_reraises_after_logging():
    # A BROAD handler that re-raises can still turn the test red.
    try:
        assert charge_card(None, amount=1) is None
    except Exception:
        raise


def test_narrow_handler_renamed_at_import():
    # A NARROW class renamed at import is still narrow — resolving bindings must
    # not blanket-flag every aliased handler.
    try:
        load_receipt("/nonexistent/receipt.json")
    except Missing:
        pass
    assert load_receipt.cache_misses == 2


def test_expected_total_from_a_literal_local(mocker):
    # A literal hoisted into a local is fine when the assertion still reads a
    # REAL value — dropping constant names must not blanket-flag every local.
    expected = 1200
    receipt = charge_card(mocker.Mock(), amount=1200)
    assert receipt.total == expected


def test_total_read_into_a_local(mocker):
    # The local holds a value the code under test produced, so it is a real
    # observation however it is named.
    receipt = charge_card(mocker.Mock(), amount=1200)
    total = receipt.total
    assert total == 1200


def test_charge_card_must_not_raise(mocker):
    # A broad handler asserting a constant FALSE always turns the test red, so
    # it propagates — the tautology rule must reject only constant-TRUE bodies.
    gateway = mocker.Mock()
    try:
        receipt = charge_card(gateway, amount=1200)
    except Exception:
        assert False, "charge_card must not raise on a valid amount"
    assert receipt.status == "settled"


def test_recorder_suppress_is_not_contextlib(mocker):
    # `.suppress()` on an arbitrary object is not contextlib's, exactly as
    # `.raises()` on an arbitrary object is not pytest's.
    recorder = mocker.Mock()
    with recorder.suppress(Exception):
        receipt = charge_card(recorder, amount=1200)
    assert receipt.total == 1200


def test_hoisted_observation_beside_a_real_one(mocker):
    # A mock observation hoisted into a local is still only a mock observation —
    # but one real assertion beside it keeps the test honest, exactly as the
    # inline form does. Carrying tips through names must not flag every local.
    gateway = mocker.Mock()
    receipt = charge_card(gateway, amount=1200)
    seen = gateway.charge.called
    assert seen
    assert receipt.total == 1200


class TestInvoiceEdges(unittest.TestCase):
    def test_zero_items_is_zero(self):
        # unittest idiom — self.assertEqual counts as a real assertion.
        self.assertEqual(render_invoice({"items": [], "tax": 0.2}).total, 0)


class TestInvoiceConstants(unittest.TestCase):
    # A class-body literal is a legitimate place to keep an EXPECTED value.
    EXPECTED_TOTAL = 17

    def test_total_matches_a_class_constant(self):
        # Dropping `self.EXPECTED_TOTAL` must leave the REAL observation standing.
        self.assertEqual(render_invoice({"items": [10, 5], "tax": 0.1}).total,
                         self.EXPECTED_TOTAL)

    def test_charge_card_must_not_raise_via_fail(self):
        # `self.fail(...)` always raises, so a broad handler around it can still
        # go red — the tautology rule must not reject every literal-argument call.
        try:
            receipt = charge_card(unittest.mock.Mock(), amount=1200)
        except Exception:
            self.fail("charge_card must not raise on a valid amount")
        self.assertEqual(receipt.total, 1200)


if sys.version_info >= (3, 8):
    # Collected from inside a version guard, and clean — the widened traversal
    # must scan it, not flag it.
    def test_guarded_total_is_asserted():
        assert render_invoice({"items": [7], "tax": 0.0}).total == 7

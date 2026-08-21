"""KNOWN-DIRTY fixture — every test here executes code and proves nothing.

Each function drives coverage on `billing` while asserting nothing about it, so
a coverage report over this suite reads 100% and a CRAP score reads green.
One case per gaming shape, including the idiom swaps an agent in a
fix-until-green loop reaches for first — a renamed import, a def behind a
version guard, an expected value hoisted into a local or a class body, the
observation hoisted instead of the expected value, a tautology in the handler
that is not a bare `True`. The scanner must find all thirty-four.
Parsed by ast, never executed.
"""
import builtins
import contextlib
import sys
import unittest
from builtins import Exception as Boom
from contextlib import suppress
from contextlib import suppress as quiet

import pytest  # noqa: F401  (import shape only; this file is never run)

from billing import charge_card, render_invoice, retry

EXPECTED_CALLS = 1  # a module-level literal is no more a real value than an inline one


def _invariant(invoice):
    """Not a test function — the scanner must ignore this, assertion and all."""
    assert invoice.total >= 0


def test_render_invoice_runs():
    # NO-ASSERTION — calls the code, inspects nothing.
    invoice = render_invoice({"items": [1, 2, 3], "tax": 0.09})
    print(invoice)


def test_charge_card_calls_gateway(mocker):
    # MOCK-ONLY — the mock's own assert method.
    gateway = mocker.Mock()
    charge_card(gateway, amount=1200)
    gateway.charge.assert_called_once_with(1200)


def test_charge_card_poked_the_double(mocker):
    # MOCK-ONLY — same claim as an assert statement on `.called`.
    gateway = mocker.Mock()
    charge_card(gateway, amount=1200)
    assert gateway.charge.called


def test_charge_card_call_args_shape(mocker):
    # MOCK-ONLY — an assert statement comparing `.call_args` to a literal.
    gateway = mocker.Mock()
    charge_card(gateway, amount=1200)
    assert gateway.charge.call_args == ((1200,), {})


def test_charge_card_call_args_via_local(mocker):
    # MOCK-ONLY — the same claim with the literal hoisted into a local. Naming a
    # constant is the cheapest idiom swap there is; it must not launder the verdict.
    gateway = mocker.Mock()
    charge_card(gateway, amount=1200)
    expected = ((1200,), {})
    assert gateway.charge.call_args == expected


def test_charge_card_called_flag_via_local(mocker):
    # MOCK-ONLY — `assert gw.charge.called` rewritten against a named True.
    gateway = mocker.Mock()
    charge_card(gateway, amount=1200)
    yes = True
    assert gateway.charge.called == yes


def test_charge_card_call_args_via_rebound_param(mocker, expected):
    # MOCK-ONLY — the same hoist one step further along: a fixture parameter
    # overwritten with the literal is still a literal at the assertion.
    gateway = mocker.Mock()
    charge_card(gateway, amount=1200)
    expected = ((1200,), {})
    assert gateway.charge.call_args == expected


def test_charge_card_count_via_module_const(mocker):
    # MOCK-ONLY — the same hoist one scope further out, to a module constant.
    gateway = mocker.Mock()
    charge_card(gateway, amount=1200)
    assert gateway.charge.call_count == EXPECTED_CALLS


def test_charge_card_call_args_via_hoisted_observation(mocker):
    # MOCK-ONLY — the mirror hoist: the OBSERVATION moved into a local. The value
    # chain still terminates in `.call_args`; only the wording changed.
    gateway = mocker.Mock()
    charge_card(gateway, amount=1200)
    actual = gateway.charge.call_args
    assert actual == ((1200,), {})


def test_charge_card_called_via_hoisted_observation(mocker):
    # MOCK-ONLY — `.called` read into a local and asserted bare.
    gateway = mocker.Mock()
    charge_card(gateway, amount=1200)
    was_called = gateway.charge.called
    assert was_called


def test_charge_card_count_via_hoisted_observation(mocker):
    # MOCK-ONLY — `.call_count` read into a local, then compared to a literal.
    gateway = mocker.Mock()
    charge_card(gateway, amount=1200)
    n = gateway.charge.call_count
    assert n == 1


def test_charge_card_called_via_walrus(mocker):
    # MOCK-ONLY — the same hoist written inline as an assignment expression.
    gateway = mocker.Mock()
    charge_card(gateway, amount=1200)
    assert (seen := gateway.charge.called)


def test_retry_never_fails():
    # SWALLOWED — the broad handler eats every failure, assertion included.
    try:
        assert retry(lambda: 1 / 0, attempts=3) == 1
    except Exception:
        pass


def test_retry_swallows_with_tautology():
    # SWALLOWED — `assert True` is one token off `pass` and just as unable to
    # turn the test red, so it does not rescue the handler.
    try:
        assert retry(lambda: 1 / 0, attempts=3) == 1
    except Exception:
        assert True


def test_retry_swallows_with_named_tautology():
    # SWALLOWED — the same tautology behind a name bound to a literal.
    ok = True
    try:
        assert retry(lambda: 1 / 0, attempts=3) == 1
    except Exception:
        assert ok


def test_retry_swallows_with_negated_false():
    # SWALLOWED — `not False` is one token off `True` and just as unfailable.
    try:
        assert retry(lambda: 1 / 0, attempts=3) == 1
    except Exception:
        assert not False


def test_retry_swallows_with_arithmetic_tautology():
    # SWALLOWED — an arithmetic constant no run can turn red.
    try:
        assert retry(lambda: 1 / 0, attempts=3) == 1
    except Exception:
        assert 1 + 1


def test_retry_swallows_with_boolop_tautology():
    # SWALLOWED — a short-circuiting `or` whose first operand settles it.
    try:
        assert retry(lambda: 1 / 0, attempts=3) == 1
    except Exception:
        assert True or charge_card


def test_retry_swallows_via_dotted_suppress():
    # SWALLOWED — suppress reached through the contextlib module alias.
    with contextlib.suppress(Exception):
        assert retry(lambda: 1 / 0, attempts=3) == 1


def test_retry_swallows_by_returning():
    # SWALLOWED — `return` instead of `pass`: one token, same eaten failure.
    try:
        assert retry(lambda: 1 / 0, attempts=3) == 1
    except Exception:
        return


def test_retry_swallows_by_logging():
    # SWALLOWED — a logging body still cannot turn the test red.
    try:
        assert retry(lambda: 1 / 0, attempts=3) == 1
    except Exception as e:
        print(e)


def test_retry_swallows_via_dotted_alias():
    # SWALLOWED — the broad class reached through a module attribute.
    try:
        assert retry(lambda: 1 / 0, attempts=3) == 1
    except builtins.Exception:
        pass


def test_retry_swallows_via_suppress():
    # SWALLOWED — contextlib.suppress, with no except handler to find.
    with suppress(Exception):
        assert retry(lambda: 1 / 0, attempts=3) == 1


def test_retry_swallows_via_aliased_suppress():
    # SWALLOWED — the same suppress renamed at import; a one-token idiom swap.
    with quiet(Exception):
        assert retry(lambda: 1 / 0, attempts=3) == 1


def test_retry_never_fails_aliased_class():
    # SWALLOWED — the broad class renamed at import; resolved by binding.
    try:
        assert retry(lambda: 1 / 0, attempts=3) == 1
    except Boom:
        pass


def test_callback_checks_the_total():
    # NO-ASSERTION — the assertion lives in a nested def that is never called.
    def _check(result):
        assert result.total == 42

    render_invoice({"items": [42], "tax": 0.0})


def test_raises_on_a_random_object():
    # NO-ASSERTION — a `.raises()` method on some object is not pytest.raises.
    fake = object()
    charge_card(fake, amount=1)
    fake.raises(ValueError)


class GatewayCase(unittest.TestCase):
    """A shared base — not a test class, but its literals travel to subclasses."""

    EXPECTED_CALLS = 1


class TestGatewayCallCount(unittest.TestCase):
    def test_call_count_only(self):
        # MOCK-ONLY — the unittest idiom, still asserting only on the double.
        gateway = unittest.mock.Mock()
        charge_card(gateway, amount=1200)
        self.assertEqual(gateway.charge.call_count, 1)

    def test_call_count_via_hoisted_local(self):
        # MOCK-ONLY — the observation hoist inside the unittest idiom.
        gateway = unittest.mock.Mock()
        charge_card(gateway, amount=1200)
        n = gateway.charge.call_count
        self.assertEqual(n, 1)


class TestGatewayClassConst(unittest.TestCase):
    # MOCK-ONLY ×2 — the expected literal hoisted into the CLASS body, which is
    # where the unittest idiom puts it. A class constant is no more a real value
    # than a module one.
    EXPECTED_CALLS = 1
    EXPECTED_ARGS = ((1200,), {})

    def test_call_count_via_class_const(self):
        gateway = unittest.mock.Mock()
        charge_card(gateway, amount=1200)
        self.assertEqual(gateway.charge.call_count, self.EXPECTED_CALLS)

    def test_call_args_via_class_const(self):
        gateway = unittest.mock.Mock()
        charge_card(gateway, amount=1200)
        assert gateway.charge.call_args == self.EXPECTED_ARGS


class TestGatewayBaseConst(GatewayCase):
    def test_call_count_via_base_class_const(self):
        # MOCK-ONLY — the same hoist one class further out, onto a shared base.
        gateway = unittest.mock.Mock()
        charge_card(gateway, amount=1200)
        self.assertEqual(gateway.charge.call_count, self.EXPECTED_CALLS)


class TestRetryUnittestIdioms(unittest.TestCase):
    def test_retry_swallows_with_unittest_tautology(self):
        # SWALLOWED — `self.assertTrue(True)` is `assert True` in the unittest
        # costume, and rescues the handler exactly as little.
        try:
            assert retry(lambda: 1 / 0, attempts=3) == 1
        except Exception:
            self.assertTrue(True)


if sys.version_info >= (3, 8):
    # NO-ASSERTION — pytest collects a def behind a version guard; so must the
    # scanner, or a partial scan certifies the tests it never read.
    def test_charge_card_runs_guarded():
        charge_card(object(), amount=1200)

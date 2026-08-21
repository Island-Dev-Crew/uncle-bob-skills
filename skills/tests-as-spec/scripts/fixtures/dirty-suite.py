"""Dirty fixture: a suite that teaches a fresh context nothing.

Valid Python on purpose - the lint must go red on the NAMES, not on a parse
error. One violation of each kind, in order: MIRRORS-CODE, PLACEHOLDER,
THIN-NAME, DUPLICATE.
"""


def test_render_invoice_line():
    assert "widget x2 @ 3.00" == "widget x2 @ 3.00"


def test_case_2_works():
    assert True


def test_total():
    assert 0 == 0


def test_cart_totals_zero_when_empty():
    assert 0 == 0


def test_cart_totals_zero_when_empty():  # noqa: F811 - the point of the fixture
    assert 1 == 1

"""Forge attempt: the dirty suite laundered by DELETING THE UNDERSCORES.

The same four worthless tests as dirty-suite.py, renamed so that any collector
narrower than pytest's own `python_functions = test*` skips them and reports the
file clean. pytest collects all of them, so the lint must see all of them.
The trailing `test_1` is the second forge - a module-level binding, not a def.
"""


def testrenderinvoiceline():
    assert "widget x2 @ 3.00" == "widget x2 @ 3.00"


def testcase2works():
    assert True


def testtotal():
    assert 0 == 0


def test_cart_totals_zero_when_empty():
    assert 0 == 0


test_1 = testtotal

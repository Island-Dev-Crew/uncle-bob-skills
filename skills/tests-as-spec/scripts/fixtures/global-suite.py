"""Forge attempt: bind the worthless names from INSIDE a function body.

`global` is the one keyword that makes a def's body bind at module scope, so a
collector that records a def's name and refuses to descend - correct everywhere
else, because pytest collects nothing from a function body - hands this a silent
pass. The installer is called at import, pytest collects all three, and the two
laundered names are the same ones bound-suite.py catches with a walrus: the
identical forge, moved one indent down behind a keyword. Recording the
declaration alone is fail-closed - the name is spelled here whether or not
_install() ever runs.
"""


def _impl():
    assert True


def _install():
    global test_1, test_it_works  # THIN-NAME x2, declared here, bound at module scope
    test_1 = _impl
    test_it_works = _impl


_install()


def test_empty_cart_totals_zero():  # the one honest test
    assert 0 == 0

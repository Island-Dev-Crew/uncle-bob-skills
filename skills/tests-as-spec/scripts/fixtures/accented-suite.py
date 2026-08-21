"""Forge attempt: launder the dirty names through ACCENTED respellings.

Three names from dirty-suite.py, respelled with diacritics so that a comparison
keyed on raw ASCII words misses its join: the filler set never sees "works",
and MIRRORS-CODE never sees "render". pytest collects all four regardless -
identifiers are just identifiers to it. `test_tötal` is written DECOMPOSED
(NFD) on disk, so the file also proves the two Unicode forms key alike: CPython
NFKC-normalizes identifiers at parse time and the lint folds NFKD on top.
"""


def test_bäsic_häppy_päth():  # PLACEHOLDER once folded - basic/happy/path
    assert True


def test_rénder_invoice_line():  # MIRRORS-CODE once folded
    assert True


def test_tötal():  # THIN-NAME once folded - one word
    assert 0 == 0


def test_empty_cart_totals_zero():  # the one honest test
    assert 0 == 0

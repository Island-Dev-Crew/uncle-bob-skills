"""Forge attempt: launder the dirty names through STROKE and LIGATURE letters.

The accented-suite trick again, one step past the fold: ø ł æ œ ß đ are Latin
letters NFKD leaves atomic, so dropping combining marks cannot key them to their
ASCII twins. Worse than a missed join, they SHATTER the word split - `bøsic`
becomes ('b','sic'), neither fragment filler - so four worthless names scored six
behaviour words apiece and the file read clean. pytest collects all four
regardless. The lint now rejects what it cannot read (UNFOLDABLE) instead of
judging it, which is the fail-closed side this fixture exists to hold shut.
"""


def test_bøsic_høppy_pøth():  # UNFOLDABLE - would score b/sic/h/ppy/p/th
    assert True


def test_rønder_invoice_line():  # UNFOLDABLE - MIRRORS-CODE cannot see the join
    assert True


def test_it_wœrks_œk():  # UNFOLDABLE - the filler set cannot see "works"
    assert True


def test_rænder_invoice_line():  # UNFOLDABLE - a second ligature, same shatter
    assert True

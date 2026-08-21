"""Forge attempt: a BOM at byte zero, hoping "cannot parse" replaces the verdict.

CPython strips a UTF-8 BOM from source, so this file is perfectly good Python
with one worthless name in it. A lint that decodes as plain utf-8 sees a literal
U+FEFF, calls it a parse error, and exits 2 - an IO code standing in for a
verdict the gate could have computed. It must exit 1 on the name instead.
"""


def test_1():
    assert True

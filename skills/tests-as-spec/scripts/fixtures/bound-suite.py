"""Forge attempt: bind the worthless names WITHOUT a def and WITHOUT an `=`.

The same worthless names again, this time bound by a walrus, a `for` target, a
`with ... as`, and a `match` capture - four binders that spell a static target
name in the file's own text and that pytest collects exactly like a def. A
collector that knows only defs, assignments and imports reports this file clean
while pytest runs all five. Every binding is live at import time, which is the
point: pytest collects what the module binds, however the module binds it.
"""
import contextlib


def _impl():
    assert True


def test_empty_cart_totals_zero():  # the one honest test
    assert 0 == 0


if (test_render_invoice_line := _impl):  # MIRRORS-CODE, bound by a walrus
    pass

for test_total in (_impl,):  # THIN-NAME, bound by a for target
    pass

with contextlib.nullcontext(_impl) as test_it_works:  # THIN-NAME, bound by with-as
    pass

match [_impl]:
    case [test_case_2_works]:  # PLACEHOLDER, bound by a match capture
        pass

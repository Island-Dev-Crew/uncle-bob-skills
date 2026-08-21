"""Report window — v2, the wrong repair. The out-of-range cases survive
untouched; the change only adds more handling around them, plus one new raise.
Five error paths, up from three.
"""


def slice_window(items, start, end):
    if start < 0 or start > len(items):
        raise IndexError(f"start {start} out of range")
    if end < start or end > len(items):
        raise IndexError(f"end {end} out of range")
    return items[start:end]


def summarize(items, start, end):
    try:
        window = slice_window(items, start, end)
    except IndexError:
        window = []
    except TypeError:
        raise ValueError("items must be a sequence") from None
    return len(window)

"""Report window — v1. Endpoints are validated, so every caller of
slice_window must be prepared for IndexError, and summarize branches on it.
Three error paths: two raise sites and one handler.
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
    return len(window)

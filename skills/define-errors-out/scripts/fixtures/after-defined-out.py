"""Report window — v2, the redesign. Endpoints clamp into the sequence, so
every (start, end) pair is a legal input and the operation is total. The
out-of-range case no longer exists, so neither does anything to catch.
Zero error paths.
"""


def slice_window(items, start, end):
    lo = min(max(start, 0), len(items))
    hi = min(max(end, lo), len(items))
    return items[lo:hi]


def summarize(items, start, end):
    return len(slice_window(items, start, end))

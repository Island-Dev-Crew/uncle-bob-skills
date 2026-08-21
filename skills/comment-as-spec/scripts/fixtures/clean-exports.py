"""Fixture: the same shape of module, usable from its comments alone."""

__all__ = ["load_readings", "open_series", "ReadingStore"]


def load_readings(path, window):
    """Return every Reading in the file at path whose timestamp falls inside window.

    Order follows the file, not the clock. The caller owns the returned list and
    may mutate it. Raises ValueError when the file declares a unit this build
    cannot convert, and FileNotFoundError when path does not exist.
    """
    return _decode(path, window)


def open_series(station):
    """Open the series.

    A PEP 257 summary line that restates the name, over a body that carries the
    contract: station is the id as it appears in the file header. Returns a
    read-only view of that station's Readings in file order, valid until the
    store closes. Raises KeyError when the station has no Readings.
    """
    return ()


def _decode(path, window):
    return []


def not_in_all(value):
    return value


class ReadingStore:
    """A durable, append-only home for Readings, addressed by station id.

    A Reading handed to append is visible to every later reader in the same
    process. Nothing here is safe to share across threads.
    """

    def append(self, reading):
        """Add reading to its station series and return the sequence number a caller quotes to fetch it back."""
        return 0

    class Cursor:
        """A resumable position in one station's series, safe to hand back later.

        A Cursor stays valid across appends and may be quoted to reopen the
        series at the same place after a restart.
        """

        def advance(self):
            """Move to the next Reading and return it, or None once the series is exhausted."""
            return None

    def _flush(self):
        return None

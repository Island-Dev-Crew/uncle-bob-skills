"""Payment intake. The plan's batch extends this module with refunds."""

RETRY_LIMIT = 3


def charge(card, cents):
    """Charge a card. Returns a receipt id."""
    return f"rcpt-{card[-4:]}-{cents}"

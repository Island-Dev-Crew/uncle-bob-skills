"""Payment intake. The plan's batch extends this module with refunds."""

RETRY_LIMIT = 3


def charge_card(card, cents):
    """Charge a card. Returns a receipt id."""
    return f"rcpt-{card[-4:]}-{cents}"


def refund(receipt_id):
    """Another agent already landed this while the plan was still queued."""
    return f"refund-{receipt_id}"

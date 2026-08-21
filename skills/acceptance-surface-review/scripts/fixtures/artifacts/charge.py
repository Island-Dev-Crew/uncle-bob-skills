"""Payment capture - the dangerous path a critical-tier review must open."""


def capture(cart_total_cents, card_token, processor):
    if cart_total_cents <= 0:
        raise ValueError("refusing to capture a non-positive amount")
    receipt = processor.charge(card_token, cart_total_cents)
    return {"status": "paid" if receipt.approved else "payment failed",
            "captured_cents": cart_total_cents if receipt.approved else 0,
            "receipt_id": receipt.id}

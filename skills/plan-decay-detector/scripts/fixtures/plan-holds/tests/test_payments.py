from src.payments import charge


def test_charge_returns_a_receipt():
    assert charge("4242424242424242", 500).startswith("rcpt-")

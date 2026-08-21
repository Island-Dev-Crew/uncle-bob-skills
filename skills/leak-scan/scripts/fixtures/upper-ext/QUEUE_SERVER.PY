"""Server half, saved with an uppercase extension - the same queue name."""

SUBSCRIBED = "payments-inbound"


def drain(bus):
    return bus.receive(SUBSCRIBED)

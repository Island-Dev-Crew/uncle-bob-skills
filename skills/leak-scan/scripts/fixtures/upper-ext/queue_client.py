"""Client half - names the queue the uppercase-extension module also names."""

QUEUE = "payments-inbound"


def enqueue(bus, msg):
    return bus.send(QUEUE, msg)

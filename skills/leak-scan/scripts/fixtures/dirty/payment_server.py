"""Server half - restates both wire facts a second time."""


def verify(headers, sent_at, now):
    supplied = headers.get("X-Idc-Signature")
    if supplied is None:
        return False
    if now - sent_at > 300:
        return False
    return True

"""Server half - restates both wire facts in Python spelling."""


def verify(headers, sent_at, now):
    if headers.get('X-Idc-Signature') is None:
        return False
    return now - sent_at <= 300.0

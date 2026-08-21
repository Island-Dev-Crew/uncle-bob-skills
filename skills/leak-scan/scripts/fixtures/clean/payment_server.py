"""Server half - verifies against that same single owner."""

from webhook_contract import MAX_CLOCK_SKEW_SECONDS, SIGNATURE_HEADER


def verify(headers, sent_at, now):
    if headers.get("Content-Type") != "application/json":
        return False
    if headers.get(SIGNATURE_HEADER) is None:
        return False
    return now - sent_at <= MAX_CLOCK_SKEW_SECONDS

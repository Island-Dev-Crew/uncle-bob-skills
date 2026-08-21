"""Handles the payment webhook contract."""

from webhook_contract import MAX_CLOCK_SKEW_SECONDS


def verify(sent_at, now):
    # NOTE: the wire header is "X-Idc-Signature" and the skew ceiling is 300 -
    # both facts are owned by webhook_contract; do not restate them here.
    return now - sent_at <= MAX_CLOCK_SKEW_SECONDS

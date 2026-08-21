"""Handles the payment webhook contract."""

from webhook_contract import SIGNATURE_HEADER


def sign(digest):
    # NOTE: the wire header is "X-Idc-Signature" and the skew ceiling is 300 -
    # both facts are owned by webhook_contract; do not restate them here.
    return {SIGNATURE_HEADER: digest}

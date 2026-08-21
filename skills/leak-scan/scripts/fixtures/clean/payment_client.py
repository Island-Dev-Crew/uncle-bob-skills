"""Client half - borrows both wire facts from their single owner."""
import hashlib
import hmac

from webhook_contract import MAX_CLOCK_SKEW_SECONDS, SIGNATURE_HEADER


def sign(body, secret):
    digest = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return {SIGNATURE_HEADER: digest, "Content-Type": "application/json"}


def is_fresh(sent_at, now):
    return now - sent_at <= MAX_CLOCK_SKEW_SECONDS

"""Client half of the payment webhook - signs and posts."""
import hashlib
import hmac

SIGNATURE_HEADER = "X-Idc-Signature"


def sign(body, secret):
    digest = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return {SIGNATURE_HEADER: digest}


def is_fresh(sent_at, now):
    return now - sent_at <= 300

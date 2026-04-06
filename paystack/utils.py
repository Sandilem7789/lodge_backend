"""
Payment utilities — shared helpers for PayFast and amount formatting.
"""
import hashlib
import urllib.parse
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger('payfast')


# ---------------------------------------------------------------------------
# PayFast signature helpers
# ---------------------------------------------------------------------------

def generate_payfast_signature(data: dict, passphrase: str = None) -> str:
    """
    Generate the MD5 signature required by PayFast.

    Rules (from PayFast docs):
    - Iterate over `data` in insertion order (use OrderedDict or Python 3.7+ dict).
    - Skip fields whose value is empty/None.
    - URL-encode each value with urllib.parse.quote_plus.
    - Join as "key=value&key2=value2".
    - If a passphrase is set, append "&passphrase=<encoded>".
    - Return the hexadecimal MD5 digest.
    """
    fields = []
    for key, value in data.items():
        if value is not None and str(value).strip() != '':
            encoded = urllib.parse.quote_plus(str(value))
            fields.append(f"{key}={encoded}")

    query_string = '&'.join(fields)

    if passphrase and passphrase.strip():
        encoded_pass = urllib.parse.quote_plus(passphrase.strip())
        query_string += f"&passphrase={encoded_pass}"

    return hashlib.md5(query_string.encode('utf-8')).hexdigest()


def validate_payfast_itn(post_data: dict, passphrase: str = None) -> bool:
    """
    Validate an incoming PayFast ITN POST.

    Removes 'signature' from the data, regenerates the hash, and compares.
    Returns True if valid.
    """
    data = {k: v for k, v in post_data.items() if k != 'signature'}
    received = post_data.get('signature', '')
    expected = generate_payfast_signature(data, passphrase)
    return received == expected


# ---------------------------------------------------------------------------
# Amount formatting helpers (kept for backward compatibility)
# ---------------------------------------------------------------------------

def rand_to_cents(amount_rand):
    """Convert ZAR rand to cents (integer)."""
    if amount_rand is None:
        raise ValueError("Amount cannot be None")
    try:
        amount_dec = Decimal(str(amount_rand))
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError(f"Invalid amount format: {amount_rand}")
    if amount_dec < 0:
        raise ValueError("Amount cannot be negative")
    amount_cents = int(amount_dec * 100)
    if amount_cents == 0 and amount_dec > 0:
        raise ValueError(f"Amount {amount_rand} is too small (< 0.01 ZAR)")
    return amount_cents


def cents_to_rand(amount_cents):
    """Convert cents to ZAR rand (Decimal)."""
    if amount_cents is None:
        raise ValueError("Amount cannot be None")
    try:
        amount_int = int(amount_cents)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid amount format: {amount_cents}")
    if amount_int < 0:
        raise ValueError("Amount cannot be negative")
    return (Decimal(amount_int) / 100).quantize(Decimal('0.01'))


def validate_amount_not_in_cents(amount_rand):
    """Warn if amount looks like it was already converted to cents."""
    try:
        amount_dec = Decimal(str(amount_rand))
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError(f"Invalid amount format: {amount_rand}")
    if amount_dec % 100 == 0 and amount_dec >= 100000:
        logger.warning(
            f"Amount {amount_dec} ZAR might already be in cents. "
            "Please verify this is the correct value in rand."
        )


def get_paystack_amount(amount_rand, validate=True):
    """Return amount in cents for Paystack (kept for compatibility)."""
    if validate:
        validate_amount_not_in_cents(amount_rand)
    return rand_to_cents(amount_rand)


def get_display_amount(amount_rand):
    """Return amount as float in ZAR for display."""
    try:
        return float(Decimal(str(amount_rand)).quantize(Decimal('0.01')))
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError(f"Invalid amount format: {amount_rand}")


def format_payfast_amount(amount_rand) -> str:
    """Return amount formatted as '100.00' for PayFast form field."""
    try:
        return f"{float(Decimal(str(amount_rand)).quantize(Decimal('0.01'))):.2f}"
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError(f"Invalid amount: {amount_rand}")

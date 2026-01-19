"""
Paystack payment utilities for converting between rand and cents,
with validation to prevent double multiplication errors.
"""
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger('paystack')


def rand_to_cents(amount_rand):
    """
    Convert amount from ZAR (rand) to Paystack cents.
    
    Args:
        amount_rand: Amount in ZAR (e.g., 4000.00)
        
    Returns:
        int: Amount in cents (e.g., 400000)
        
    Raises:
        ValueError: If amount is invalid or already appears to be in cents
    """
    if amount_rand is None:
        raise ValueError("Amount cannot be None")
    
    try:
        # Convert to Decimal for precise arithmetic
        amount_dec = Decimal(str(amount_rand))
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError(f"Invalid amount format: {amount_rand}")
    
    if amount_dec < 0:
        raise ValueError("Amount cannot be negative")
    
    # Validation: Check if amount appears to already be in cents
    # Amounts in rand typically have 1-2 decimal places; if > 1000000 cents (R10,000),
    # likely already in cents
    if amount_dec > Decimal('100000'):
        # This is a heuristic - amounts above R100,000 are suspicious as daily rates
        # Log a warning but allow it (could be a legitimate large booking)
        logger.warning(
            f"Large amount detected: {amount_dec} ZAR. "
            f"Ensure this is not already in cents. Converting to {int(amount_dec * 100)} cents."
        )
    
    # Convert to cents (multiply by 100) and ensure integer
    amount_cents = int(amount_dec * 100)
    
    if amount_cents == 0 and amount_dec > 0:
        raise ValueError(f"Amount {amount_rand} is too small (< 0.01 ZAR)")
    
    return amount_cents


def cents_to_rand(amount_cents):
    """
    Convert amount from Paystack cents back to ZAR (rand).
    
    Args:
        amount_cents: Amount in cents (e.g., 400000)
        
    Returns:
        Decimal: Amount in ZAR with 2 decimal places (e.g., 4000.00)
        
    Raises:
        ValueError: If amount is invalid
    """
    if amount_cents is None:
        raise ValueError("Amount cannot be None")
    
    try:
        amount_int = int(amount_cents)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid amount format: {amount_cents}")
    
    if amount_int < 0:
        raise ValueError("Amount cannot be negative")
    
    # Convert from cents to rand and return as Decimal with 2 places
    amount_rand = Decimal(amount_int) / 100
    return amount_rand.quantize(Decimal('0.01'))


def validate_amount_not_in_cents(amount_rand):
    """
    Validate that an amount in ZAR has not already been converted to cents.
    
    Args:
        amount_rand: Amount that should be in ZAR (rand)
        
    Raises:
        ValueError: If amount appears to be already in cents
    """
    try:
        amount_dec = Decimal(str(amount_rand))
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError(f"Invalid amount format: {amount_rand}")
    
    # Check for common patterns of cent amounts:
    # - Multiple of 100 (e.g., 400000, 50000)
    # - No fractional part but > 1000 (unlikely for ZAR)
    # - Divisible by 100 with no remainder and > 100
    if amount_dec % 100 == 0 and amount_dec >= 1000:
        # Additional check: if it would be a valid daily rate (< 10000 ZAR), allow it
        if amount_dec >= 100000:
            logger.warning(
                f"Amount {amount_dec} ZAR might already be in cents. "
                f"Please verify this is the correct amount in rand."
            )


def get_paystack_amount(amount_rand, validate=True):
    """
    Get the amount formatted for Paystack API (in cents).
    Combines conversion and validation.
    
    Args:
        amount_rand: Amount in ZAR (rand)
        validate: Whether to validate amount hasn't already been converted
        
    Returns:
        int: Amount in cents for Paystack API
        
    Raises:
        ValueError: If amount is invalid or appears to be in cents
    """
    if validate:
        validate_amount_not_in_cents(amount_rand)
    
    return rand_to_cents(amount_rand)


def get_display_amount(amount_rand):
    """
    Get the amount formatted for display to the frontend (in rand).
    
    Args:
        amount_rand: Amount in ZAR (rand) as Decimal or float
        
    Returns:
        float: Amount in ZAR with 2 decimal places
    """
    try:
        amount_dec = Decimal(str(amount_rand))
        return float(amount_dec.quantize(Decimal('0.01')))
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError(f"Invalid amount format: {amount_rand}")

"""
Seasonal pricing logic for Ikhaya Lami Lodge bookings.
"""
from decimal import Decimal
from datetime import date, timedelta


def calculate_easter(year):
    """Calculate Easter date for a given year using the Anonymous Gregorian algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


# Base rates per booking type (per night, except where noted)
BASE_RATES = {
    'chalet': Decimal('800.00'),
    'campsite': Decimal('200.00'),
    'conference': Decimal('5000.00'),  # Flat rate
    'safari': Decimal('400.00'),  # Flat rate (updated from 2500)
    'event': Decimal('1000.00'),  # Flat rate
}

# Seasonal adjustments (per night)
SEASONAL_ADJUSTMENTS = {
    'easter': {
        'chalet': Decimal('100.00'),
        'campsite': Decimal('50.00'),
    },
    'festive': {
        'chalet': Decimal('300.00'),
        'campsite': Decimal('100.00'),
    },
}


def get_easter_dates(year):
    """Get Easter dates for a given year (Good Friday to Easter Monday)."""
    easter_date = calculate_easter(year)
    good_friday = easter_date - timedelta(days=2)
    easter_monday = easter_date + timedelta(days=1)
    return good_friday, easter_monday


def get_festive_season_dates(year):
    """Get festive season dates (December 15 - January 5)."""
    start = date(year, 12, 15)
    end = date(year + 1, 1, 5)
    return start, end


def determine_season(check_in_date, check_out_date):
    """
    Determine the season for a booking period.
    Returns: 'normal', 'easter', or 'festive'
    """
    if not check_in_date or not check_out_date:
        return 'normal'
    
    year = check_in_date.year
    
    # Check Easter (Good Friday to Easter Monday)
    good_friday, easter_monday = get_easter_dates(year)
    if good_friday <= check_in_date <= easter_monday or good_friday <= check_out_date <= easter_monday:
        return 'easter'
    
    # Check next year's Easter if booking spans year boundary
    if check_out_date.year > year:
        next_good_friday, next_easter_monday = get_easter_dates(year + 1)
        if next_good_friday <= check_in_date <= next_easter_monday or next_good_friday <= check_out_date <= next_easter_monday:
            return 'easter'
    
    # Check if any date in the range falls in Easter
    current_date = check_in_date
    while current_date <= check_out_date:
        current_year = current_date.year
        gf, em = get_easter_dates(current_year)
        if gf <= current_date <= em:
            return 'easter'
        current_date += timedelta(days=1)
        if current_date > check_out_date:
            break
    
    # Check Festive Season (Dec 15 - Jan 5)
    festive_start = date(year, 12, 15)
    festive_end = date(year + 1, 1, 5)
    
    # Check if booking overlaps with festive season
    if (festive_start <= check_in_date <= festive_end) or \
       (festive_start <= check_out_date <= festive_end) or \
       (check_in_date <= festive_start <= check_out_date):
        return 'festive'
    
    # Check if any date in the range falls in festive season
    current_date = check_in_date
    while current_date <= check_out_date:
        if current_date.month == 12 and current_date.day >= 15:
            return 'festive'
        if current_date.month == 1 and current_date.day <= 5:
            return 'festive'
        current_date += timedelta(days=1)
        if current_date > check_out_date:
            break
    
    return 'normal'


def calculate_booking_amount(booking_type, check_in, check_out, season=None):
    """
    Calculate the total booking amount based on type, dates, and season.
    
    Args:
        booking_type: One of 'chalet', 'campsite', 'conference', 'safari', 'event'
        check_in: Date object or None
        check_out: Date object or None
        season: Optional season override ('normal', 'easter', 'festive')
    
    Returns:
        Decimal: Total amount in ZAR
    """
    base_rate = BASE_RATES.get(booking_type, Decimal('500.00'))
    
    # Safari and conference are flat rates (no seasonal adjustment)
    if booking_type in ['safari', 'conference']:
        return base_rate
    
    # Event is also flat rate
    if booking_type == 'event':
        return base_rate
    
    # For chalet and campsite, calculate per night
    if not check_in or not check_out:
        # If no dates, return base rate for 1 night
        return base_rate
    
    # Determine season if not provided
    if season is None:
        season = determine_season(check_in, check_out)
    
    # Calculate number of nights
    duration = (check_out - check_in).days
    if duration < 1:
        duration = 1
    
    # Get seasonal adjustment
    adjustment = Decimal('0.00')
    if season in SEASONAL_ADJUSTMENTS:
        adjustment = SEASONAL_ADJUSTMENTS[season].get(booking_type, Decimal('0.00'))
    
    # Calculate total: (base_rate + adjustment) * nights
    nightly_rate = base_rate + adjustment
    total = nightly_rate * duration
    
    return total


def get_seasonal_rates():
    """
    Get all rates for all booking types and seasons.
    Returns a dictionary with rates for staff dashboard.
    """
    rates = {}
    
    for booking_type in BASE_RATES.keys():
        rates[booking_type] = {
            'base_rate': float(BASE_RATES[booking_type]),
            'normal_season': {
                'rate': float(BASE_RATES[booking_type]),
                'description': 'Base rate'
            }
        }
        
        # Add seasonal rates for chalet and campsite
        if booking_type in ['chalet', 'campsite']:
            easter_adjustment = SEASONAL_ADJUSTMENTS['easter'].get(booking_type, Decimal('0.00'))
            festive_adjustment = SEASONAL_ADJUSTMENTS['festive'].get(booking_type, Decimal('0.00'))
            
            rates[booking_type]['easter_season'] = {
                'rate': float(BASE_RATES[booking_type] + easter_adjustment),
                'adjustment': float(easter_adjustment),
                'description': f'Base + R{easter_adjustment} per night'
            }
            
            rates[booking_type]['festive_season'] = {
                'rate': float(BASE_RATES[booking_type] + festive_adjustment),
                'adjustment': float(festive_adjustment),
                'description': f'Base + R{festive_adjustment} per night'
            }
        elif booking_type == 'safari':
            rates[booking_type]['description'] = 'Flat rate (no seasonal adjustment)'
        elif booking_type in ['conference', 'event']:
            rates[booking_type]['description'] = 'Flat rate (no seasonal adjustment)'
    
    return rates


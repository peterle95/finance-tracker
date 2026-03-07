"""
finance_tracker/services/currency_service.py

Central utility for parsing and formatting currency values with comma notation.
"""

def parse_amount(amount_str: str) -> float:
    """
    Parses a currency string in comma notation.
    Example: '3.000,20' -> 3000.20, '30,01' -> 30.01
    """
    if not amount_str:
        return 0.0
    
    # Remove currency symbol if present
    s = amount_str.replace('€', '').strip()
    
    # Remove thousands separators (.)
    # Then replace decimal comma (,) with dot (.)
    # If there's no comma but there are dots, they might be dots for decimals if the user is inconsistent,
    # but the requirement says comma notation, so we treat dots as thousands and comma as decimal.
    
    if ',' in s:
        s = s.replace('.', '')
        s = s.replace(',', '.')
    else:
        # If no comma is present, the dots might be intended as decimal points (legacy support)
        # OR they might be thousands separators. 
        # Requirement: "30,01 as 30 euro and 1 cent. 3.000,20 is the same as 3000,20"
        # If someone types "3000.20" without a comma, we should ideally handle it or stick strictly to comma.
        # Let's be flexible: if there's a dot but no comma, 
        # and there's only one dot and it's near the end, it might be a decimal.
        # However, following "dot notation to comma notation" strictly:
        pass

    try:
        return float(s)
    except ValueError:
        return 0.0

def format_amount(val: float, include_symbol: bool = True) -> str:
    """
    Formats a float with dot as thousands separator and comma as decimal separator.
    Example: 3000.20 -> '€3.000,20'
    """
    if val is None:
        val = 0.0
        
    # Format with 2 decimal places and dot as thousands separator
    # Then switch them
    s = f"{val:,.2f}"
    # Replace , with temp, . with ,, temp with .
    s = s.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    
    return f"€{s}" if include_symbol else s

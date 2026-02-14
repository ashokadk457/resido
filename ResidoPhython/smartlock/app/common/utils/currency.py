from forex_python.converter import CurrencyCodes


def get_currency_codes(currency_code):
    """
    Converts a currency code to its symbol.

    Args:
        currency_code (str): The currency code (e.g., 'USD', 'EUR', 'GBP')

    Returns:
        str: The currency symbol (e.g., '$', '€', '£'). Returns the original
             currency code if symbol cannot be found.
    """
    if not currency_code:
        return currency_code

    currency_codes = CurrencyCodes()
    symbol = currency_codes.get_symbol(currency_code)

    # If no symbol is found, return the original currency code
    return symbol if symbol else currency_code

import json

from bot.services.currency_service import CurrencyService


def get_currency_rate(query: str, currency_service: CurrencyService) -> str:
    currencies = currency_service.extract_currencies(query)
    if currencies is None:
        return json.dumps(
            {
                "error": (
                    "Hangi para birimini sormak istedigini anlayamadim."
                ),
            }
        )

    from_currency, to_currency = currencies
    return currency_service.get_rate(from_currency, to_currency)

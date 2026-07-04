import json
import re


ALLOWED_EXPRESSION = re.compile(r"^[0-9+\-*/().,\s]+$")
MAX_EXPRESSION_LENGTH = 64


def calculate(expression: str) -> str:
    sanitized = expression.replace(",", ".").strip()

    if not sanitized:
        return json.dumps(
            {
                "expression": expression,
                "error": "Calculation could not be completed.",
            }
        )

    if len(sanitized) > MAX_EXPRESSION_LENGTH:
        return json.dumps(
            {
                "expression": expression,
                "error": "Calculation could not be completed.",
            }
        )

    if not ALLOWED_EXPRESSION.fullmatch(sanitized) or "**" in sanitized:
        return json.dumps(
            {
                "expression": expression,
                "error": "Calculation could not be completed.",
            }
        )

    try:
        result = eval(sanitized, {"__builtins__": {}}, {})
    except Exception:
        return json.dumps(
            {
                "expression": expression,
                "error": "Calculation could not be completed.",
            }
        )

    return json.dumps(
        {
            "expression": expression,
            "result": str(result),
        }
    )

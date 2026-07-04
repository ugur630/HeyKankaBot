import json
from datetime import datetime


def get_current_date(query: str) -> str:
    del query
    now = datetime.now()
    return json.dumps(
        {
            "date": now.strftime("%Y-%m-%d"),
        }
    )

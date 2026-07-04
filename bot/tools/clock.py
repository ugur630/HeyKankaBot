import json
from datetime import datetime


def get_current_time(query: str) -> str:
    del query
    now = datetime.now()
    return json.dumps(
        {
            "time": now.strftime("%H:%M:%S"),
        }
    )

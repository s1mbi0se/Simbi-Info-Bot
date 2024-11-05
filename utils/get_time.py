import datetime

import httpx
from config import Config


def get_time_from_api():
    response = httpx.get(
        "https://timeapi.io/api/time/current/zone?timeZone=America%2FSao_Paulo"
    )
    data = response.json()
    datetime_string = data["dateTime"][:26]
    datetime_object = datetime.datetime.strptime(
        datetime_string, "%Y-%m-%dT%H:%M:%S.%f"
    )
    now = datetime_object.astimezone(Config.TIME_ZONE)
    print("NOW: ", now)
    return now

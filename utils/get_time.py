import datetime

import httpx
from config import Config


def get_time_from_api():
    response = httpx.get(
        r"https://worldtimeapi.org/api/timezone/America/Sao_Paulo"
    )
    data = response.json()
    datetime_string = data["datetime"]
    datetime_object = datetime.datetime.strptime(
        datetime_string, "%Y-%m-%dT%H:%M:%S.%f%z"
    )
    now = datetime_object.astimezone(Config.TIME_ZONE)
    return now

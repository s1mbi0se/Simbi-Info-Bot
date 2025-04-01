import datetime
from datetime import datetime

from config import Config


def get_time_from_api():
    now = datetime.now(Config.TIME_ZONE)
    print("NOW: ", now)
    return now

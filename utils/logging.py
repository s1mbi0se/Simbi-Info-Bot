import asyncio
from datetime import datetime

from utils.get_time import get_time_from_api


def write_error_log(sender: str, msg: str, now: datetime = None) -> None:
    now = now if now else get_time_from_api()
    with open("error.log", "a") as f:
        f.write(f"{now}: {sender}: ERROR: {str(msg)}\n")


def write_report_log(sender: str, msg: str, now: datetime = None) -> None:
    now = now if now else get_time_from_api()
    with open("report.log", "a") as f:
        f.write(f"{now}: {sender}: {msg}\n")


async def write_report_log_async(
    sender: str, msg: str, now: datetime = None
) -> None:
    await asyncio.to_thread(write_report_log, sender, msg, now)


async def write_error_log_async(
    sender: str, msg: str, now: datetime = None
) -> None:
    await asyncio.to_thread(write_error_log, sender, msg, now)

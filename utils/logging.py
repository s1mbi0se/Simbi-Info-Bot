from utils.get_time import get_time_from_api


def write_error_log(sender: str, msg: str) -> None:
    now = get_time_from_api()
    with open("error.log", "a") as f:
        f.write(f"{now}: {sender}: ERROR: {str(msg)}\n")


def write_report_log(sender: str, msg: str) -> None:
    with open("report.log", "a") as f:
        now = get_time_from_api()
        f.write(f"{now}: {sender}: {msg}\n")

from datetime import datetime

import gspread
from config import Config

from utils.get_time import get_time_from_api
from utils.logging import write_error_log


def get_cloud_storage_client():
    if Config.IS_EMPTY:
        return None

    client = gspread.service_account_from_dict(Config.CREDENTIALS)

    return client


def get_birthdays():
    TODAY = get_time_from_api().date()

    try:
        g_cloud_client = get_cloud_storage_client()

        if g_cloud_client:
            sheet = g_cloud_client.open_by_url(Config.BIRTHDAY_SHEET)

            worksheet = sheet.worksheet("Endereço")
            dict_of_values = worksheet.get_all_records()

            dict_of_values = [
                {
                    k: (
                        datetime.strptime(v, "%d/%m/%Y")
                        if k == "Nascimento" and v
                        else v
                    )
                    for k, v in record.items()
                }
                for record in dict_of_values
            ]

            filtered_records = [
                record
                for record in dict_of_values
                if record.get("Foto")
                and record.get("Nascimento").month == TODAY.month
                and record.get("Nascimento").day == TODAY.day
            ]

            if filtered_records:
                for record in filtered_records:
                    url = record.get("Foto")
                    url = url.replace("/file/d/", "/uc?id=")
                    url = url.split("/view")[0]
                    record["Foto"] = url

            return filtered_records if filtered_records else None

    except Exception as e:
        write_error_log(sender="BIRTH SPREAD", msg=str(e))


if __name__ == "__main__":
    print(get_birthdays())

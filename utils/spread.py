from datetime import datetime, timedelta

import gspread
from config import Config


def get_cloud_storage_client():
    if Config.IS_EMPTY:
        return None

    client = gspread.service_account_from_dict(Config.CREDENTIALS)

    return client


def get_next_revaluation():
    FUTURE_DATE = datetime.today().date() + timedelta(
        days=Config.DAYS_IN_ADVANCE
    )

    try:
        g_cloud_client = get_cloud_storage_client()

        if g_cloud_client:
            sheet = g_cloud_client.open_by_url(Config.URL_SHEET)

            worksheet = sheet.worksheet("Reavaliação")
            dict_of_values = worksheet.get_all_records()

            dict_of_values = [
                {
                    k: (
                        datetime.strptime(v, "%d/%m/%Y")
                        if k == "Próxima reavaliação" and v != "-"
                        else v
                    )
                    for k, v in record.items()
                }
                for record in dict_of_values
            ]

            filtered_records = [
                record
                for record in dict_of_values
                if record.get("Próxima reavaliação") != "-"
                and record.get("Próxima reavaliação").date() == FUTURE_DATE
            ]

            return filtered_records if filtered_records else None

    except Exception:
        return None

import httpx

from utils.logging import write_error_log


def ping_notify(url: str) -> str:
    try:
        response = httpx.get(url, timeout=10.0)

        if response.status_code == 200:
            return "ON"
        else:
            return "OFF"

    except httpx.ConnectError:
        return "OFF"

    except httpx.TimeoutException as e:
        write_error_log(sender=f"SERVICE -> {url}", msg=str(e))
        return "TIMEOUT"

    except Exception as e:
        write_error_log(sender=f"SERVICE -> {url}", msg=str(e))
        return "INTERNAL ERROR"


def generate_message(name: str, status: str):
    match status:
        case "ON":
            return f"   ✅ {name}" + "\n"
        case "OFF":
            return f"   ❌ {name}" + "\n"
        case "TIMEOUT":
            return f"   🕔 {name}: TIMEOUT" + "\n"
        case _:
            return f"   💀 {name}: ERRO INTERNO - VERIFICAR LOG" + "\n"

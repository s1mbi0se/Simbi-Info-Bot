import asyncio
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx

from utils.logging import write_error_log


async def _get_cert_status(url: str, timeout: float = 10.0) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or url
    port = parsed.port or 443

    def fetch():
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        not_after = cert.get("notAfter")
        if not_after:
            exp = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=timezone.utc
            )
            if exp > datetime.now(timezone.utc):
                return "🔒"
            return "🔓 (SSL invalido)"
        return "🔒"

    try:
        return await asyncio.to_thread(fetch)
    except Exception:
        return "🔓 (SSL invalido)"


async def ping_notify(url: str) -> str:
    ping_url = urljoin(url.rstrip("/") + "/", "api/v1/ping")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(ping_url)

        cert_status = await _get_cert_status(url)

        if response.status_code == 200:
            instance_status = "✅"
        else:
            instance_status = "❌"

        domain = urlparse(url).netloc
        return f"{domain} {instance_status} {cert_status}"

    except httpx.ConnectError as e:
        cause = getattr(e, "__cause__", None)
        domain = urlparse(url).netloc

        if isinstance(cause, ssl.SSLCertVerificationError):
            return f"{domain} ❌ 🔓 (SSL inválido)"
        return f"{domain} ❌ 🔓 (SSL inválido)"

    except httpx.TimeoutException as e:
        write_error_log(sender=f"SERVICE -> {url}", msg=str(e))
        domain = urlparse(url).netloc
        cert_status = await _get_cert_status(url)
        return f"{domain} 🕔 {cert_status} (timeout)"

    except Exception as e:
        write_error_log(sender=f"SERVICE -> {url}", msg=str(e))
        domain = urlparse(url).netloc
        cert_status = await _get_cert_status(url)
        return f"{domain} ❌ {cert_status} (erro)"


def generate_message(name: str, status: str):
    match status:
        case "ON":
            return f"   ✅ {name}\n"
        case "OFF":
            return f"   ❌ {name}\n"
        case "TIMEOUT":
            return f"   🕔 {name}: TIMEOUT\n"
        case _:
            return f"   💀 {name}: ERRO INTERNO - VERIFICAR LOG\n"

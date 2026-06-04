import logging

from core.config import settings
from core.http_client import post_json
from core.models import ExchangeRate

logger = logging.getLogger(__name__)


def login() -> str:
    """Obtiene el access token de la API."""
    url = f"{settings.api_base_url.rstrip('/')}/auth/login"
    payload = {
        "email": settings.api_email,
        "password": settings.api_password,
    }
    data = post_json(url, payload)
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Login no devolvió access_token")
    return token


def save_rate(rate: ExchangeRate, token: str | None = None) -> bool:
    """Guarda una tasa en la API. Retorna True si fue exitoso."""
    url = f"{settings.api_base_url.rstrip('/')}/rates"
    try:
        access_token = token or login()
        headers = {"Authorization": f"Bearer {access_token}"}
        post_json(url, rate.to_dict(), headers=headers)
        logger.info(f"Guardado: {rate.bank_code} {rate.currency_from}/{rate.currency_to}")
        return True
    except Exception as e:
        logger.error(f"Error guardando tasa {rate.bank_code}: {e}")
        return False


def save_rates_bulk(rates: list[ExchangeRate]) -> int:
    """
    Guarda una lista de tasas en la API.
    Retorna el número de registros guardados exitosamente.
    """
    if not rates:
        return 0

    token = login()
    saved = 0
    for rate in rates:
        if save_rate(rate, token=token):
            saved += 1
    return saved

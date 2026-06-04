import time
import logging
from typing import Optional

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


def get_html(url: str, headers: Optional[dict] = None, retries: Optional[int] = None) -> str:
    """GET con reintentos y User-Agent de browser real."""
    max_retries = retries if retries is not None else settings.max_retries
    default_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "es-ES,es;q=0.9",
    }
    if headers:
        default_headers.update(headers)

    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=settings.request_timeout, follow_redirects=True) as client:
                response = client.get(url, headers=default_headers)
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            logger.warning(f"[attempt {attempt}/{max_retries}] HTTP {e.response.status_code} en {url}")
        except Exception as e:
            logger.warning(f"[attempt {attempt}/{max_retries}] Error en {url}: {e}")

        if attempt < max_retries:
            time.sleep(2 ** attempt)  # backoff exponencial: 2s, 4s

    raise RuntimeError(f"Falló después de {max_retries} intentos: {url}")


def post_json(url: str, payload: dict, headers: Optional[dict] = None) -> dict:
    """POST JSON a la API con reintentos."""
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)

    for attempt in range(1, settings.max_retries + 1):
        try:
            with httpx.Client(timeout=settings.request_timeout) as client:
                response = client.post(url, json=payload, headers=default_headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"[attempt {attempt}] POST falló: {e}")
            if attempt < settings.max_retries:
                time.sleep(2 ** attempt)

    raise RuntimeError(f"POST falló después de {settings.max_retries} intentos: {url}")

"""
Scraper para BHD León (República Dominicana).

Consume directamente el endpoint JSON interno del banco:
  GET https://backend.bhd.com.do/api/modal-cambio-rate?populate=deep

Respuesta relevante:
  data.attributes.exchangeRates → lista de tasas
  Cada item: { "currency": "USD", "buyingRate": 56.7, "sellingRate": 60.2, ... }
"""
import logging

import httpx

from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class BHDScraper(BaseScraper):
    bank_code = "BHD"
    bank_name = "BHD León"
    country_code = "DO"
    source_url = "https://backend.bhd.com.do/api/modal-cambio-rate?populate=deep"
    entity_id = 6

    # Monedas a guardar en la API. Quita/agrega según lo que quieras recoger.
    currency_ids = {
        "USD": 2,
        "EUR": 3,
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        data = self._call_api()

        # Navegar la estructura: data → attributes → exchangeRates
        try:
            exchange_rates: list[dict] = (
                data["data"]["attributes"]["exchangeRates"]
            )
        except (KeyError, TypeError) as e:
            raise RuntimeError(f"Estructura de respuesta inesperada: {e}") from e

        if not exchange_rates:
            raise RuntimeError("exchangeRates vino vacío en la respuesta de BHD")

        rates = []
        for item in exchange_rates:
            currency = item.get("currency", "").upper().strip()
            buy = item.get("buyingRate")
            sell = item.get("sellingRate")

            if currency not in self.currency_ids:
                logger.debug(f"[BHD] Moneda ignorada: {currency}")
                continue

            if buy is None and sell is None:
                logger.warning(f"[BHD] {currency} sin tasas, se omite")
                continue

            rates.append(self._make_rate(
                currency_from=currency,
                currency_to="DOP",
                buy_rate=buy,
                sell_rate=sell,
            ))
            logger.info(f"[BHD] {currency}: compra={buy}, venta={sell}")

        return rates

    def _call_api(self) -> dict:
        """Llama al endpoint JSON de BHD con headers de browser para evitar bloqueos."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.bhd.com.do/",
            "Origin": "https://www.bhd.com.do",
        }
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            response = client.get(self.source_url, headers=headers)
            response.raise_for_status()
            return response.json()

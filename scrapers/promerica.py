"""
Scraper para Banco Promerica Republica Dominicana.

Lee las tasas publicadas en la pagina principal:
  https://www.promerica.com.do/
"""
import json
import logging

import httpx
from bs4 import BeautifulSoup

from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class PromericaScraper(BaseScraper):
    bank_code = "PROMERICA"
    bank_name = "Banco Promerica Republica Dominicana"
    country_code = "DO"
    source_url = "https://www.promerica.com.do/"
    entity_id = 9

    currency_ids = {
        "USD": 2,
        "EUR": 3,
    }

    CURRENCY_CODES = {
        "840": "USD",
        "978": "EUR",
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        data = self._call_api()
        items = data.get("value")
        if not isinstance(items, list):
            raise RuntimeError("Estructura de respuesta inesperada en Promerica")

        rates = []
        for item in items:
            currency = self.CURRENCY_CODES.get(str(item.get("currency", "")).strip())
            if currency not in self.currency_ids:
                continue

            buy = item.get("buys")
            sell = item.get("sales")
            if buy is None and sell is None:
                logger.warning(f"[PROMERICA] {currency} sin tasas, se omite")
                continue

            rates.append(self._make_rate(
                currency_from=currency,
                currency_to="DOP",
                buy_rate=buy,
                sell_rate=sell,
            ))
            logger.info(f"[PROMERICA] {currency}: compra={buy}, venta={sell}")

        if not rates:
            raise RuntimeError("No se encontraron tasas en Promerica")

        return rates

    def _call_api(self) -> dict:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-ES,es;q=0.9",
        }
        with httpx.Client(timeout=30, follow_redirects=True, headers=headers) as client:
            html_response = client.get(self.source_url)
            html_response.raise_for_status()

            soup = BeautifulSoup(html_response.text, "html.parser")
            section = soup.select_one("#tipoCambioHome")
            if not section or not section.get("data-url"):
                raise RuntimeError("No se encontro el endpoint de tipo de cambio en Promerica")

            endpoint = str(httpx.URL(self.source_url).join(section["data-url"]))
            response = client.post(
                endpoint,
                data={"json": json.dumps({"operacion": 2})},
                headers={
                    "Referer": self.source_url,
                    "X-Requested-With": "XMLHttpRequest",
                },
            )
            response.raise_for_status()
            return response.json()

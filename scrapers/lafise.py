"""
Scraper para Banco LAFISE Republica Dominicana.

Lee las tasas usadas por la pagina principal:
  https://www.lafise.com/blrd/
"""
import logging
from datetime import date

import httpx

from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class LafiseScraper(BaseScraper):
    bank_code = "LAFISE"
    bank_name = "Banco LAFISE Republica Dominicana"
    country_code = "DO"
    source_url = "https://www.lafise.com/blrd/"
    fetch_url = "https://www.lafise.com/OpenBankingProxy/obl/v1/banks/BLRD/rates"
    entity_id = 16

    currency_ids = {
        "USD": 2,
        "EUR": 3,
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        payload = self._fetch_payload()
        rate_date = self._parse_date(payload.get("date"))
        rates_data = payload.get("rates") or {}

        rates = []
        for currency in self.currency_ids:
            item = rates_data.get(currency) or {}
            buy = item.get("buying")
            sell = item.get("selling")
            if buy is None or sell is None:
                logger.warning(f"[LAFISE] {currency} sin tasas, se omite")
                continue

            rates.append(self._make_rate(
                currency_from=currency,
                currency_to="DOP",
                buy_rate=buy,
                sell_rate=sell,
                rate_date=rate_date,
            ))
            logger.info(f"[LAFISE] {currency}: compra={buy}, venta={sell}")

        if not rates:
            raise RuntimeError("No se encontraron tasas en LAFISE")

        return rates

    def _fetch_payload(self) -> dict:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": self.source_url,
        }
        with httpx.Client(timeout=30, follow_redirects=True, headers=headers) as client:
            response = client.get(self.fetch_url)
            response.raise_for_status()
            return response.json()

    def _parse_date(self, value: str | None) -> date | None:
        if not value:
            return None

        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            logger.warning(f"[LAFISE] Fecha invalida: {value}")
            return None

"""
Scraper para Banco Vimenca Republica Dominicana.

Lee las tasas usadas por la pagina principal:
  https://www.bancovimenca.com/
"""
import logging
from datetime import datetime

import httpx

from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class VimencaScraper(BaseScraper):
    bank_code = "VIMENCA"
    bank_name = "Banco Vimenca"
    country_code = "DO"
    source_url = "https://www.bancovimenca.com/"
    fetch_url = "https://devops.bancovimenca.com/api-proxy.php"
    entity_id = 14

    currency_ids = {
        "USD": 2,
        "EUR": 3,
    }

    COIN_CODES = {
        "USD": 2,
        "EUR": 4,
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        payload = self._fetch_payload()
        items = payload.get("data") or []

        rates = []
        for currency, coin_code in self.COIN_CODES.items():
            item = self._find_rate(items, coin_code)
            if not item:
                logger.warning(f"[VIMENCA] {currency} sin tasas, se omite")
                continue

            buy = item.get("purchaseValue")
            sell = item.get("saleValue")
            if buy is None or sell is None:
                logger.warning(f"[VIMENCA] {currency} sin compra/venta, se omite")
                continue

            rates.append(self._make_rate(
                currency_from=currency,
                currency_to="DOP",
                buy_rate=buy,
                sell_rate=sell,
                rate_date=self._parse_date(item.get("fecha")),
            ))
            logger.info(f"[VIMENCA] {currency}: compra={buy}, venta={sell}")

        if not rates:
            raise RuntimeError("No se encontraron tasas en Vimenca")

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

    def _find_rate(self, items: list[dict], coin_code: int) -> dict | None:
        return next((item for item in items if item.get("coinCode") == coin_code), None)

    def _parse_date(self, value: str | None):
        if not value:
            return None

        try:
            return datetime.strptime(str(value).strip(), "%Y%m%d").date()
        except ValueError:
            logger.warning(f"[VIMENCA] Fecha invalida: {value}")
            return None

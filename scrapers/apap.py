"""
Scraper para Asociacion Popular de Ahorros y Prestamos (APAP).

Lee las tasas publicadas en la pagina principal:
  https://www.apap.com.do/
"""
import logging
import re

from bs4 import BeautifulSoup

from core.http_client import get_html
from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class APAPScraper(BaseScraper):
    bank_code = "APAP"
    bank_name = "Asociacion Popular de Ahorros y Prestamos"
    country_code = "DO"
    source_url = "https://www.apap.com.do/"
    entity_id = 2

    currency_ids = {
        "USD": 2,
        "EUR": 3,
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        html = get_html(self.source_url)
        soup = BeautifulSoup(html, "html.parser")

        rates = []
        for currency in self.currency_ids:
            buy = self._extract_rate(soup, html, f"currency-buy-{currency}")
            sell = self._extract_rate(soup, html, f"currency-sell-{currency}")
            if not buy or not sell:
                logger.warning(f"[APAP] {currency} sin tasas, se omite")
                continue

            rates.append(self._make_rate(
                currency_from=currency,
                currency_to="DOP",
                buy_rate=buy,
                sell_rate=sell,
            ))
            logger.info(f"[APAP] {currency}: compra={buy}, venta={sell}")

        if not rates:
            raise RuntimeError("No se encontraron tasas en APAP")

        return rates

    def _extract_rate(self, soup: BeautifulSoup, html: str, element_id: str) -> str | None:
        element = soup.select_one(f"#{element_id}")
        if element:
            value = self._clean_rate(element.get_text(strip=True))
            if value:
                return value

        match = re.search(rf"#{element_id}[^;]+?([0-9]+(?:[.,][0-9]+)?)", html)
        if match:
            return match.group(1)

        return None

    def _clean_rate(self, value: str) -> str:
        return value.replace("DOP", "").strip()

"""
Scraper para Banco BDI Republica Dominicana.

Lee las tasas publicadas en la pagina principal:
  https://www.bdi.com.do/
"""
import logging
from datetime import datetime

from bs4 import BeautifulSoup

from core.http_client import get_html
from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class BDIScraper(BaseScraper):
    bank_code = "BDI"
    bank_name = "Banco BDI"
    country_code = "DO"
    source_url = "https://www.bdi.com.do/"
    entity_id = 12

    currency_ids = {
        "USD": 2,
        "EUR": 3,
    }

    RATE_SELECTORS = {
        "USD": ("#rd-compra", "#rd-venta"),
        "EUR": ("#rd-euro-compra", "#rd-euro-venta"),
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        html = get_html(self.source_url)
        soup = BeautifulSoup(html, "html.parser")
        rate_date = self._extract_date(soup)

        rates = []
        for currency, (buy_selector, sell_selector) in self.RATE_SELECTORS.items():
            buy = self._extract_rate(soup, buy_selector)
            sell = self._extract_rate(soup, sell_selector)
            if not buy or not sell:
                logger.warning(f"[BDI] {currency} sin tasas, se omite")
                continue

            rates.append(self._make_rate(
                currency_from=currency,
                currency_to="DOP",
                buy_rate=buy,
                sell_rate=sell,
                rate_date=rate_date,
            ))
            logger.info(f"[BDI] {currency}: compra={buy}, venta={sell}")

        if not rates:
            raise RuntimeError("No se encontraron tasas en BDI")

        return rates

    def _extract_rate(self, soup: BeautifulSoup, selector: str) -> str | None:
        element = soup.select_one(selector)
        if not element:
            return None

        value = element.get("value") or element.get_text(strip=True)
        return value.strip() if value else None

    def _extract_date(self, soup: BeautifulSoup):
        footer = soup.select_one(".modal-footer p")
        if not footer:
            return None

        value = footer.get_text(" ", strip=True).replace("Actualizado:", "").strip()
        if not value:
            return None

        try:
            return datetime.strptime(value, "%d/%m/%Y %H:%M").date()
        except ValueError:
            logger.warning(f"[BDI] Fecha invalida: {value}")
            return None

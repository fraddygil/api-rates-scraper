"""
Scraper para Banesco Republica Dominicana.

Lee las tasas publicadas en la pagina principal:
  https://www.banesco.com.do/
"""
import logging
from datetime import date

from bs4 import BeautifulSoup

from core.http_client import get_html
from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class BanescoScraper(BaseScraper):
    bank_code = "BANESCO"
    bank_name = "Banesco Republica Dominicana"
    country_code = "DO"
    source_url = "https://www.banesco.com.do/"
    entity_id = 10

    currency_ids = {
        "USD": 2,
        "EUR": 3,
    }

    RATE_ATTRIBUTES = {
        "USD": ("data-currency-usd-rate-buy", "data-currency-usd-rate-sell"),
        "EUR": ("data-currency-eur-rate-buy", "data-currency-eur-rate-sell"),
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        html = get_html(self.source_url)
        soup = BeautifulSoup(html, "html.parser")
        calculator = soup.select_one(".calculator")
        if not calculator:
            raise RuntimeError("No se encontro el bloque de tasas en Banesco")

        rate_date = self._parse_date(calculator.get("data-currency-date"))
        rates = []
        for currency, (buy_attr, sell_attr) in self.RATE_ATTRIBUTES.items():
            buy = calculator.get(buy_attr)
            sell = calculator.get(sell_attr)
            if not buy or not sell:
                logger.warning(f"[BANESCO] {currency} sin tasas, se omite")
                continue

            rates.append(self._make_rate(
                currency_from=currency,
                currency_to="DOP",
                buy_rate=buy,
                sell_rate=sell,
                rate_date=rate_date,
            ))
            logger.info(f"[BANESCO] {currency}: compra={buy}, venta={sell}")

        if not rates:
            raise RuntimeError("No se encontraron tasas en Banesco")

        return rates

    def _parse_date(self, value: str | None) -> date | None:
        if not value:
            return None

        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            logger.warning(f"[BANESCO] Fecha invalida: {value}")
            return None

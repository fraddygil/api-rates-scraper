"""
Scraper para Banreservas (Republica Dominicana).

Lee las tasas publicadas en la pagina principal:
  https://www.banreservas.com/
"""
import logging

from bs4 import BeautifulSoup

from core.http_client import get_html
from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class BanreservasScraper(BaseScraper):
    bank_code = "BANRESERVAS"
    bank_name = "Banreservas"
    country_code = "DO"
    source_url = "https://www.banreservas.com/"
    entity_id = 4

    # Monedas a guardar en la API. Quita/agrega segun lo que quieras recoger.
    currency_ids = {
        "USD": 2,
        "EUR": 3,
    }

    RATE_SELECTORS = {
        "USD": (".tasacambio-compraUS", ".tasacambio-ventaUS"),
        "EUR": (".tasacambio-compraEU", ".tasacambio-ventaEU"),
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        html = get_html(self.source_url)
        soup = BeautifulSoup(html, "html.parser")

        rates = []
        for currency, (buy_selector, sell_selector) in self.RATE_SELECTORS.items():
            if currency not in self.currency_ids:
                continue

            buy_el = soup.select_one(buy_selector)
            sell_el = soup.select_one(sell_selector)
            if not buy_el or not sell_el:
                logger.warning(f"[BANRESERVAS] {currency} sin tasas, se omite")
                continue

            buy = buy_el.get_text(strip=True)
            sell = sell_el.get_text(strip=True)
            rates.append(self._make_rate(
                currency_from=currency,
                currency_to="DOP",
                buy_rate=buy,
                sell_rate=sell,
            ))
            logger.info(f"[BANRESERVAS] {currency}: compra={buy}, venta={sell}")

        if not rates:
            raise RuntimeError("No se encontraron tasas en Banreservas")

        return rates

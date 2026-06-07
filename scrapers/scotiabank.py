"""
Scraper para Scotiabank Republica Dominicana.

Lee las tasas publicadas en:
  https://do.scotiabank.com/banca-personal/tarifas/tasas-de-cambio.html
"""
import logging

from bs4 import BeautifulSoup

from core.http_client import get_html
from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ScotiabankScraper(BaseScraper):
    bank_code = "SCOTIABANK"
    bank_name = "Scotiabank Republica Dominicana"
    country_code = "DO"
    source_url = "https://do.scotiabank.com/banca-personal/tarifas/tasas-de-cambio.html"
    entity_id = 8

    currency_ids = {
        "USD": 2,
        "EUR": 3,
    }

    CURRENCY_LABELS = {
        "USD": ("Dolar (US)", "Dólar (US)"),
        "EUR": ("Euro (EU)",),
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        html = get_html(self.source_url)
        soup = BeautifulSoup(html, "html.parser")

        rates = []
        for currency, labels in self.CURRENCY_LABELS.items():
            row = self._find_currency_row(soup, labels)
            if not row:
                logger.warning(f"[SCOTIABANK] {currency} sin tasas, se omite")
                continue

            cols = [td.get_text(" ", strip=True) for td in row.select("td")]
            if len(cols) < 4:
                logger.warning(f"[SCOTIABANK] {currency} fila incompleta, se omite")
                continue

            buy = cols[-2]
            sell = cols[-1]
            rates.append(self._make_rate(
                currency_from=currency,
                currency_to="DOP",
                buy_rate=buy,
                sell_rate=sell,
            ))
            logger.info(f"[SCOTIABANK] {currency}: compra={buy}, venta={sell}")

        if not rates:
            raise RuntimeError("No se encontraron tasas en Scotiabank")

        return rates

    def _find_currency_row(self, soup: BeautifulSoup, labels: tuple[str, ...]):
        for row in soup.select("._bns--table table tr"):
            row_text = row.get_text(" ", strip=True).replace("\xa0", " ")
            if any(label in row_text for label in labels):
                return row

        return None

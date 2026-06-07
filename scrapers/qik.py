"""
Scraper para Qik Banco Digital Dominicano.

Lee la tasa USD publicada en:
  https://qik.do/tasadeldia/
"""
import logging
import re

from bs4 import BeautifulSoup

from core.http_client import get_html
from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class QikScraper(BaseScraper):
    bank_code = "QIK"
    bank_name = "Qik Banco Digital Dominicano"
    country_code = "DO"
    source_url = "https://qik.do/tasadeldia/"
    entity_id = 19

    currency_ids = {
        "USD": 2,
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        html = get_html(self.source_url)
        soup = BeautifulSoup(html, "html.parser")

        rate_block = soup.find(string=re.compile(r"Vendemos:"))
        if not rate_block:
            raise RuntimeError("No se encontraron tasas USD en Qik")

        text = rate_block.parent.get_text(" ", strip=True)
        sell = self._extract_rate(text, "Vendemos")
        buy = self._extract_rate(text, "Compramos")
        if not buy or not sell:
            raise RuntimeError("No se encontraron tasas USD en Qik")

        rate = self._make_rate(
            currency_from="USD",
            currency_to="DOP",
            buy_rate=buy,
            sell_rate=sell,
        )
        logger.info(f"[QIK] USD: compra={buy}, venta={sell}")

        return [rate]

    def _extract_rate(self, text: str, label: str) -> str | None:
        match = re.search(rf"{label}:\s*RD\$\s*([0-9]+(?:[.,][0-9]+)?)", text)
        if match:
            return match.group(1)

        return None

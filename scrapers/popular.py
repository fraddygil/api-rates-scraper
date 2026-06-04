"""
Scraper para Banco Popular Dominicano.
Ajusta los selectores CSS al inspeccionar el HTML real del sitio.
"""
import logging
from bs4 import BeautifulSoup

from core.http_client import get_html
from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class PopularScraper(BaseScraper):
    bank_code = "POPULAR"
    bank_name = "Banco Popular Dominicano"
    country_code = "DO"
    source_url = "https://www.popularenlinea.com/personas/Paginas/TasadeCambio.aspx"
    entity_id = 0  # TODO: reemplazar por el ID real de Popular en la API
    currency_ids = {
        "USD": 0,  # TODO: reemplazar por el ID real de USD
        "EUR": 0,  # TODO: reemplazar por el ID real de EUR
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        html = get_html(self.source_url)
        soup = BeautifulSoup(html, "html.parser")
        rates = []

        # Ajusta el selector según la estructura real
        rows = soup.select(".tasa-cambio tr, .exchange-rate-table tr")
        for row in rows:
            cols = [td.get_text(strip=True) for td in row.select("td")]
            if len(cols) < 3:
                continue

            currency_label = cols[0].upper()
            currency_map = {
                "USD": "USD", "DÓLAR": "USD",
                "EUR": "EUR", "EURO": "EUR",
            }
            currency_code = next(
                (v for k, v in currency_map.items() if k in currency_label),
                None
            )
            if not currency_code:
                continue

            if currency_code not in self.currency_ids:
                continue

            rates.append(self._make_rate(
                currency_from=currency_code,
                currency_to="DOP",
                buy_rate=cols[1],
                sell_rate=cols[2],
            ))

        return rates

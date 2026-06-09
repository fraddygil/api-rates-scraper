"""
Scraper para Banco Caribe Republica Dominicana.

Lee las tasas publicadas en la pagina principal:
  https://www.bancocaribe.com.do/
"""
import logging

from bs4 import BeautifulSoup

import httpx

from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class BancoCaribeScraper(BaseScraper):
    bank_code = "BANCOCARIBE"
    bank_name = "Banco Caribe"
    country_code = "DO"
    source_url = "https://www.bancocaribe.com.do/"
    fetch_url = "http://www.bancocaribe.com.do/"
    entity_id = 11

    currency_ids = {
        "USD": 2,
        "EUR": 3,
    }

    RATE_SELECTORS = {
        "USD": ("#us_buy_num", "#us_sell_num"),
        "EUR": ("#eur_buy_num", "#eur_sell_num"),
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        html = self._fetch_html()
        soup = BeautifulSoup(html, "html.parser")

        rates = []
        for currency, (buy_selector, sell_selector) in self.RATE_SELECTORS.items():
            buy = self._extract_rate(soup, buy_selector)
            sell = self._extract_rate(soup, sell_selector)
            if not buy or not sell:
                logger.warning(f"[BANCOCARIBE] {currency} sin tasas, se omite")
                continue

            rates.append(self._make_rate(
                currency_from=currency,
                currency_to="DOP",
                buy_rate=buy,
                sell_rate=sell,
            ))
            logger.info(f"[BANCOCARIBE] {currency}: compra={buy}, venta={sell}")

        if not rates:
            raise RuntimeError("No se encontraron tasas en Banco Caribe")

        return rates

    def _extract_rate(self, soup: BeautifulSoup, selector: str) -> str | None:
        element = soup.select_one(selector)
        if not element:
            return None

        value = element.get_text(strip=True)
        return value or None

    def _fetch_html(self) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-ES,es;q=0.9",
        }
        with httpx.Client(timeout=30, follow_redirects=True, headers=headers) as client:
            response = client.get(self.fetch_url)
            response.raise_for_status()
            return response.text

"""
Scraper para Banco Central de la Republica Dominicana.

Lee la tasa USD publicada en:
  https://www.bancentral.gov.do/SectorExterno/HistoricoTasas
"""
import logging
from datetime import datetime

import httpx

from core.models import ExchangeRate
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class BancoCentralScraper(BaseScraper):
    bank_code = "BANCOCENTRAL"
    bank_name = "Banco Central de la Republica Dominicana"
    country_code = "DO"
    source_url = "https://www.bancentral.gov.do/SectorExterno/HistoricoTasas"
    entity_id = 1

    currency_ids = {
        "USD": 2,
    }

    def fetch_rates(self) -> list[ExchangeRate]:
        data = self._call_api()
        result = data.get("result")
        if not result:
            raise RuntimeError("Respuesta inesperada de Banco Central")

        buy = result.get("actualPurchaseValueFormatted")
        sell = result.get("actualSellingValueFormatted")
        if not buy or not sell:
            raise RuntimeError("No se encontraron tasas USD en Banco Central")

        rate_date = datetime.fromisoformat(
            result["date"].replace("Z", "+00:00")
        ).date()
        rate = self._make_rate(
            currency_from="USD",
            currency_to="DOP",
            buy_rate=buy,
            sell_rate=sell,
            rate_date=rate_date,
        )
        logger.info(f"[BANCOCENTRAL] USD: compra={buy}, venta={sell}")

        return [rate]

    def _call_api(self) -> dict:
        headers = {
            "User-Agent": "Mozilla/5.0",
        }
        with httpx.Client(timeout=30, follow_redirects=True, headers=headers) as client:
            client.get(self.source_url)
            response = client.post(
                "https://www.bancentral.gov.do/Home/GetActualExchangeRate",
                data={},
                headers={
                    "content-type": "application/x-www-form-urlencoded",
                    "Referer": self.source_url,
                    "X-Requested-With": "XMLHttpRequest",
                },
            )
            response.raise_for_status()
            return response.json()

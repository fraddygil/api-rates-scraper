import logging
from abc import ABC, abstractmethod
from datetime import date

from core.models import ExchangeRate, ScrapeResult

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Clase base para todos los scrapers de bancos."""

    bank_code: str        # Identificador único, ej: "BHD"
    bank_name: str        # Nombre completo
    country_code: str     # ISO 3166-1 alpha-2, ej: "DO"
    source_url: str       # URL principal a scrapear
    entity_id: int        # ID de la entidad en la API
    currency_ids: dict[str, int]  # Monedas a guardar, ej: {"USD": 1, "EUR": 2}

    def scrape(self) -> ScrapeResult:
        """Ejecuta el scraper y retorna el resultado."""
        logger.info(f"[{self.bank_code}] Iniciando scrape de {self.source_url}")
        try:
            rates = self.fetch_rates()
            logger.info(f"[{self.bank_code}] {len(rates)} tasas obtenidas")
            return ScrapeResult(
                bank_code=self.bank_code,
                success=True,
                rates=rates,
            )
        except Exception as e:
            logger.error(f"[{self.bank_code}] Error: {e}", exc_info=True)
            return ScrapeResult(
                bank_code=self.bank_code,
                success=False,
                error=str(e),
            )

    @abstractmethod
    def fetch_rates(self) -> list[ExchangeRate]:
        """Implementar en cada banco. Debe retornar la lista de tasas."""
        ...

    def _make_rate(
        self,
        currency_from: str,
        currency_to: str,
        buy_rate,
        sell_rate,
        rate_date: date | None = None,
    ) -> ExchangeRate:
        """Helper para construir un ExchangeRate con los datos del banco."""
        from decimal import Decimal, InvalidOperation

        def to_decimal(val):
            if val is None:
                return None
            try:
                return Decimal(str(val).replace(",", ".").strip())
            except InvalidOperation:
                return None

        return ExchangeRate(
            entity_id=self.entity_id,
            currency_id=self.currency_ids[currency_from],
            bank_code=self.bank_code,
            bank_name=self.bank_name,
            country_code=self.country_code,
            currency_from=currency_from,
            currency_to=currency_to,
            buy_rate=to_decimal(buy_rate),
            sell_rate=to_decimal(sell_rate),
            rate_date=rate_date or date.today(),
            source_url=self.source_url,
        )

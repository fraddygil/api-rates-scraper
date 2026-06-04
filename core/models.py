from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from decimal import Decimal


@dataclass
class ExchangeRate:
    entity_id: int
    currency_id: int
    bank_code: str          # ej: "BHD", "POPULAR", "RESERVAS"
    bank_name: str
    country_code: str       # ej: "DO"
    currency_from: str      # ej: "USD"
    currency_to: str        # ej: "DOP"
    buy_rate: Optional[Decimal]
    sell_rate: Optional[Decimal]
    rate_date: date
    source_url: str

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "currency_id": self.currency_id,
            "buy_rate": str(self.buy_rate) if self.buy_rate else None,
            "sell_rate": str(self.sell_rate) if self.sell_rate else None,
            "rate_date": self.rate_date.isoformat(),
        }


@dataclass
class ScrapeResult:
    bank_code: str
    success: bool
    rates: list[ExchangeRate] = field(default_factory=list)
    error: Optional[str] = None
    records_saved: int = 0

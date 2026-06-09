"""
Registro central de scrapers.
Para agregar un nuevo banco:
  1. Crea scrapers/nuevo_banco.py con clase que herede BaseScraper
  2. Registra el módulo y la clase en SCRAPER_REGISTRY
"""
from importlib import import_module

SCRAPER_REGISTRY = {
    "BHD": ("scrapers.bhd", "BHDScraper"),
    "BANRESERVAS": ("scrapers.banreservas", "BanreservasScraper"),
    "APAP": ("scrapers.apap", "APAPScraper"),
    "BANCOCENTRAL": ("scrapers.bancentral", "BancoCentralScraper"),
    "QIK": ("scrapers.qik", "QikScraper"),
    "SCOTIABANK": ("scrapers.scotiabank", "ScotiabankScraper"),
    "PROMERICA": ("scrapers.promerica", "PromericaScraper"),
    "BANESCO": ("scrapers.banesco", "BanescoScraper"),
    "BANCOCARIBE": ("scrapers.bancocaribe", "BancoCaribeScraper"),
    "BDI": ("scrapers.bdi", "BDIScraper"),
    # "POPULAR": ("scrapers.popular", "PopularScraper"),
}


def get_scrapers(bank_filter: str | None = None):
    """Carga solo los scrapers requeridos."""
    registry = SCRAPER_REGISTRY
    if bank_filter:
        bank_code = bank_filter.upper()
        registry = {bank_code: SCRAPER_REGISTRY[bank_code]} if bank_code in SCRAPER_REGISTRY else {}

    scrapers = []
    for module_name, class_name in registry.values():
        module = import_module(module_name)
        scrapers.append(getattr(module, class_name))
    return scrapers

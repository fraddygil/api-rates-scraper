"""
main.py — Punto de entrada del scraper scheduler.

Uso:
  python main.py              # corre todos los scrapers
  python main.py --bank BHD  # corre solo un banco

GitHub Actions lo ejecuta con: python main.py
"""
import argparse
import logging
import sys
from datetime import date

from core.api_client import save_rates_bulk
from core.models import ScrapeResult
from core.telegram import send_daily_summary, send_error_alert
from scrapers import get_scrapers

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_all(bank_filter: str | None = None, notify_telegram: bool = True) -> list[ScrapeResult]:
    scrapers_to_run = get_scrapers(bank_filter)
    if bank_filter and not scrapers_to_run:
        logger.error(f"Banco '{bank_filter}' no encontrado en el registro.")
        sys.exit(1)

    results: list[ScrapeResult] = []

    for ScraperClass in scrapers_to_run:
        scraper = ScraperClass()
        result = scraper.scrape()

        if result.success and result.rates:
            try:
                saved = save_rates_bulk(result.rates)
                result.records_saved = saved
                logger.info(f"[{result.bank_code}] ✅ {saved}/{len(result.rates)} registros guardados")
            except Exception as e:
                result.success = False
                result.error = f"Error guardando tasas: {e}"
                logger.error(f"[{result.bank_code}] ❌ {result.error}")
                if notify_telegram:
                    send_error_alert(result.bank_code, result.error)
        elif not result.success:
            logger.error(f"[{result.bank_code}] ❌ {result.error}")
            if notify_telegram:
                send_error_alert(result.bank_code, result.error or "Error desconocido")

        results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(description="Exchange Rate Scraper")
    parser.add_argument("--bank", help="Correr solo un banco específico (ej: BHD)")
    parser.add_argument("--no-telegram", action="store_true", help="No enviar notificaciones Telegram")
    args = parser.parse_args()

    logger.info(f"=== Iniciando scraper {date.today().isoformat()} ===")

    results = run_all(bank_filter=args.bank, notify_telegram=not args.no_telegram)

    ok_count = sum(1 for r in results if r.success)
    total_records = sum(r.records_saved for r in results)
    logger.info(f"=== Finalizado: {ok_count}/{len(results)} bancos, {total_records} registros ===")

    if not args.no_telegram:
        send_daily_summary(results)

    # Exit code != 0 si todos fallaron (útil para GitHub Actions)
    if ok_count == 0 and results:
        sys.exit(1)


if __name__ == "__main__":
    main()

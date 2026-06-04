import logging
from datetime import date
from typing import Optional

import httpx

from core.config import settings
from core.models import ScrapeResult

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _send(text: str, parse_mode: str = "HTML") -> bool:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.info("Telegram no configurado; se omite notificación")
        return False

    url = TELEGRAM_API.format(token=settings.telegram_bot_token)
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    try:
        with httpx.Client(timeout=15) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"No se pudo enviar mensaje Telegram: {e}")
        return False


def send_error_alert(bank_code: str, error: str) -> None:
    """Alerta inmediata cuando un scraper falla."""
    msg = (
        f"⚠️ <b>Error en scraper</b>\n"
        f"Banco: <code>{bank_code}</code>\n"
        f"Error: {error[:300]}"
    )
    _send(msg)


def send_daily_summary(results: list[ScrapeResult], run_date: Optional[date] = None) -> None:
    """Resumen completo al finalizar todos los scrapers."""
    run_date = run_date or date.today()
    ok = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    total_records = sum(r.records_saved for r in ok)

    lines = [
        f"📊 <b>Resumen de tasas de cambio</b>",
        f"📅 Fecha: {run_date.isoformat()}",
        f"",
        f"✅ Exitosos: {len(ok)}/{len(results)} bancos",
        f"💾 Registros guardados: {total_records}",
    ]

    if ok:
        lines.append("")
        lines.append("<b>Bancos procesados:</b>")
        for r in ok:
            lines.append(f"  • {r.bank_code} — {r.records_saved} tasa(s)")

    if failed:
        lines.append("")
        lines.append(f"❌ <b>Fallidos ({len(failed)}):</b>")
        for r in failed:
            short_err = (r.error or "desconocido")[:150]
            lines.append(f"  • {r.bank_code}: {short_err}")

    _send("\n".join(lines))

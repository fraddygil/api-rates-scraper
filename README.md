# Exchange Rate Scraper

Scraper automático de tasas de cambio bancarias para República Dominicana.
Corre via GitHub Actions, guarda en tu API FastAPI y notifica por Telegram.

## Estructura

```
exchange-scraper/
├── main.py                    # Entrypoint
├── core/
│   ├── config.py              # Variables de entorno
│   ├── models.py              # ExchangeRate, ScrapeResult
│   ├── http_client.py         # GET/POST con reintentos
│   ├── api_client.py          # Guarda tasas en tu API
│   └── telegram.py            # Notificaciones
├── scrapers/
│   ├── base.py                # BaseScraper (heredar aquí)
│   ├── __init__.py            # Registro lazy de scrapers activos
│   ├── bhd.py                 # BHD León
│   ├── banreservas.py         # Banreservas
│   └── popular.py             # Banco Popular
└── .github/workflows/
    └── scraper.yml            # GitHub Actions (cron diario)
```

## Configurar GitHub Secrets

En tu repo: **Settings → Secrets → Actions → New repository secret**

| Secret | Descripción |
|--------|-------------|
| `API_BASE_URL` | URL base de tu API, ej: `https://currency-rates.fastapicloud.dev` |
| `API_EMAIL` | Email para `POST /auth/login` |
| `API_PASSWORD` | Password para `POST /auth/login` |
| `TELEGRAM_BOT_TOKEN` | Opcional. Token del bot (obtener con @BotFather) |
| `TELEGRAM_CHAT_ID` | Opcional. ID del chat/grupo donde llegan las notificaciones |

## Crear el bot de Telegram

1. Habla con `@BotFather` en Telegram → `/newbot`
2. Copia el token
3. Para obtener el `CHAT_ID`:
   - Agrega el bot al grupo o usa chat directo
   - Llama: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - El `chat.id` está en la respuesta

## Agregar un nuevo banco

```python
# scrapers/nuevo_banco.py
from scrapers.base import BaseScraper

class NuevoBancoScraper(BaseScraper):
    bank_code = "NUEVO"
    bank_name = "Nombre Completo del Banco"
    country_code = "DO"
    source_url = "https://www.nuevobanco.com/tasas"
    entity_id = 0  # ID real de la entidad en la API
    currency_ids = {
        "USD": 0,  # ID real de USD en la API
        "EUR": 0,  # ID real de EUR en la API
    }

    def fetch_rates(self):
        html = get_html(self.source_url)
        # ... parsear con BeautifulSoup
        return [self._make_rate("USD", "DOP", buy_rate=60.50, sell_rate=61.00)]
```

Luego en `scrapers/__init__.py`:
```python
SCRAPER_REGISTRY = {
    "NUEVO": ("scrapers.nuevo_banco", "NuevoBancoScraper"),
}
```

## Uso local

```bash
cp .env.example .env
# Editar .env con tus valores

pip install -r requirements.txt

# Todos los bancos
python main.py

# Un banco específico
python main.py --bank BHD

# Sin Telegram (para debugging)
python main.py --no-telegram
```

## Endpoint esperado en tu API

```
POST /auth/login
Content-Type: application/json

{
  "email": "usuario@dominio.com",
  "password": "password"
}

POST /rates
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "entity_id": 1,
  "currency_id": 1,
  "buy_rate": "60.50",
  "sell_rate": "61.00",
  "rate_date": "2026-06-03"
}
```

Los IDs de entidad y moneda se configuran en cada scraper, por ejemplo en `scrapers/bhd.py`.

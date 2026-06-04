# CitasFáciles Bot 🤖

Chatbot con inteligencia artificial para agendar citas en Google Calendar.
Funciona en **Telegram** y **WhatsApp**.

## ¿Qué puede hacer?

- Agendar citas con profesionales en Google Calendar
- Validar fechas y horas (no acepta fechas pasadas, inexistentes ni lejanas)
- Cambiar el estilo de respuesta (profesional, amigable, con emojis, formal)
- Funcionar en Telegram y WhatsApp simultáneamente

## Stack tecnológico

- **Python** + **FastAPI** — servidor web
- **Groq (Llama 3)** — inteligencia artificial
- **Google Calendar API** — agendamiento
- **python-telegram-bot** — integración Telegram
- **Twilio** — integración WhatsApp
- **SQLite** — persistencia de conversaciones

## Instalación

```bash
pip install -r requirements.txt
cp .env.example .env
# Completar las claves en .env
uvicorn app:app --reload --port 8000
```

## Variables de entorno necesarias

| Variable | Descripción |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token de @BotFather |
| `GROQ_API_KEY` | Clave de console.groq.com |
| `GOOGLE_CALENDAR_ID` | ID del calendario (tu email) |
| `GOOGLE_CREDENTIALS_FILE` | Archivo JSON de cuenta de servicio |
| `TWILIO_ACCOUNT_SID` | Account SID de Twilio |
| `TWILIO_AUTH_TOKEN` | Auth Token de Twilio |

## Configurar webhook de Telegram

```bash
python setup_webhook.py https://tu-url-publica.ngrok-free.app
```

## Probar Google Calendar

```bash
python test_calendar.py
```

## Comandos de Telegram

| Comando | Descripción |
|---|---|
| `/start` | Iniciar el bot |
| `/help` | Ver ayuda |
| `/estilo [nombre]` | Cambiar estilo (professional / friendly / emoji / formal) |
| `/profesionales` | Ver profesionales disponibles |

## Agregar profesionales

Editá `config/professionals.py`:

```python
PROFESSIONALS = [
    {"id": "1", "name": "Dr. García", "specialty": "Medicina General", "calendar_email": ""},
]
```

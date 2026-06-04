import asyncio
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build

from config.settings import settings

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_service():
    if not os.path.exists(settings.GOOGLE_CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"No encontré '{settings.GOOGLE_CREDENTIALS_FILE}'. "
            "Seguí las instrucciones del README para configurar Google Calendar."
        )
    creds = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_CREDENTIALS_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)


def _create_event_sync(date: str, time: str, professional: dict, client_name: str) -> dict:
    service = _get_service()
    tz = ZoneInfo(settings.TIMEZONE)
    start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    end_dt = start_dt + timedelta(hours=settings.APPOINTMENT_DURATION_HOURS)

    event = {
        "summary": f"Cita: {client_name} con {professional['name']}",
        "description": (
            f"Cliente: {client_name}\n"
            f"Profesional: {professional['name']} ({professional['specialty']})\n"
            f"Agendado por: {settings.BOT_NAME} Bot"
        ),
        "start": {"dateTime": start_dt.isoformat(), "timeZone": settings.TIMEZONE},
        "end":   {"dateTime": end_dt.isoformat(),   "timeZone": settings.TIMEZONE},
    }
    if professional.get("calendar_email"):
        event["attendees"] = [{"email": professional["calendar_email"]}]

    return service.events().insert(
        calendarId=settings.GOOGLE_CALENDAR_ID,
        body=event,
        sendUpdates="all" if professional.get("calendar_email") else "none",
    ).execute()


async def create_appointment(date: str, time: str, professional: dict, client_name: str) -> dict:
    return await asyncio.to_thread(_create_event_sync, date, time, professional, client_name)


def format_appointment_summary(date: str, time: str, professional: dict, client_name: str) -> str:
    try:
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        months = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
                  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        date_str = f"{dt.day} de {months[dt.month]} de {dt.year}"
        time_str = dt.strftime("%H:%M")
    except ValueError:
        date_str, time_str = date, time
    return (
        f"📅 Fecha: {date_str}\n"
        f"🕐 Hora: {time_str} hs\n"
        f"👨‍⚕️ Profesional: {professional['name']} ({professional['specialty']})\n"
        f"👤 Cliente: {client_name}"
    )

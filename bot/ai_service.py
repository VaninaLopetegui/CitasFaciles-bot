import asyncio
import re
from datetime import datetime, timedelta

from groq import Groq

from config.professionals import get_professionals_list
from config.settings import settings, get_current_style
from config.styles import STYLES

client = Groq(api_key=settings.GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

SCHEDULING_KEYWORDS = [
    "cita", "agendar", "reservar", "turno", "appointment",
    "programar", "quiero ir", "necesito turno", "hacer una cita",
    "sacar turno", "pedir hora", "disponible", "me gustaría ir",
]

CANCEL_KEYWORDS = [
    "cancelar", "cancel", "no quiero", "déjalo", "olvídalo",
    "salir", "stop", "parar", "atrás",
]

MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def _build_system_prompt() -> str:
    style = STYLES.get(get_current_style(), STYLES["friendly"])
    base = style["system_prompt"].format(name=settings.BOT_NAME)
    return (
        f"{base}\n\n"
        f"Profesionales disponibles:\n{get_professionals_list()}\n\n"
        "Responde siempre en español."
    )


def detect_scheduling_intent(message: str) -> bool:
    return any(kw in message.lower() for kw in SCHEDULING_KEYWORDS)


def detect_cancel_intent(message: str) -> bool:
    return any(kw in message.lower() for kw in CANCEL_KEYWORDS)


def _get_ai_response_sync(message: str, history: list) -> str:
    messages = [{"role": "system", "content": _build_system_prompt()}]
    for msg in history:
        role = "assistant" if msg["role"] == "model" else msg["role"]
        messages.append({"role": role, "content": msg["parts"][0]})
    messages.append({"role": "user", "content": message})
    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content


async def get_ai_response(message: str, history: list) -> str:
    try:
        return await asyncio.to_thread(_get_ai_response_sync, message, history)
    except Exception:
        return "Lo siento, en este momento no puedo responder. Por favor intentá de nuevo."


def _parse_datetime_local(text: str) -> dict:
    text_lower = text.lower()
    today = datetime.now()
    max_date = datetime(today.year, 12, 31)

    # --- FECHA ---
    date_obj = None
    if "pasado mañana" in text_lower:
        date_obj = today + timedelta(days=2)
    elif re.search(r'(?<![a-záéíóúñ])mañana(?![a-záéíóúñ])', text_lower) and "de la mañana" not in text_lower:
        date_obj = today + timedelta(days=1)
    elif "hoy" in text_lower:
        date_obj = today
    else:
        for month_name, month_num in MONTHS.items():
            match = re.search(rf'(\d{{1,2}})\s+de\s+{month_name}(?:\s+(?:de\s+)?(\d{{4}}))?', text_lower)
            if match:
                day = int(match.group(1))
                year = int(match.group(2)) if match.group(2) else today.year
                try:
                    dt = datetime(year, month_num, day)
                    if dt.date() < today.date():
                        return {"valid": False, "reason": "past"}
                    date_obj = dt
                except ValueError:
                    return {"valid": False, "reason": "invalid_date"}
                break
        if not date_obj:
            match = re.search(r'(\d{1,2})[/\-](\d{1,2})', text_lower)
            if match:
                day, month = int(match.group(1)), int(match.group(2))
                try:
                    dt = datetime(today.year, month, day)
                    if dt.date() < today.date():
                        return {"valid": False, "reason": "past"}
                    date_obj = dt
                except ValueError:
                    return {"valid": False, "reason": "invalid_date"}

    if not date_obj:
        return {"valid": False, "date": None, "time": None}

    if date_obj > max_date:
        return {"valid": False, "reason": "too_far"}

    # --- HORA ---
    if re.search(r'medio\s*d[ií]a|mediod[ií]a', text_lower):
        hour, minutes = 12, 0
    elif "medianoche" in text_lower:
        hour, minutes = 0, 0
    else:
        time_match = re.search(r'a las (\d{1,2})(?::(\d{2}))?', text_lower)
        if not time_match:
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(?:hrs?|hs\b)', text_lower)
        if not time_match:
            time_match = re.search(r'\b(\d{1,2}):(\d{2})\b', text_lower)
        if not time_match:
            return {"valid": False, "date": None, "time": None}
        hour = int(time_match.group(1))
        minutes = int(time_match.group(2)) if time_match.group(2) else 0
        if not (0 <= hour <= 23 and 0 <= minutes <= 59):
            return {"valid": False, "date": None, "time": None}

    if date_obj.date() == today.date():
        if date_obj.replace(hour=hour, minute=minutes) <= today:
            return {"valid": False, "reason": "past_time"}

    return {
        "valid": True,
        "date": date_obj.strftime("%Y-%m-%d"),
        "time": f"{hour:02d}:{minutes:02d}",
    }


async def extract_datetime_from_text(text: str) -> dict:
    return await asyncio.to_thread(_parse_datetime_local, text)

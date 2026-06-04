from fastapi import Response
from bot.message_processor import process_message


async def handle_whatsapp_message(from_number: str, body: str) -> Response:
    if not body or not body.strip():
        return Response(content=_twiml("Solo proceso mensajes de texto 😊"), media_type="application/xml")
    user_id = f"whatsapp_{from_number}"
    response_text = await process_message(user_id, body)
    response_text = response_text.replace("*", "").replace("_", "")
    return Response(content=_twiml(response_text), media_type="application/xml")


def _twiml(message: str) -> str:
    safe = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{safe}</Message></Response>'

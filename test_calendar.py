import asyncio
from datetime import datetime, timedelta
from bot.calendar_service import create_appointment


async def test() -> None:
    print("🔄 Probando conexión con Google Calendar...")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        event = await create_appointment(
            date=tomorrow, time="10:00",
            professional={"name": "Test", "specialty": "Prueba", "calendar_email": ""},
            client_name="Cliente de Prueba",
        )
        print(f"✅ Conexión exitosa. Evento: {event.get('summary')}")
        print("Podés eliminar este evento de prueba en Google Calendar.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test())

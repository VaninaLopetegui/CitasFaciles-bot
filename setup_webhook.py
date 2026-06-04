import asyncio
import sys
from telegram import Bot
from config.settings import settings


async def set_webhook(public_url: str) -> None:
    url = public_url.rstrip("/")
    webhook_url = f"{url}/webhook/telegram"
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    result = await bot.set_webhook(webhook_url)
    if result:
        print(f"✅ Webhook configurado en:\n   {webhook_url}")
    else:
        print("❌ No se pudo configurar el webhook")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python setup_webhook.py https://tu-url.ngrok-free.app")
        sys.exit(1)
    asyncio.run(set_webhook(sys.argv[1]))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse

from bot.conversation import init_db
from bot.telegram_handler import get_telegram_app, setup_telegram
from bot.whatsapp_handler import handle_whatsapp_message
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.TELEGRAM_BOT_TOKEN:
        await setup_telegram()
        print(f"✅ Bot de Telegram '{settings.BOT_NAME}' iniciado")
    else:
        print("⚠️  TELEGRAM_BOT_TOKEN no configurado")
    yield
    ptb = get_telegram_app()
    if ptb:
        await ptb.stop()
        await ptb.shutdown()


app = FastAPI(title=f"{settings.BOT_NAME} Bot", lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "running", "bot": settings.BOT_NAME}


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    ptb = get_telegram_app()
    if not ptb:
        return JSONResponse({"error": "Telegram no configurado"}, status_code=503)
    from telegram import Update
    data = await request.json()
    update = Update.de_json(data, ptb.bot)
    await ptb.process_update(update)
    return {"ok": True}


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(Body: str = Form(default=""), From: str = Form(default="")):
    return await handle_whatsapp_message(From, Body)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from bot.message_processor import process_message
from config.professionals import get_professionals_list
from config.settings import settings, set_current_style, get_current_style
from config.styles import STYLES, list_styles

_telegram_app: Application | None = None


async def setup_telegram() -> None:
    global _telegram_app
    _telegram_app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).updater(None).build()
    _telegram_app.add_handler(CommandHandler("start", cmd_start))
    _telegram_app.add_handler(CommandHandler("help", cmd_help))
    _telegram_app.add_handler(CommandHandler("estilo", cmd_estilo))
    _telegram_app.add_handler(CommandHandler("profesionales", cmd_profesionales))
    _telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await _telegram_app.initialize()
    await _telegram_app.start()


def get_telegram_app() -> Application | None:
    return _telegram_app


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    user_id = f"telegram_{update.effective_user.id}"
    response = await process_message(user_id, update.message.text)
    await update.message.reply_text(response, parse_mode="Markdown")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = f"telegram_{update.effective_user.id}"
    await update.message.reply_text(
        f"¡Hola! Te estás comunicando con el asistente *{settings.BOT_NAME}*. "
        "Estoy aquí para ayudarte a agendar una cita. ¿Comenzamos?\n\n"
        "1. Agendemos una cita\n"
        "2. No, muchas gracias",
        parse_mode="Markdown",
    )
    from bot.conversation import conversation_store
    state = conversation_store.get(user_id)
    state.scheduling_step = "welcome"
    conversation_store.save(user_id, state)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"*Comandos:*\n"
        f"/start — Iniciar\n"
        f"/help — Esta ayuda\n"
        f"/estilo [nombre] — Cambiar estilo de respuesta\n"
        f"/profesionales — Ver profesionales\n\n"
        f"*Estilo actual:* {STYLES[get_current_style()]['description']}\n\n"
        f"*Profesionales:*\n{get_professionals_list()}",
        parse_mode="Markdown",
    )


async def cmd_estilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if settings.ADMIN_TELEGRAM_ID and str(update.effective_user.id) != settings.ADMIN_TELEGRAM_ID:
        await update.message.reply_text("Solo el administrador puede cambiar el estilo.")
        return
    args = context.args
    if not args:
        await update.message.reply_text(
            f"*Estilos disponibles:*\n{list_styles()}\n\nUso: `/estilo friendly`",
            parse_mode="Markdown",
        )
        return
    if set_current_style(args[0].lower()):
        await update.message.reply_text(f"✅ Estilo cambiado a: *{args[0]}*", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Estilo no válido. Opciones: professional, friendly, emoji, formal")


async def cmd_profesionales(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"*Profesionales disponibles:*\n\n{get_professionals_list()}",
        parse_mode="Markdown",
    )

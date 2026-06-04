from config.professionals import get_professionals_list, find_professional
from bot.ai_service import detect_scheduling_intent, detect_cancel_intent, extract_datetime_from_text
from bot.calendar_service import create_appointment, format_appointment_summary
from bot.conversation import conversation_store

AFFIRMATIVE_WORDS = ["si", "sí", "yes", "confirmo", "correcto", "ok", "dale", "bueno", "claro", "adelante"]

MENSAJE_BIENVENIDA = (
    "¡Hola! Te estás comunicando con el asistente Carlos Bot. "
    "Estoy aquí para ayudarte a agendar una cita. ¿Comenzamos?\n\n"
    "1. Agendemos una cita\n"
    "2. No, muchas gracias"
)

MENSAJE_REDIRECCION = (
    "Solo puedo ayudarte a agendar citas. 📅\n\n"
    "1. Agendemos una cita\n"
    "2. No, muchas gracias"
)

MENSAJE_DESPEDIDA = "¡Hasta luego! Si en algún momento querés agendar una cita, estaré aquí. 😊"


async def process_message(user_id: str, message: str) -> str:
    state = conversation_store.get(user_id)
    message = message.strip()

    try:
        return await _handle(user_id, message, state)
    finally:
        conversation_store.save(user_id, state)


async def _handle(user_id: str, message: str, state) -> str:

    if state.scheduling_step and state.scheduling_step not in ("confirm", "cancel_reason") and detect_cancel_intent(message):
        conversation_store.reset_scheduling(user_id)
        return "Entendido, cancelé el agendamiento. Cuando quieras reservar un turno escribí: *quiero agendar una cita*"

    if state.scheduling_step == "datetime":
        return await _handle_datetime(user_id, message, state)

    if state.scheduling_step == "professional":
        return await _handle_professional(user_id, message, state)

    if state.scheduling_step == "name":
        return await _handle_name(user_id, message, state)

    if state.scheduling_step == "confirm":
        return await _handle_confirmation(user_id, message, state)

    if state.scheduling_step == "cancel_reason":
        return await _handle_cancel_reason(user_id, message, state)

    if state.scheduling_step == "welcome":
        if message.strip() == "1" or detect_scheduling_intent(message):
            state.scheduling_step = "datetime"
            return (
                "¡Perfecto! ¿Para qué día y hora necesitas la cita?\n"
                "Ejemplo: *mañana a las 15:00* o *5 de junio a las 10:30*"
            )
        elif message.strip() == "2" or detect_cancel_intent(message):
            state.scheduling_step = None
            return MENSAJE_DESPEDIDA
        else:
            return (
                "No tenemos una opción que diga eso, por favor digitá una de las opciones:\n\n"
                "1. Agendemos una cita\n"
                "2. No, muchas gracias"
            )

    if detect_scheduling_intent(message):
        state.scheduling_step = "datetime"
        return (
            "¡Con gusto te ayudo a agendar una cita! 📅\n\n"
            "¿Para qué día y hora necesitas la cita?\n"
            "Ejemplo: *mañana a las 15:00* o *5 de junio a las 10:30*"
        )

    thanks = ["gracias", "muchas gracias", "thank you", "thanks", "mil gracias"]
    if any(t in message.lower() for t in thanks):
        state.scheduling_step = "welcome"
        return (
            "¡Gracias a usted por contactarnos! Fue un placer ayudarle. 😊\n\n"
            "Si necesita agendar otra cita, estamos aquí.\n\n"
            "1. Agendar otra cita\n"
            "2. No, hasta luego"
        )

    greetings = ["hola", "buenos días", "buenas tardes", "buenas noches", "buenas", "hey", "hi", "buen día"]
    if any(g in message.lower() for g in greetings):
        state.scheduling_step = "welcome"
        return MENSAJE_BIENVENIDA

    state.scheduling_step = "welcome"
    return MENSAJE_REDIRECCION


async def _handle_datetime(user_id: str, message: str, state) -> str:
    result = await extract_datetime_from_text(message)

    if not result.get("valid") or not result.get("date") or not result.get("time"):
        reason = result.get("reason", "")
        if reason == "invalid_date":
            return "Esa fecha no existe en el calendario. Por favor verificá el día y mes.\n\nEjemplo: *5 de julio a las 10:30*"
        if reason == "past_time":
            return "Esa hora ya pasó. Por favor indicá una hora que aún no haya pasado.\n\nEjemplo: *hoy a las 17:00* o *mañana a las 10:30*"
        if reason == "past":
            return "Esa fecha ya pasó. Por favor indicá una fecha de hoy en adelante.\n\nEjemplo: *hoy a las 15:00* o *5 de julio a las 10:30*"
        if reason == "too_far":
            return "Solo podemos agendar citas hasta diciembre de este año.\n\nEjemplo: *mañana a las 15:00* o *20 de noviembre a las 09:00*"
        return "Necesito que me indiques la fecha y la hora juntas.\n\nEjemplo: *mañana a las 15:00* o *5 de junio a las 10:30*"

    state.appointment_date = result["date"]
    state.appointment_time = result["time"]
    state.scheduling_step = "professional"
    return (
        f"Perfecto ✅\n\n"
        f"¿Con qué profesional quieres la cita?\n\n{get_professionals_list()}\n\n"
        "Podés escribir el nombre o el número de la lista."
    )


async def _handle_professional(user_id: str, message: str, state) -> str:
    prof = find_professional(message)
    if not prof:
        return f"No encontré ese profesional. Por favor elegí uno de la lista:\n\n{get_professionals_list()}"
    state.professional = prof
    state.scheduling_step = "name"
    return f"Excelente, con {prof['name']} ({prof['specialty']}).\n\n¿Cuál es tu nombre completo para registrar la cita?"


async def _handle_name(user_id: str, message: str, state) -> str:
    state.client_name = message.strip()
    state.scheduling_step = "confirm"
    summary = format_appointment_summary(state.appointment_date, state.appointment_time, state.professional, state.client_name)
    return f"Estos son los datos de tu cita:\n\n{summary}\n\n¿Confirmás? Respondé *sí* para agendar o *no* para cancelar."


async def _handle_confirmation(user_id: str, message: str, state) -> str:
    if any(word in message.lower() for word in AFFIRMATIVE_WORDS):
        try:
            await create_appointment(state.appointment_date, state.appointment_time, state.professional, state.client_name)
            summary = format_appointment_summary(state.appointment_date, state.appointment_time, state.professional, state.client_name)
            conversation_store.reset_scheduling(user_id)
            return f"¡Cita agendada con éxito! ✅\n\n{summary}\n\nYa quedó registrada en el calendario."
        except FileNotFoundError as e:
            conversation_store.reset_scheduling(user_id)
            return f"⚠️ Error de configuración: {e}"
        except Exception as e:
            conversation_store.reset_scheduling(user_id)
            return f"❌ Hubo un problema al agendar la cita. Por favor intentá de nuevo.\n\nDetalle: {str(e)}"
    else:
        state.scheduling_step = "cancel_reason"
        return (
            "¡Lamentamos lo sucedido! Dinos el motivo para no confirmar:\n\n"
            "1. Quiero cambiar la fecha de la cita\n"
            "2. Quiero cambiar la hora de la cita\n"
            "3. Quiero cambiar el profesional para la cita\n"
            "4. Cambiemos el nombre para la cita\n"
            "5. Simplemente quiero cancelar\n"
            "6. Motivos personales"
        )


async def _handle_cancel_reason(user_id: str, message: str, state) -> str:
    option = message.strip()
    if option in ("1", "2"):
        state.scheduling_step = "datetime"
        state.appointment_date = None
        state.appointment_time = None
        return "¿Para qué nueva fecha y hora necesitas la cita?\nEjemplo: *mañana a las 15:00*"
    elif option == "3":
        state.scheduling_step = "professional"
        state.professional = None
        return f"¿Con qué profesional quieres la cita?\n\n{get_professionals_list()}"
    elif option == "4":
        state.scheduling_step = "name"
        state.client_name = None
        return "¿Cuál es el nombre correcto para registrar en la cita?"
    elif option in ("5", "6"):
        conversation_store.reset_scheduling(user_id)
        return "Entendido, cancelé la cita. Cuando quieras reservar escribí: *quiero agendar una cita*"
    else:
        return (
            "No tenemos una opción que diga eso, por favor digitá una de las opciones:\n\n"
            "1. Quiero cambiar la fecha de la cita\n"
            "2. Quiero cambiar la hora de la cita\n"
            "3. Quiero cambiar el profesional para la cita\n"
            "4. Cambiemos el nombre para la cita\n"
            "5. Simplemente quiero cancelar\n"
            "6. Motivos personales"
        )

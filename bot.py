print("🚀 BOT INICIADO DESDE Railway")
import os
import json
import requests
import telegram
from telegram import Update
from telegram.ext import ContextTypes
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.error import TelegramError
from utils.helpers import load_json, save_json
from config import USUARIOS_AUTORIZADOS 
from handlers.commands import ver_blacklist
from handlers.commands import descastigar 
from handlers.commands import ver_canales

# Configuración de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token desde variable de entorno
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Handlers de comandos
from handlers.commands import (
    start,
    estado_bot,
    agregar_canal,
    eliminar_canal,
    publicar_botonera,
    eliminar_botonera,
    autorizar,
    revocar,
    listar_autorizados,
    ver_canales,
)

# Callback handler
from handlers.callbacks import callback_handler

# Crear app
app = ApplicationBuilder().token(BOT_TOKEN).build()

async def callback_guardar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user # type: ignore

    if user is None or not autorizado(user.id):
        return await query.answer("❌ No estás autorizado.", show_alert=True) # type: ignore

    # ✅ Carga los canales y filtra los que NO están marcados para eliminar
    canales = load_json("data/channels.json")
    canales_filtrados = [c for c in canales if not c.get("eliminar")]

    # 💾 Guarda el nuevo archivo sin los canales marcados
    save_json("data/channels.json", canales_filtrados)

    await query.answer("✅ Cambios guardados.") # type: ignore
    await query.edit_message_text("✅ Cambios guardados correctamente.") # type: ignore

def autorizado(user_id: int) -> bool:
    return user_id in USUARIOS_AUTORIZADOS

async def eliminar_canal_boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    print(f"✏️ Callback recibido: {query.data}") # type: ignore

    if not query or not query.from_user:
        return

    user = query.from_user
    if not autorizado(user.id):
        return await query.answer("❌ No estás autorizado.", show_alert=True)

    data = query.data
    if not data or not data.startswith("eliminar_canal_"):
        return await query.answer("⚠️ Acción inválida.", show_alert=True)

    try:
        canal_id = int(data.replace("eliminar_canal_", ""))
    except ValueError:
        return await query.answer("⚠️ ID inválido.", show_alert=True)

    canales = load_json("data/channels.json")
    encontrado = False

    for canal in canales:
        if str(canal["id"]) == str(canal_id):
            canal["eliminar"] = True
            encontrado = True
            break

    if not encontrado:
        return await query.answer("⚠️ Canal no encontrado.", show_alert=True)

    save_json("data/channels.json", canales)

    await query.answer("✅ Canal marcado para eliminar.", show_alert=False)
    await query.edit_message_caption(
    caption="📝 Cambios pendientes. Pulsa 'Guardar cambios' para aplicar."
)

# Registro de handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("estado", estado_bot))
app.add_handler(CommandHandler("agregar", agregar_canal))
app.add_handler(CommandHandler("eliminar", eliminar_canal))
app.add_handler(CommandHandler("publicar", publicar_botonera))
app.add_handler(CommandHandler("borrar", eliminar_botonera))
app.add_handler(CommandHandler("autorizar", autorizar))
app.add_handler(CommandHandler("revocar", revocar))
app.add_handler(CommandHandler("listar", listar_autorizados))
app.add_handler(CommandHandler("vercanales", ver_canales))
app.add_handler(CommandHandler("blacklist", ver_blacklist))
app.add_handler(CommandHandler("descastigar", descastigar))
app.add_handler(CallbackQueryHandler(eliminar_canal_boton, pattern="^eliminar_canal_"))
app.add_handler(CallbackQueryHandler(callback_guardar, pattern="^guardar$"))
app.add_handler(CallbackQueryHandler(callback_handler))
app.add_handler(CommandHandler("ver_canales", ver_canales))

# Manejo de errores
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling update:", exc_info=context.error)

app.add_error_handler(error_handler)

# Entry point final
if __name__ == "__main__":
    print("✅ Bot ejecutándose correctamente...")
    app.run_polling(stop_signals=None)
print("🚀 BOT INICIADO DESDE Railway")
import os
import json
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
    listar_autorizados
)

# Callback handler
from handlers.callbacks import callback_handler

# Crear app
app = ApplicationBuilder().token(BOT_TOKEN).build()

async def callback_guardar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.from_user:
        return
    user = query.from_user

    if not autorizado(user.id):
        return await query.answer("❌ No estás autorizad@", show_alert=True)

    # Carga y filtra los canales que NO están marcados con "eliminar": true
    canales = load_json("data/channels.json")
    canales_filtrados = [c for c in canales if not c.get("eliminar")]

    save_json("data/channels.json", canales_filtrados)
    await query.answer("✅ Cambios guardados.")
    await query.edit_message_text("✅ Cambios guardados correctamente.")

def autorizado(user_id: int) -> bool:
    return user_id in USUARIOS_AUTORIZADOS

async def ver_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message or update.effective_message

    if user is None or not autorizado(user.id):
        return

    canales = load_json("data/channels.json")
    texto = json.dumps(canales, indent=2, ensure_ascii=False)
    if message:
        await message.reply_text(f"📁 Contenido de channels.json:\n\n{texto}")

async def eliminar_canal_boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    print(f"✏️ Callback recibido: {query.data}")

    if not query or not query.from_user:
        return

    user = query.from_user
    print(f"👤 Usuario que pulsó el botón: {user.id}")

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
    encontrados = 0

    for canal in canales:
        if canal["id"] == canal_id:
            canal["eliminar"] = True
            encontrados += 1
            break

    save_json("data/channels.json", canales)

    if encontrados:
        await query.answer("✅ Canal marcado para eliminar.")
        await query.edit_message_text("✅ Canal marcado. Pulsa 📝 Guardar cambios para aplicar.")
    else:
        await query.answer("⚠️ Canal no encontrado.", show_alert=True)

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
app.add_handler(CommandHandler("verchannels", ver_channels))
app.add_handler(CommandHandler("blacklist", ver_blacklist))
app.add_handler(CommandHandler("descastigar", descastigar))
app.add_handler(CallbackQueryHandler(eliminar_canal_boton, pattern="^eliminar_canal_"))
app.add_handler(CallbackQueryHandler(callback_guardar, pattern="^guardar$"))
app.add_handler(CallbackQueryHandler(callback_handler))

# Manejo de errores
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling update:", exc_info=context.error)

app.add_error_handler(error_handler)

# Entry point final
if __name__ == "__main__":
    print("✅ Bot ejecutándose correctamente...")
    app.run_polling(stop_signals=None)
import os
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
app.add_handler(CallbackQueryHandler(callback_handler))

# Manejo de errores
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling update:", exc_info=context.error)

app.add_error_handler(error_handler)

# Entry point final
if __name__ == "__main__":
    print("✅ Bot ejecutándose correctamente...")
    app.run_polling(stop_signals=None)
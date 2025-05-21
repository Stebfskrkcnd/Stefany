from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler
)

import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

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
    editar_encabezado,
    ver_encabezado
)

from handlers.callbacks import callback_handler

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("estado", estado_bot))
app.add_handler(CommandHandler("agregar", agregar_canal))
app.add_handler(CommandHandler("eliminar", eliminar_canal))
app.add_handler(CommandHandler("publicar", publicar_botonera))
app.add_handler(CommandHandler("borrar", eliminar_botonera))
app.add_handler(CommandHandler("autorizar", autorizar))
app.add_handler(CommandHandler("revocar", revocar))
app.add_handler(CommandHandler("listar", listar_autorizados))
app.add_handler(CommandHandler("encabezado", ver_encabezado))
app.add_handler(CommandHandler("editar_encabezado", editar_encabezado))
app.add_handler(CallbackQueryHandler(callback_handler))

print("✅ Bot ejecutándose correctamente...")
app.run_polling(stop_signals=None)
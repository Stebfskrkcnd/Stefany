import asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler
)
from config import BOT_TOKEN
from handlers.commands import (
    start, estado_bot, agregar_canal, eliminar_canal,
    publicar_botonera, eliminar_botonera, autorizar,
    revocar, listar_autorizados, editar_encabezado, ver_encabezado
)
from handlers.callbacks import callback_handler


app = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers de comandos
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

# Handler para botones interactivos
app.add_handler(CallbackQueryHandler(callback_handler))

async def main():
    print("✅ Bot ejecutándose correctamente...")
    await app.run_polling()

if name == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.get_event_loop().run_until_complete(main())
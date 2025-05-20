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

async def main():
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
    await app.run_polling()


import asyncio
import sys

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
import os

from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
USUARIOS_AUTORIZADOS = [int(uid) for uid in os.getenv("USUARIOS_AUTORIZADOS", "").split(",") if uid]

async def notificar_admins(mensaje):
    bot = Bot(token=BOT_TOKEN)
    for uid in USUARIOS_AUTORIZADOS:
        try:
            await bot.send_message(chat_id=uid, text=mensaje)
        except:
            pass
        except Exception as e:
    logging.warning(f"Fallo notificando a {uid}: {e}")